"""Herramientas de robustez: rejilla ±25 %, quitar mejores operaciones, Monte Carlo, subperiodos.
(Costes × 2 y retraso de 1 vela se hacen con SimConfig: costs=stress, entry_delay=1.)"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd


def param_grid(params: dict, keys: list[str], pct: float = 0.25) -> list[dict]:
    """Combinaciones {−pct, 0, +pct} de cada parámetro numérico de `keys` (enteros redondeados)."""
    axes = []
    for k in keys:
        v = params[k]
        vals = [v * (1 - pct), v, v * (1 + pct)]
        if isinstance(v, int):
            vals = sorted({max(1, int(round(x))) for x in vals})
        axes.append([(k, x) for x in vals])
    return [{**params, **dict(c)} for c in itertools.product(*axes)]


def drop_top_trades(trades: pd.DataFrame, n: int = 5) -> float:
    """P&L total ($) quitando las n mejores operaciones."""
    if trades.empty:
        return 0.0
    return float(trades["pnl_usd"].sort_values(ascending=False).iloc[n:].sum())


def monte_carlo_dd(
    trades: pd.DataFrame, initial_equity: float, n: int = 1000, seed: int = 42
) -> np.ndarray:
    """Drawdowns máximos (positivos) al barajar el orden de las operaciones (semilla fija)."""
    rng = np.random.default_rng(seed)
    pnl = trades["pnl_usd"].to_numpy()
    out = np.empty(n)
    for i in range(n):
        eq = initial_equity + np.cumsum(rng.permutation(pnl))
        eq = np.concatenate([[initial_equity], eq])
        peak = np.maximum.accumulate(eq)
        out[i] = float(np.max(1 - eq / peak))
    return out


def subperiods(start, end, n: int = 3) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    step = (e - s) / n
    return [(s + step * i, s + step * (i + 1)) for i in range(n)]


# --- Añadido en el paso 2 (candidatas de docs/hipotesis.md) ---------------------------------


def kill_switch_episodes(equity: pd.Series, threshold: float = 0.10) -> list[pd.Timestamp]:
    """Fechas en las que el kill switch habría saltado (equity < máximo × (1 − umbral)),
    REINICIANDO el máximo tras cada episodio (hipotesis.md §3, P1). La primera fecha es la
    de la regla literal (parada permanente)."""
    out: list[pd.Timestamp] = []
    if equity.empty:
        return out
    peak = float(equity.iloc[0])
    for t, v in equity.items():
        v = float(v)
        peak = max(peak, v)
        if v < peak * (1 - threshold):
            out.append(t)
            peak = v  # reinicio: el siguiente episodio se mide desde aquí
    return out


def best_asset(trades: pd.DataFrame) -> str | None:
    """Activo con mayor P&L total ($)."""
    if trades.empty:
        return None
    return str(trades.groupby("symbol")["pnl_usd"].sum().idxmax())


def drop_best_asset(trades: pd.DataFrame) -> tuple[str | None, float]:
    """(activo que más ha ganado, P&L total quitando TODAS sus operaciones). Criterio 13."""
    b = best_asset(trades)
    if b is None:
        return None, 0.0
    return b, float(trades.loc[trades["symbol"] != b, "pnl_usd"].sum())


def expectancy_by_period(
    trades: pd.DataFrame, periods: list[tuple[pd.Timestamp, pd.Timestamp]]
) -> list[dict]:
    """Expectancy (R) por subperiodo, asignando cada operación por su FECHA DE ENTRADA
    (criterio 11). Límites inclusivos por fecha."""
    out = []
    ed = pd.to_datetime(trades["entry_date"]) if len(trades) else pd.Series(dtype="datetime64[ns]")
    for a, b in periods:
        m = (ed >= a) & (ed <= b) if len(trades) else []
        sub = trades[m] if len(trades) else trades
        out.append(
            {
                "start": a,
                "end": b,
                "trades": len(sub),
                "expectancy_r": float(sub["pnl_r"].mean()) if len(sub) else float("nan"),
            }
        )
    return out


def expectancy_by_asset(trades: pd.DataFrame) -> pd.DataFrame:
    """Nº de operaciones, expectancy (R) y P&L ($) por activo (criterio 11)."""
    if trades.empty:
        return pd.DataFrame(columns=["trades", "expectancy_r", "pnl_usd"])
    g = trades.groupby("symbol")
    return pd.DataFrame(
        {"trades": g.size(), "expectancy_r": g["pnl_r"].mean(), "pnl_usd": g["pnl_usd"].sum()}
    )


def calibrate_risk(max_dd_by_level: dict[float, float], limit: float = 0.10) -> float | None:
    """Mayor fracción de riesgo cuyo drawdown máximo IS (positivo o negativo) es <= `limit`.
    None = ninguna lo cumple (la candidata muere en IS). hipotesis.md §3, P1."""
    for f in sorted(max_dd_by_level, reverse=True):
        if abs(max_dd_by_level[f]) <= limit + 1e-12:
            return f
    return None
