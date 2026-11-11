"""Lógica de scripts/backtest.py (separada para poder testearla)."""

from __future__ import annotations

import csv
import hashlib
import json
import tomllib
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from tlab import metrics
from tlab.backtest.allocation_sim import simulate_weights
from tlab.backtest.costs import cost_models
from tlab.backtest.portfolio_sim import SimConfig, simulate
from tlab.backtest.robustness import drop_top_trades, monte_carlo_dd, param_grid, subperiods
from tlab.backtest.walkforward import make_windows
from tlab.config import ROOT, asset_class_of, load_settings, load_strategy_config
from tlab.data.loader import load_bars
from tlab.report import MADRID, append_registry, write_report
from tlab.strategies import SIGNAL_STRATEGIES

MODES = ("is", "wf", "oos", "full", "robust")


class OOSGuardError(RuntimeError):
    """Uso indebido del out-of-sample."""


def params_hash(params: dict) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]


def check_oos_guard(
    log_path: Path, strategy: str, params: dict, confirm: bool, force: bool
) -> None:
    """Exige --confirm-oos; si ya hubo OOS con otros parámetros, exige --force. Registra."""
    if not confirm:
        raise OOSGuardError("--mode oos exige --confirm-oos (el OOS se mira UNA vez)")
    h = params_hash(params)
    prev = []
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            prev = [r for r in csv.DictReader(f) if r["strategy"] == strategy]
    if any(r["params_hash"] != h for r in prev) and not force:
        raise OOSGuardError(
            "Ya hay un OOS con otros parámetros para esta estrategia; "
            "usa --force solo si de verdad procede (queda anotado)"
        )
    new = not log_path.exists()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date_madrid", "strategy", "params_hash", "forced"])
        w.writerow(
            [datetime.now(MADRID).isoformat(timespec="minutes"), strategy, h, bool(force and prev)]
        )


def periods_per_year(symbols: list[str]) -> int:
    return 365 if any(asset_class_of(s) == "crypto" for s in symbols) else 252


def _slice(df: pd.DataFrame, a, b) -> pd.DataFrame:
    return df[(df.index >= a) & (df.index <= b)]


def run_signals(bars: dict, params: dict, fn, cfg: SimConfig, a, b):
    """Señales con TODA la historia (son causales) y simulación solo en [a, b]."""
    sigs = {s: fn(df, params) for s, df in bars.items()}
    bb = {s: _slice(df, a, b) for s, df in bars.items()}
    bb = {s: df for s, df in bb.items() if len(df)}
    ss = {s: _slice(sigs[s], a, b) for s in bb}
    return simulate(bb, ss, cfg)


def benchmark_equity(bars: dict, symbol: str, costs: dict, a, b, init: float) -> pd.Series:
    df = _slice(bars[symbol], a, b)
    w = pd.DataFrame({symbol: [1.0]}, index=[df.index[0]])
    # Compra a la apertura de la segunda vela (igual que una señal en la primera).
    eq, _ = simulate_weights({symbol: df}, w, costs, init)
    return eq


