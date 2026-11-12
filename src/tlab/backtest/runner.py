"""Lógica de scripts/backtest.py (separada para poder testearla)."""

from __future__ import annotations

import tomllib
from dataclasses import replace
from datetime import datetime
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

from tlab import metrics
from tlab.backtest.allocation_sim import simulate_weights
from tlab.backtest.costs import cost_models
from tlab.backtest.guards import (
    GitProbe,
    OOSGuardError,
    append_log_row,
    params_hash,
    read_log,
    require_not_blocked,
)
from tlab.backtest.portfolio_sim import SimConfig, simulate
from tlab.backtest.robustness import (
    calibrate_risk,
    drop_best_asset,
    drop_top_trades,
    expectancy_by_asset,
    expectancy_by_period,
    kill_switch_episodes,
    monte_carlo_dd,
    param_grid,
    subperiods,
)
from tlab.backtest.tranches import IS_MODES, is_round2
from tlab.backtest.walkforward import fixed_windows, make_windows, pick_best
from tlab.config import ROOT, asset_class_of, load_settings, load_strategy_config
from tlab.data.loader import load_bars
from tlab.report import MADRID, append_registry, write_report
from tlab.strategies import resolve_signal_fn

MODES = ("is", "wf", "oos", "full", "robust", "replica", "holdout_old", "holdout_new")

# OOSGuardError y params_hash viven en guards.py (los comparte tranches.py); se reexportan aquí
# porque el resto del repo y los tests los importan desde runner.
__all__ = ["OOSGuardError", "params_hash"]


def check_oos_guard(
    log_path: Path,
    strategy: str,
    params: dict,
    confirm: bool,
    force: bool,
    *,
    tranche: str = "oos",
    costs: str = "base",
    entry_delay: int = 0,
    kind: str = "candidata",
    report: str = "",
    commit: str = "",
) -> None:
    """Exige --confirm-oos; si ya hubo OOS con otros parámetros, exige --force. Registra
    (migrando la cabecera antigua de 4 columnas si hace falta)."""
    if not confirm:
        raise OOSGuardError("--mode oos exige --confirm-oos (el OOS se mira UNA vez)")
    h = params_hash(params)
    prev = [r for r in read_log(log_path) if r["strategy"] == strategy]
    if any(r["params_hash"] != h for r in prev) and not force:
        raise OOSGuardError(
            "Ya hay un OOS con otros parámetros para esta estrategia; "
            "usa --force solo si de verdad procede (queda anotado)"
        )
    append_log_row(
        log_path,
        {
            "date_madrid": datetime.now(MADRID).isoformat(timespec="minutes"),
            "strategy": strategy,
            "params_hash": h,
            "forced": str(bool(force and prev)),
            "tranche": tranche,
            "costs": costs,
            "entry_delay": str(int(entry_delay)),
            "kind": kind,
            "report": report,
            "commit": commit,
        },
    )


def periods_per_year(symbols: list[str]) -> int:
    return 365 if any(asset_class_of(s) == "crypto" for s in symbols) else 252


def _slice(df: pd.DataFrame, a, b) -> pd.DataFrame:
    return df[(df.index >= a) & (df.index <= b)]


def run_signals(bars: dict, params: dict, fn, cfg: SimConfig, a, b, entry_from=None):
    """Señales con TODA la historia (son causales) y simulación solo en [a, b].
    `entry_from[s]`: primera fecha en la que el activo `s` forma parte del universo."""
    entry_from = entry_from or {}
    sigs = fn(bars, params)  # `fn` es una función de panel (strategies.resolve_signal_fn)
    bb = {}
    for s, df in bars.items():
        lo = max(a, entry_from[s]) if s in entry_from else a
        x = _slice(df, lo, b)
        if len(x):
            bb[s] = x
    if not bb:
        raise ValueError(f"Ningún activo tiene datos en {a} → {b}")
    ss = {s: _slice(sigs[s], bb[s].index[0], b) for s in bb}
    return simulate(bb, ss, cfg)


