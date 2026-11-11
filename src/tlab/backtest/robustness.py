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