def run_backtest(
    strategy: str,
    mode: str,
    costs_mode: str = "base",
    params_file: str | None = None,
    confirm_oos: bool = False,
    force: bool = False,
    data: dict | None = None,
    reports_dir: Path | None = None,
    registry: Path | None = None,
    settings: dict | None = None,
    strat_cfg: dict | None = None,
) -> Path:
    """Ejecuta un backtest y devuelve la ruta del resumen.md."""
    if mode not in MODES:
        raise ValueError(f"modo desconocido: {mode}")
    s = settings or load_settings()
    sc = strat_cfg or load_strategy_config(strategy)
    params = dict(sc["params"])
    if params_file:
        with open(params_file, "rb") as f:
            params.update(tomllib.load(f).get("params", {}))
    reports_dir = reports_dir or ROOT / "reports"
    registry = registry or ROOT / "docs" / "registro_pruebas.md"
    if mode == "oos":
        check_oos_guard(reports_dir / "oos_log.csv", strategy, params, confirm_oos, force)
    universe = list(sc["universe"])
    bench = sc.get("benchmark", universe[0])
    syms = sorted(set(universe + [bench]))
    if data is None:
        from tlab.data.loader import pick_source

        src = pick_source(s["data"]["source"])
        data_src = f"{src.name} (ajuste: {src.adjustment})"
        data = load_bars(
            syms,
            "1Day",
            start=s["data"]["history_start"],
            source=src,
            cache_dir=ROOT / s["data"]["cache_dir"],
        )
    else:
        data_src = "datos pasados por el llamador (tests)"
    bars = {k: data[k] for k in universe}
    costs = cost_models(s, costs_mode)
    r = s["risk"]
    cfg = SimConfig(
        initial_equity=s["capital"]["virtual_equity_usd"],
        risk_per_trade=r["risk_per_trade"],
        max_positions=r["max_positions"],
        max_gross_exposure=r["max_gross_exposure"],
        kill_switch_drawdown=r["kill_switch_drawdown"],
        costs=costs,
    )
    fn = SIGNAL_STRATEGIES[strategy]
    # Periodo común: desde que todos los activos de la estrategia tienen 1 año de datos.
    first = max(df.index[0] for df in bars.values()) + pd.Timedelta(days=365)
    last = min(df.index[-1] for df in bars.values())
    split = (
        pd.Timestamp(sc["is_end"], tz="UTC")
        if "is_end" in sc
        else first + (last - first) * s["validation"]["is_fraction"]
    )
    a, b = {
        "is": (first, split),
        "oos": (split + pd.Timedelta(days=1), last),
        "full": (first, last),
        "wf": (first, last),
        "robust": (first, split),
    }[mode]
    ppy = periods_per_year(universe)
    res = run_signals(bars, params, fn, cfg, a, b)
    st = metrics.summary(res.equity, res.trades, ppy, res.exposure)
    beq = benchmark_equity(data, bench, costs, a, b, cfg.initial_equity)
    bm = metrics.summary(beq, None, 252 if asset_class_of(bench) == "equity" else 365)
    extra = []
    if res.kill_switch_date is not None:
        extra.append(
            f"**KILL SWITCH** activado el {res.kill_switch_date.date()} (sin entradas posteriores)."
        )
    if mode == "wf":
        rows = [
            "## Walk-forward (parámetros por defecto, sin re-optimizar)",
            "| ventana prueba | retorno | trades |",
            "|---|---|---|",
        ]
        wins = make_windows(a, b, s["validation"]["wf_windows"])
        pos = 0
        for w in wins:
            rw = run_signals(bars, params, fn, cfg, w.test_start, w.test_end)
            tr = metrics.total_return(rw.equity)
            pos += tr > 0
            rows.append(
                f"| {w.test_start.date()} → {w.test_end.date()} | {tr * 100:.2f} % | "
                f"{len(rw.trades)} |"
            )
        rows.append(f"\nVentanas positivas: {pos}/{len(wins)}")
        extra.append("\n".join(rows))
    if mode == "robust":
        extra.append(
            robust_section(bars, params, sc.get("robust_keys", []), fn, cfg, a, b, s, ppy, res)
        )
    data_info = "\n".join(
        f"- {k}: {df.index[0].date()} → {df.index[-1].date()} ({len(df)} velas)"
        for k, df in data.items()
        if k in syms
    )
    data_info += (
        f"\n- Fuente: {data_src}\n- Periodo simulado: {a.date()} → {b.date()} (modo {mode})"
    )
    costs_info = (
        "\n".join(
            f"- {k}: slippage {v.slippage_bps} pb/lado, comisión "
            f"{v.fee_rate * 100:.3f} %/lado + {v.commission_per_share} $/acc."
            for k, v in costs.items()
        )
        + f"\n- Escenario: {costs_mode}"
    )
    stamp = datetime.now(MADRID).strftime("%Y%m%d-%H%M")
    out = reports_dir / strategy / f"{mode}_{stamp}"
    key = (
        f"CAGR {st['cagr'] * 100:.2f} %, Sharpe {st['sharpe']:.2f}, "
        f"DD {st['max_dd'] * 100:.1f} %, n={st['trades']}"
    )
    n = append_registry(
        registry,
        strategy,
        params,
        f"{mode}/{costs_mode}",
        key,
        str(out.relative_to(reports_dir.parent)) + "/resumen.md",
    )
    return write_report(
        out,
        f"{strategy} — modo {mode} ({sc.get('status', '?')})",
        st,
        bm,
        data_info,
        costs_info,
        params,
        n,
        res.equity,
        res.trades,
        "\n\n".join(extra),
    )


def robust_section(bars, params, keys, fn, cfg: SimConfig, a, b, s, ppy, base) -> str:
    from dataclasses import replace

    lines = [
        "## Robustez (in-sample)",
        "| prueba | Sharpe | expectancy R | trades |",
        "|---|---|---|---|",
    ]

    def row(label, res):
        st = metrics.summary(res.equity, res.trades, ppy)
        lines.append(
            f"| {label} | {st['sharpe']:.2f} | {st['expectancy_r']:.3f} | {st['trades']} |"
        )

    row("central", base)
    for p in param_grid(params, keys):
        if p != params:
            row(", ".join(f"{k}={p[k]}" for k in keys), run_signals(bars, p, fn, cfg, a, b))
    row(
        "costes × 2",
        run_signals(bars, params, fn, replace(cfg, costs=cost_models(s, "stress")), a, b),
    )
    row("retraso 1 vela", run_signals(bars, params, fn, replace(cfg, entry_delay=1), a, b))
    lines.append(
        f"\nP&L total sin las 5 mejores operaciones: {drop_top_trades(base.trades, 5):.2f} $"
    )
    if len(base.trades):
        mc = monte_carlo_dd(base.trades, cfg.initial_equity)
        lines.append(
            f"Monte Carlo (1000, semilla 42): DD p50 {np.percentile(mc, 50) * 100:.1f}"
            f" %, p95 {np.percentile(mc, 95) * 100:.1f} %"
        )
    for x, y in subperiods(a, b, 3):
        row(f"subperiodo {x.date()}→{y.date()}", run_signals(bars, params, fn, cfg, x, y))
    return "\n".join(lines)