def benchmark_equity(bars: dict, symbol: str, costs: dict, a, b, init: float) -> pd.Series:
    df = _slice(bars[symbol], a, b)
    w = pd.DataFrame({symbol: [1.0]}, index=[df.index[0]])
    # Compra a la apertura de la segunda vela (igual que una señal en la primera).
    eq, _ = simulate_weights({symbol: df}, w, costs, init)
    return eq


def mix_benchmark_equity(
    bars: dict, weights: dict[str, float], costs: dict, a, b, init: float
) -> pd.Series:
    """Benchmark informativo con rebalanceo mensual y costes (p. ej. 60/40 SPY/IEF o
    50 % BTC / 50 % caja). Pesos que no suman 1 → el resto en caja (rinde 0)."""
    from tlab.strategies.allocation import monthly_closes

    syms = sorted(weights)
    sub = {s: _slice(bars[s], a, b) for s in syms}
    closes = pd.DataFrame({s: sub[s]["close"] for s in syms}).dropna()
    sub = {s: df.loc[df.index.isin(closes.index)] for s, df in sub.items()}
    m = monthly_closes(closes)
    # Primera decisión en la primera vela (compra en la segunda), luego cada fin de mes.
    idx = m.index.union(closes.index[:1])
    w = pd.DataFrame({s: float(weights[s]) for s in syms}, index=idx)
    eq, _ = simulate_weights(sub, w, costs, init, always_rebalance=True)
    return eq


def asset_entry_dates(bars: dict, min_bars: int) -> dict:
    """Fecha de la vela nº `min_bars` de cada activo (desde ahí puede entrar al universo)."""
    out = {}
    for s, df in bars.items():
        out[s] = (
            df.index[min_bars - 1] if len(df) >= min_bars else df.index[-1] + pd.Timedelta(days=1)
        )
    return out


def is_candidate(sc: dict) -> bool:
    """Candidata pre-registrada: sus fechas posteriores a `is_end` están protegidas."""
    return sc.get("status") == "preregistrada" or "is_end" in sc


def make_cfg(s: dict, sc: dict, costs: dict, risk: float | None = None) -> SimConfig:
    """SimConfig con los límites de settings.toml y lo específico de la estrategia (TOML)."""
    r = s["risk"]
    ks = r["kill_switch_drawdown"] if sc.get("kill_switch_in_backtest", True) else None
    return SimConfig(
        initial_equity=s["capital"]["virtual_equity_usd"],
        risk_per_trade=risk if risk is not None else sc.get("risk_per_trade", r["risk_per_trade"]),
        max_positions=r["max_positions"],
        max_gross_exposure=r["max_gross_exposure"],
        kill_switch_drawdown=ks,
        costs=costs,
        max_position_fraction=r.get("max_position_fraction"),
    )


