"""Criterios de la ronda 2 (docs/hipotesis_ronda2.md §4) como funciones puras (R2-10).
Solo ordenan y formatean cifras: no deciden nada que no esté escrito en §4 y ninguna dice
«apta» (el veredicto es de Fable)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tlab.metrics import return_dd_ratio


def criterion_16(strat_cagr: float, cash_cagr: float, margin: float) -> bool:
    """margin > 0: strat >= cash + margin (16-IS, 16a, 16d). margin == 0: strat > cash (16b)."""
    if margin > 0:
        return bool(strat_cagr >= cash_cagr + margin)
    return bool(strat_cagr > cash_cagr)


def criterion_17(
    strat_cagr: float, strat_dd: float, n_trades: int, bench_cagr: float, bench_dd: float
) -> bool:
    """E9: False si n_trades == 0 o strat_cagr <= 0; True si la relación del benchmark es
    <= 0; si no, relación de la estrategia > relación del benchmark (estricto).
    Relación del benchmark no definida (NaN) → False (opción conservadora)."""
    if n_trades == 0 or strat_cagr <= 0:
        return False
    rb = return_dd_ratio(bench_cagr, bench_dd)
    if np.isnan(rb):
        return False
    if rb <= 0:
        return True
    return bool(return_dd_ratio(strat_cagr, strat_dd, n_trades) > rb)


def monte_carlo_dd_grouped(
    trades: pd.DataFrame, initial_equity: float, n: int = 1000, seed: int = 42
) -> np.ndarray:
    """Como ``robustness.monte_carlo_dd``, pero barajando la SUMA de las operaciones abiertas
    el mismo día (hallazgo B4). Informativo."""
    rng = np.random.default_rng(seed)
    pnl = trades.groupby(pd.to_datetime(trades["entry_date"]))["pnl_usd"].sum().to_numpy(float)
    out = np.empty(n)
    for i in range(n):
        eq = np.concatenate([[initial_equity], initial_equity + np.cumsum(rng.permutation(pnl))])
        peak = np.maximum.accumulate(eq)
        out[i] = float(np.max(1 - eq / peak))
    return out


def _pct(x: float) -> str:
    return f"{x * 100:.2f} %"


def checklist(tranche: str, **m) -> list[tuple[str, str, bool | None]]:
    """Filas (criterio, texto con las cifras, sí/no) de ese tramo. Solo se emiten las filas
    para las que llega la medida; ``None`` = no calculable. Solo ordena y formatea §4."""
    rows: list[tuple[str, str, bool | None]] = []
    if tranche == "is":
        if "expectancy_usd" in m:
            rows.append(
                ("0 expectancy > 0", f"{m['expectancy_usd']:.2f} $", m["expectancy_usd"] > 0)
            )
        if "max_dd_calibrated" in m:
            dd = m["max_dd_calibrated"]
            rows.append(("Calibración: caída ≤ 12 %", _pct(dd), dd >= -0.12))
        if "sharpe" in m:
            rows.append(("3-IS Sharpe ≥ 0,5", f"{m['sharpe']:.3f}", m["sharpe"] >= 0.5))
        if "cagr" in m and "cash_cagr" in m:
            rows.append(
                (
                    "16-IS CAGR ≥ caja + 2 pp",
                    f"{_pct(m['cagr'])} frente a caja {_pct(m['cash_cagr'])}",
                    criterion_16(m["cagr"], m["cash_cagr"], 0.02),
                )
            )
    elif tranche in ("holdout_old", "holdout_new"):
        if "expectancy_r" in m:
            e = m["expectancy_r"]
            rows.append(("2 expectancy > 0,10 R", f"{e:.3f} R", e > 0.10))
        if "sharpe" in m:
            rows.append(("3 Sharpe ≥ 0,5", f"{m['sharpe']:.3f}", m["sharpe"] >= 0.5))
        if "kill_switch_episodes" in m:
            k = m["kill_switch_episodes"]
            rows.append(("12 kill switch no salta", f"{k} episodios", k == 0))
        if "cagr" in m and "cash_cagr" in m:
            rows.append(
                (
                    "16b CAGR > caja",
                    f"{_pct(m['cagr'])} frente a caja {_pct(m['cash_cagr'])}",
                    criterion_16(m["cagr"], m["cash_cagr"], 0.0),
                )
            )
        if "g_old" in m or "joint_cagr" in m:
            j, jc = m.get("joint_cagr"), m.get("joint_cash_cagr")
            if j is None or jc is None:
                rows.append(("16a CAGR conjunto ≥ caja + 2 pp", "no calculable", None))
            else:
                rows.append(
                    (
                        "16a CAGR conjunto ≥ caja + 2 pp",
                        f"{_pct(j)} frente a caja {_pct(jc)}",
                        criterion_16(j, jc, 0.02),
                    )
                )
    elif tranche == "full":
        if "n_trades" in m:
            rows.append(("1 muestra ≥ 100 operaciones", f"{m['n_trades']}", m["n_trades"] >= 100))
        if "max_dd" in m:
            rows.append(("4 caída máxima ≤ 15 %", _pct(m["max_dd"]), m["max_dd"] >= -0.15))
        if {"cagr_16d", "ief_cagr_16d", "cash_cagr_16d"} <= m.keys():
            s, i, c = m["cagr_16d"], m["ief_cagr_16d"], m["cash_cagr_16d"]
            rows.append(
                (
                    "16d CAGR ≥ IEF y ≥ caja + 2 pp",
                    f"{_pct(s)}; IEF {_pct(i)}; caja {_pct(c)}",
                    bool(s >= i and criterion_16(s, c, 0.02)),
                )
            )
    if {"cagr", "max_dd", "n_trades", "spy_cagr", "spy_dd"} <= m.keys():
        key = {"is": "17-IS", "full": "17d"}.get(tranche, "17")
        mine = return_dd_ratio(m["cagr"], m["max_dd"], m["n_trades"])
        spy = return_dd_ratio(m["spy_cagr"], m["spy_dd"])
        rows.append(
            (
                f"{key} relación > relación de SPY",
                f"{mine:.3f} frente a {spy:.3f}",
                criterion_17(m["cagr"], m["max_dd"], m["n_trades"], m["spy_cagr"], m["spy_dd"]),
            )
        )
    return rows
