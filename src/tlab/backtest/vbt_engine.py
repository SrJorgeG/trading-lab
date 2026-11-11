"""Envoltorio de vectorbt para análisis rápido POR ACTIVO y rejillas de parámetros.

No aplica las reglas de cartera (1 % de riesgo, máx. 3, kill switch): eso es portfolio_sim.
Señales desplazadas 1 vela; precio de ejecución = apertura de la vela de ejecución.
El stop absoluto se convierte en % respecto a la apertura de ejecución (sl_stop de vectorbt).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tlab.backtest.costs import CostModel


def run_single(
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    costs: CostModel,
    init_cash: float = 10_000.0,
    use_stop: bool = True,
):
    """Devuelve un vbt.Portfolio con todo el efectivo en cada entrada (size=inf)."""
    import vectorbt as vbt

    entries = signals["entry"].shift(1, fill_value=False).astype(bool)
    exits = signals["exit"].shift(1, fill_value=False).astype(bool)
    stop = signals["stop_price"].shift(1)
    sl = ((bars["open"] - stop) / bars["open"]).where(entries, np.nan)
    # Igual que portfolio_sim: si la apertura ya está por debajo del stop, no se entra.
    entries = entries & (sl > 0)
    kw = {}
    if use_stop:
        kw = {
            "sl_stop": sl.where(entries, np.nan).fillna(np.inf).values,
            "open": bars["open"],
            "high": bars["high"],
            "low": bars["low"],
            "stop_entry_price": "price",
        }
    return vbt.Portfolio.from_signals(
        close=bars["close"],
        entries=entries,
        exits=exits,
        price=bars["open"],
        size=np.inf,
        fees=costs.fee_rate,
        slippage=costs.slip,
        init_cash=init_cash,
        freq="1D",
        **kw,
    )