def _key(st: dict) -> str:
    return (
        f"CAGR {st['cagr'] * 100:.2f} %, Sharpe {st['sharpe']:.2f}, "
        f"DD {st['max_dd'] * 100:.1f} %, n={st['trades']}, "
        f"expectancy {st.get('expectancy_r', float('nan')):.3f} R"
    )


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
    entry_delay: int = 0,
    confirm_tranche: bool = False,
    git_probe: GitProbe | None = None,
) -> Path:
    """Ejecuta un backtest y devuelve la ruta del resumen.md (en `replica`, la de criterio15.md).
    `entry_delay`: velas extra de retraso en la entrada (estrés del criterio 8).
    `confirm_tranche` y `git_probe` solo se usan en la ronda 2 (`git_probe` se inyecta en tests)."""
    if mode not in MODES:
        raise ValueError(f"modo desconocido: {mode}")
    s = settings or load_settings()
    sc = strat_cfg or load_strategy_config(strategy)
    cand = is_candidate(sc)
    params = dict(sc["params"])
    if params_file:
        with open(params_file, "rb") as f:
            params.update(tomllib.load(f).get("params", {}))
    reports_dir = reports_dir or ROOT / "reports"
    registry = registry or ROOT / "docs" / "registro_pruebas.md"
    # E21: las estrategias rechazadas o aparcadas solo ejecutan modos de IS (también la ronda 1).
    require_not_blocked(sc, mode in IS_MODES)
    if is_round2(sc):
        from tlab.backtest.round2 import run_round2

        return run_round2(
            strategy,
            mode,
            sc,
            s,
            params,
            costs_mode=costs_mode,
            entry_delay=entry_delay,
            confirm_tranche=confirm_tranche,
            data=data,
            reports_dir=reports_dir,
            registry=registry,
            git_probe=git_probe,
        )
    if mode in ("replica", "holdout_old", "holdout_new"):
        raise ValueError(f"el modo {mode} solo existe para estrategias de la ronda 2")
    # OOS: se mira UNA vez. En las candidatas, "full" también incluye el OOS → mismo candado.
    if mode == "oos" or (cand and mode == "full"):
        check_oos_guard(reports_dir / "oos_log.csv", strategy, params, confirm_oos, force)
    universe = list(sc["universe"])
    bench = sc.get("benchmark", universe[0])
    bench_info = dict(sc.get("benchmark_info", {}))
    syms = sorted(set(universe + [bench] + list(bench_info)))
    if data is None:
        from tlab.data.loader import pick_source

        src = pick_source(sc.get("data_source", s["data"]["source"]))
        data_src = f"{src.name} (ajuste: {src.adjustment})"
        data = load_bars(
            syms,
            "1Day",
            start=sc.get("history_start", s["data"]["history_start"]),
            source=src,
            cache_dir=ROOT / s["data"]["cache_dir"],
        )
    else:
        data_src = "datos pasados por el llamador (tests)"
    if "end" in sc:  # nada posterior al fin de datos pre-registrado
        end_ts = pd.Timestamp(sc["end"], tz="UTC")
        data = {k: v[v.index <= end_ts] for k, v in data.items()}
    bars = {k: data[k] for k in universe}
    costs = cost_models(s, costs_mode)
    cfg = make_cfg(s, sc, costs)
    if entry_delay:
        cfg = replace(cfg, entry_delay=int(entry_delay))
    fn = resolve_signal_fn(strategy)
    last = min(df.index[-1] for df in bars.values())
    entry_from = None
    if "start" in sc:
        first = pd.Timestamp(sc["start"], tz="UTC")
        if "min_history_bars" in sc:
            entry_from = asset_entry_dates(bars, int(sc["min_history_bars"]))
    else:
        # Periodo común: desde que todos los activos de la estrategia tienen 1 año de datos.
        first = max(df.index[0] for df in bars.values()) + pd.Timedelta(days=365)
    split = (
        pd.Timestamp(sc["is_end"], tz="UTC")
        if "is_end" in sc
        else first + (last - first) * s["validation"]["is_fraction"]
    )
    a, b = {
        "is": (first, split),
        "oos": (split + pd.Timedelta(days=1), last),
        "full": (first, last),
        # Candidatas: walk-forward SOLO dentro del IS (hipotesis.md §3).
        "wf": (first, split) if cand else (first, last),
        "robust": (first, split),
    }[mode]
    if cand and mode in ("is", "wf", "robust") and b > split:
        raise OOSGuardError("Una prueba IS no puede pasar de is_end")  # pragma: no cover
    ppy = periods_per_year(universe)
    run = partial(run_signals, entry_from=entry_from)
    res = run(bars, params, fn, cfg, a, b)
    st = metrics.summary(res.equity, res.trades, ppy, res.exposure)
    beq = benchmark_equity(data, bench, costs, a, b, cfg.initial_equity)
    bm = metrics.summary(beq, None, 252 if asset_class_of(bench) == "equity" else 365)
    stamp = datetime.now(MADRID).strftime("%Y%m%d-%H%M")
    tag = ("_stress" if costs_mode == "stress" else "") + (
        f"_delay{cfg.entry_delay}" if cfg.entry_delay else ""
    )
    out = reports_dir / strategy / f"{mode}{tag}_{stamp}"
    rep_rel = str(out.relative_to(reports_dir.parent)) + "/resumen.md"
    extra = []
    if res.kill_switch_date is not None:
        extra.append(
            f"**KILL SWITCH** activado el {res.kill_switch_date.date()} (sin entradas posteriores)."
        )
    if cfg.kill_switch_drawdown is None:
        extra.append(
            "Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas "
            "se miden sin él y los episodios se cuentan aparte."
        )
    if bench_info:
        extra.append(info_benchmark_section(data, bench_info, costs, a, b, cfg.initial_equity))
    if mode == "wf":
        if cand and "walkforward" in sc:
            extra.append(wf_fixed_section(bars, params, sc, fn, cfg, first, split, ppy, entry_from))
        else:
            extra.append(wf_legacy_section(bars, params, fn, cfg, a, b, s))
    if cand and mode in ("is", "oos", "full"):
        extra.append(
            candidate_sections(
                res,
                bars,
                params,
                sc,
                s,
                fn,
                costs,
                a,
                b,
                ppy,
                run,
                registry,
                strategy,
                rep_rel,
                mode,
                costs_mode,
            )
        )
    if mode == "robust":
        extra.append(
            robust_section(
                bars,
                params,
                sc.get("robust_keys", []),
                fn,
                cfg,
                a,
                b,
                s,
                ppy,
                res,
                run=run,
                sc=sc,
                registry=registry if cand else None,
                strategy=strategy,
                rep_rel=rep_rel,
            )
        )
    data_info = "\n".join(
        f"- {k}: {df.index[0].date()} → {df.index[-1].date()} ({len(df)} velas)"
        for k, df in data.items()
        if k in syms and len(df)
    )
    if entry_from:
        data_info += "\n" + "\n".join(
            f"- {k} entra al universo el {v.date()} (≥ {sc['min_history_bars']} velas)"
            for k, v in sorted(entry_from.items())
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
        + f"\n- Riesgo por operación: {cfg.risk_per_trade * 100:.2f} %; tope por posición: "
        + (
            f"{cfg.max_position_fraction * 100:.2f} % del equity"
            if cfg.max_position_fraction
            else "sin tope"
        )
    )
    n = append_registry(
        registry,
        strategy,
        {**params, "risk_per_trade": cfg.risk_per_trade} if cand else params,
        f"{mode}/{costs_mode}"
        + (f"/retraso {cfg.entry_delay} vela [no es variante]" if cfg.entry_delay else "")
        + ("/sin kill switch" if cfg.kill_switch_drawdown is None else ""),
        _key(st),
        rep_rel,
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


def info_benchmark_section(data, weights, costs, a, b, init) -> str:
    eq = mix_benchmark_equity(data, weights, costs, a, b, init)
    ppy = 365 if any(asset_class_of(x) == "crypto" for x in weights) else 252
    m = metrics.summary(eq, None, ppy)
    label = " / ".join(f"{k} {v * 100:.0f} %" for k, v in weights.items())
    if sum(weights.values()) < 1:
        label += f" / caja {(1 - sum(weights.values())) * 100:.0f} %"
    return (
        f"## Benchmark informativo ({label}, rebalanceo mensual, con costes)\n"
        f"CAGR {m['cagr'] * 100:.2f} %, Sharpe {m['sharpe']:.2f}, "
        f"DD {m['max_dd'] * 100:.1f} %"
    )


def wf_legacy_section(bars, params, fn, cfg, a, b, s) -> str:
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
            f"| {w.test_start.date()} → {w.test_end.date()} | {tr * 100:.2f} % | {len(rw.trades)} |"
        )
    rows.append(f"\nVentanas positivas: {pos}/{len(wins)}")
    return "\n".join(rows)


