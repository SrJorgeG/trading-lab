"""Secciones de informe propias de la ronda 2 (R2-10). Solo MUESTRAN cifras: ningún texto
dice «apta» o «aprobada» (el veredicto es de Fable).

Las secciones que ya produce `runner.candidate_sections` (calibración, quitar las 5 mejores,
quitar el mejor activo, subperiodos, por activo) no se repiten aquí."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tlab import metrics
from tlab.backtest.criteria import checklist
from tlab.backtest.guards import read_log
from tlab.backtest.robustness import kill_switch_episodes, monte_carlo_dd
from tlab.backtest.runner import benchmark_equity, mix_benchmark_equity
from tlab.data.cash import cash_equity


def _pct(x: float) -> str:
    return "n/d" if x is None or not np.isfinite(x) else f"{x * 100:.2f} %"


def _fmt(x: float) -> str:
    return "n/d" if x is None or not np.isfinite(x) else f"{x:.3f}"


def _bench_row(name: str, eq: pd.Series) -> tuple[str, float, float, float]:
    c, d = metrics.cagr(eq), metrics.max_drawdown(eq)
    return name, c, d, metrics.return_dd_ratio(c, d)


def _base_equity(log_path: Path, strategy: str, h: str, tranche: str) -> pd.Series | None:
    """`equity.csv` del informe base de `tranche` (ruta en la columna `report` del log)."""
    for r in read_log(log_path):
        if (
            r["strategy"] == strategy
            and r["tranche"] == tranche
            and r["params_hash"] == h
            and (r["costs"], r["entry_delay"], r["kind"]) == ("base", "0", "candidata")
            and r["report"]
        ):
            p = log_path.parent.parent / Path(r["report"]).parent / "equity.csv"
            if not p.exists():
                return None
            df = pd.read_csv(p, index_col=0, parse_dates=True)
            return df.iloc[:, 0].astype(float)
    return None


def round2_sections(
    *,
    mode: str,
    res,
    bars: dict,
    data: dict,
    sc: dict,
    s: dict,
    tr,
    costs: dict,
    cfg,
    log_path: Path,
    strategy: str,
    h: str,
    cash_rate: pd.Series | None = None,
    **_ignored,
) -> str:
    """Texto markdown con benchmarks, caja, relaciones y casillas del tramo. La réplica devuelve
    vacío (E3: solo `criterio15.md`, sin CAGR)."""
    if mode == "replica":
        return ""
    if mode not in ("is", "holdout_old", "holdout_new", "full"):
        return ""
    eq, trades = res.equity, res.trades
    a, b = tr.start, tr.end
    init = cfg.initial_equity
    out = ["## Ronda 2: benchmarks, caja y relaciones (solo cifras)"]
    rows = [_bench_row("Estrategia", eq)]
    bench = sc.get("benchmark", "SPY")
    rows.append(_bench_row(bench, benchmark_equity(data, bench, costs, a, b, init)))
    mix = dict(sc.get("benchmark_info", {}))
    if mix:
        label = " / ".join(f"{int(v * 100)} % {k}" for k, v in mix.items())
        rows.append(_bench_row(label, mix_benchmark_equity(data, mix, costs, a, b, init)))
    cash = None
    if cash_rate is not None:
        cash = cash_equity(cash_rate, eq.index, init)
        rows.append(_bench_row("Caja (letras a 3 meses)", cash))
    out += [
        "| | CAGR | caída máxima | relación CAGR/|caída| |",
        "|---|---|---|---|",
        *[f"| {n} | {_pct(c)} | {_pct(d)} | {_fmt(r)} |" for n, c, d, r in rows],
    ]
    if cash is None:
        out.append("\n_Caja no disponible en esta ejecución (no se pasó la serie de tipos)._")
    cagr_s, dd_s = rows[0][1], rows[0][2]
    n_tr = len(trades)
    year, yret = metrics.worst_calendar_year(eq)
    st = metrics.losing_streaks(trades)
    exp_mean = float(res.exposure.mean()) if res.exposure is not None else float("nan")
    out += [
        "",
        f"- Exposición media: {_pct(exp_mean)}",
        f"- Peor año natural: {year} ({_pct(yret)})",
        f"- Peor racha de pérdidas: {st['longest_n']} seguidas (suma {st['longest_usd']:.2f} $); "
        f"la de peor suma: {st['deepest_usd']:.2f} $",
    ]
    if cash is not None and res.exposure is not None:
        adj = metrics.cash_adjusted_equity(eq, res.exposure, cash)
        out.append(
            f"- Informativo: efectivo rindiendo como la caja → CAGR {_pct(metrics.cagr(adj))}, "
            f"caída máxima {_pct(metrics.max_drawdown(adj))}"
        )
    kse = kill_switch_episodes(eq, 0.15)
    out.append(
        f"- Episodios de kill switch al 15 % (máximo reiniciado tras cada uno): {len(kse)}"
        + (f"; el primero, {kse[0].date()}" if kse else "")
    )

    m: dict = {
        "cagr": cagr_s,
        "max_dd": dd_s,
        "n_trades": n_tr,
        "spy_cagr": rows[1][1],
        "spy_dd": rows[1][2],
    }
    stats = metrics.trade_stats(trades)
    if cash is not None:
        m["cash_cagr"] = metrics.cagr(cash)
    if mode == "is":
        m.update(
            expectancy_usd=stats["expectancy_usd"],
            sharpe=metrics.sharpe(eq),
            max_dd_calibrated=dd_s,
        )
    if mode in ("holdout_old", "holdout_new"):
        m.update(
            expectancy_r=stats["expectancy_r"],
            sharpe=metrics.sharpe(eq),
            kill_switch_episodes=len(kse),
        )
    if mode == "holdout_new":
        base = _base_equity(log_path, strategy, h, "holdout_old")
        if base is None or cash is None or cash_rate is None:
            m["g_old"] = None  # 16a «no calculable»
        else:
            cash_old = cash_equity(cash_rate, base.index, init)
            yo, yn = metrics.years(base), metrics.years(eq)
            m["g_old"] = float(base.iloc[-1] / base.iloc[0])
            m["joint_cagr"] = metrics.joint_cagr(
                m["g_old"], yo, float(eq.iloc[-1] / eq.iloc[0]), yn
            )
            m["joint_cash_cagr"] = metrics.joint_cagr(
                float(cash_old.iloc[-1] / cash_old.iloc[0]),
                yo,
                float(cash.iloc[-1] / cash.iloc[0]),
                yn,
            )
    if mode == "full":
        m["n_trades"] = n_tr
        if n_tr:
            mc = monte_carlo_dd(trades, init, 1000, 42)
            p95 = _pct(float(np.percentile(mc, 95)))
            out.append(f"- Monte Carlo (1.000 barajados, semilla 42): p95 de la caída {p95}")
        fi, fi_from = sc.get("fixed_income"), sc.get("fixed_income_from")
        if fi and fi_from and cash_rate is not None and fi in data:
            ief = benchmark_equity(data, fi, costs, pd.Timestamp(fi_from, tz="UTC"), b, init)
            tail = eq[eq.index >= pd.Timestamp(fi_from, tz="UTC")]
            cash_tail = cash_equity(cash_rate, tail.index, init)
            m.update(
                cagr_16d=metrics.cagr(tail),
                ief_cagr_16d=metrics.cagr(ief),
                cash_cagr_16d=metrics.cagr(cash_tail),
            )
    out += ["", "## Casillas de este tramo (cifras; el veredicto lo escribe Fable)"]
    out += [
        "| criterio | cifras | cumple |",
        "|---|---|---|",
        *[
            f"| {c} | {t} | {'sí' if ok else 'no' if ok is not None else 'no calculable'} |"
            for c, t, ok in checklist(mode, **m)
        ],
    ]
    return "\n".join(out)