def walk_forward_fixed(bars, params, sc, fn, cfg, first, split, ppy, entry_from=None) -> list:
    """Walk-forward de hipotesis.md §3: entrenamiento creciente desde `first`, ventanas de
    prueba con fechas fijas; en cada paso se elige en la rejilla ±25 % la combinación con mayor
    Sharpe de entrenamiento (empate → la más cercana a la de por defecto). Cada prueba arranca
    sin posiciones y con el capital inicial. Devuelve una fila (dict) por ventana."""
    w = sc["walkforward"]
    keys = list(sc.get("robust_keys", []))
    wins = fixed_windows(first, w["first_test"], int(w["test_months"]), int(w["n_windows"]), split)
    grid = param_grid(params, keys, explicit=sc.get("robust_grid"))
    run = partial(run_signals, entry_from=entry_from)
    rows = []
    for win in wins:
        scored = []
        for p in grid:
            rt = run(bars, p, fn, cfg, win.train_start, win.train_end)
            scored.append((p, metrics.sharpe(rt.equity, ppy)))
        best = pick_best(scored, params, keys)
        rt = run(bars, best, fn, cfg, win.test_start, win.test_end)
        net = float(rt.equity.iloc[-1] - cfg.initial_equity)
        rows.append(
            {
                "window": win,
                "params": {k: best[k] for k in keys},
                "train_sharpe": dict((tuple(p[k] for k in keys), sh) for p, sh in scored)[
                    tuple(best[k] for k in keys)
                ],
                "trades": len(rt.trades),
                "net_usd": net,
                "valid": len(rt.trades) > 0,
                "positive": len(rt.trades) > 0 and net > 0,
            }
        )
    return rows


def wf_fixed_section(bars, params, sc, fn, cfg, first, split, ppy, entry_from) -> str:
    rows = walk_forward_fixed(bars, params, sc, fn, cfg, first, split, ppy, entry_from)
    keys = list(sc.get("robust_keys", []))
    lines = [
        "## Walk-forward IS (hipotesis.md §3: entrenamiento creciente, ventanas fijas)",
        "| entrenamiento | prueba | parámetros elegidos | Sharpe entreno | trades | neto $ |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        w = r["window"]
        ptxt = ", ".join(f"{k}={r['params'][k]}" for k in keys)
        lines.append(
            f"| {w.train_start.date()} → {w.train_end.date()} | {w.test_start.date()} → "
            f"{w.test_end.date()} | {ptxt} | {r['train_sharpe']:.2f} | {r['trades']} | "
            f"{r['net_usd']:.2f} |"
        )
    valid = sum(r["valid"] for r in rows)
    pos = sum(r["positive"] for r in rows)
    need = int(sc["walkforward"].get("min_valid_windows", 5))
    pct = pos / valid if valid else float("nan")
    ok = valid >= need and pct >= 0.6
    lines.append(
        f"\nVentanas válidas (con operaciones): {valid}/{len(rows)} (mínimo {need}). "
        f"Positivas: {pos}/{valid} ({pct * 100:.0f} %). Criterio 5 (≥ 60 %): "
        f"{'sí' if ok else 'no'}."
    )
    return "\n".join(lines)


def candidate_sections(
    res,
    bars,
    params,
    sc,
    s,
    fn,
    costs,
    a,
    b,
    ppy,
    run,
    registry,
    strategy,
    rep_rel,
    mode,
    costs_mode,
) -> str:
    """Informes extra de las candidatas: calibración de riesgo (P1), episodios de kill switch,
    quitar las 5 mejores, quitar el mejor activo, subperiodos por fecha de entrada, por activo."""
    lines = []
    thr = s["risk"]["kill_switch_drawdown"]
    if mode == "is":
        levels = [float(x) for x in sc.get("risk_levels", [0.01, 0.0075, 0.005])]
        dds, rows = {}, []
        cur = make_cfg(s, sc, costs).risk_per_trade
        for f in levels:
            if abs(f - cur) < 1e-12:
                r_f = res
            else:
                r_f = run(bars, params, fn, make_cfg(s, sc, costs, risk=f), a, b)
                st_f = metrics.summary(r_f.equity, r_f.trades, ppy, r_f.exposure)
                append_registry(
                    registry,
                    strategy,
                    {**params, "risk_per_trade": f},
                    f"is/{costs_mode}/sin kill switch/calibración de riesgo",
                    _key(st_f),
                    rep_rel,
                )
            dds[f] = metrics.max_drawdown(r_f.equity)
            rows.append(
                f"| {f * 100:.2f} % | {dds[f] * 100:.1f} % | "
                f"{len(kill_switch_episodes(r_f.equity, thr))} | "
                f"{metrics.cagr(r_f.equity) * 100:.2f} % | "
                f"{metrics.sharpe(r_f.equity, ppy):.2f} |"
            )
        if "calibration_dd_limit" not in sc:
            raise KeyError(
                f"Falta `calibration_dd_limit` en el TOML de {strategy} (R2-2: el límite de "
                "calibración sale de la estrategia, no de un valor por defecto)."
            )
        limit = float(sc["calibration_dd_limit"])
        chosen = calibrate_risk(dds, limit)
        lines += [
            "## Calibración del riesgo en IS (P1, hipotesis.md §3)",
            "| riesgo por operación | DD máx. IS | episodios kill switch | CAGR | Sharpe |",
            "|---|---|---|---|---|",
            *rows,
            "",
            (
                f"Riesgo seleccionado (mayor con caída ≤ {limit * 100:.0f} %; kill switch al "
                f"{thr * 100:.0f} %): **{chosen * 100:.2f} %**"
                if chosen is not None
                else f"**Ninguno** cumple caída ≤ {limit * 100:.0f} %: según P1 la candidata "
                "muere en IS."
            ),
            "",
        ]
    eps = kill_switch_episodes(res.equity, thr)
    lines += [
        "## Kill switch (P1): episodios con reinicio del máximo",
        f"Episodios de caída > {thr * 100:.0f} %: **{len(eps)}**"
        + (f"; primero (regla literal) el {eps[0].date()}" if eps else ""),
        "",
    ]
    tr = res.trades
    top5 = drop_top_trades(tr, 5)
    best, wo_best = drop_best_asset(tr)
    lines += [
        "## Dependencia de pocas operaciones / un activo",
        f"- P&L total: {tr['pnl_usd'].sum() if len(tr) else 0.0:.2f} $",
        f"- Sin las 5 mejores operaciones (criterio 9): {top5:.2f} $",
        f"- Sin el mejor activo ({best}) (criterio 13): {wo_best:.2f} $",
        "",
    ]
    if "subperiods" in sc:
        per = []
        for x, y in sc["subperiods"]:
            xa, yb = pd.Timestamp(x, tz="UTC"), pd.Timestamp(y, tz="UTC")
            if yb < a or xa > b:
                continue
            per.append((max(xa, a), min(yb, b), xa, yb))
        lines += [
            "## Subperiodos (operaciones por fecha de entrada, criterio 11)",
            "| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |",
            "|---|---|---|---|",
        ]
        for row, (_, _, xa, yb) in zip(
            expectancy_by_period(tr, [(p[0], p[1]) for p in per]), per, strict=True
        ):
            lines.append(
                f"| {xa.date()} → {yb.date()} | {row['start'].date()} → {row['end'].date()} | "
                f"{row['trades']} | {row['expectancy_r']:.3f} |"
            )
        lines.append("")
    ba = expectancy_by_asset(tr)
    lines += [
        "## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)",
        "| activo | trades | expectancy R | P&L $ |",
        "|---|---|---|---|",
        *[
            f"| {sym} | {int(r.trades)} | {r.expectancy_r:.3f} | {r.pnl_usd:.2f} |"
            for sym, r in ba.iterrows()
        ],
        "",
        f"Exposición media: {float(res.exposure.mean()) * 100:.1f} %",
    ]
    return "\n".join(lines)


def robust_section(
    bars,
    params,
    keys,
    fn,
    cfg: SimConfig,
    a,
    b,
    s,
    ppy,
    base,
    run=None,
    sc=None,
    registry=None,
    strategy="",
    rep_rel="",
) -> str:
    """Robustez IS. Con `registry` (candidatas) cada variante y prueba de estrés se anota."""
    run = run or run_signals
    sc = sc or {}
    lines = [
        "## Robustez (in-sample)",
        "| prueba | Sharpe | expectancy R | trades |",
        "|---|---|---|---|",
    ]

    def row(label, res, log_params=None, tag=""):
        st = metrics.summary(res.equity, res.trades, ppy)
        lines.append(
            f"| {label} | {st['sharpe']:.2f} | {st['expectancy_r']:.3f} | {st['trades']} |"
        )
        if registry is not None and log_params is not None:
            append_registry(
                registry,
                strategy,
                {**log_params, "risk_per_trade": cfg.risk_per_trade},
                f"robust-is/{tag}"
                + ("/sin kill switch" if cfg.kill_switch_drawdown is None else ""),
                _key(st),
                rep_rel,
            )
        return st

    st0 = row("central", base)
    neigh = []
    for p in param_grid(params, keys, explicit=sc.get("robust_grid")):
        if p != params:
            st = row(
                ", ".join(f"{k}={p[k]}" for k in keys), run(bars, p, fn, cfg, a, b), p, "rejilla"
            )
            neigh.append(st)
    for ev in sc.get("extra_variants", []):
        p = {**params, **ev}
        row(
            "suelta " + ", ".join(f"{k}={v}" for k, v in ev.items()),
            run(bars, p, fn, cfg, a, b),
            p,
            "prueba suelta",
        )
    row(
        "costes × 2",
        run(bars, params, fn, replace(cfg, costs=cost_models(s, "stress")), a, b),
        params,
        "estrés costes×2 [no es variante]",
    )
    row(
        "retraso 1 vela",
        run(bars, params, fn, replace(cfg, entry_delay=1), a, b),
        params,
        "estrés retraso 1 vela [no es variante]",
    )
    if neigh:
        sh0 = st0["sharpe"]
        ok = [
            (n["expectancy_r"] > 0) and (n["sharpe"] >= 0.5 * sh0) for n in neigh if n["trades"] > 0
        ]
        frac = sum(ok) / len(neigh)
        lines.append(
            f"\nRejilla ±25 %: {sum(ok)}/{len(neigh)} vecinas ({frac * 100:.0f} %) con "
            f"expectancy > 0 y Sharpe ≥ 50 % del central ({sh0:.2f}). Criterio 6 (≥ 70 %): "
            f"{'sí' if frac >= 0.7 else 'no'}."
        )
    lines.append(
        f"\nP&L total sin las 5 mejores operaciones: {drop_top_trades(base.trades, 5):.2f} $"
    )
    if len(base.trades):
        mc = monte_carlo_dd(base.trades, cfg.initial_equity)
        lines.append(
            f"Monte Carlo (1000, semilla 42): DD p50 {np.percentile(mc, 50) * 100:.1f}"
            f" %, p95 {np.percentile(mc, 95) * 100:.1f} %"
        )
    if "subperiods" not in sc:
        for x, y in subperiods(a, b, 3):
            row(f"subperiodo {x.date()}→{y.date()}", run(bars, params, fn, cfg, x, y))
    return "\n".join(lines)
