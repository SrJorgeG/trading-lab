"""H3 — `rsi2_etf`: reversión a la media de muy corto plazo (docs/hipotesis.md §6.3).

Entrada: cierre > SMA(trend_n) y RSI_Wilder(rsi_n) < rsi_entry (y ATR disponible).
Salida: cierre > SMA(exit_sma_n).
Stop (fijo): cierre_t − atr_mult × ATR_Wilder(atr_n)_t. Rank: −RSI (más sobrevendido primero).
Las comparaciones con NaN dan False (nunca una entrada/salida por falta de datos).
"""

from __future__ import annotations

import pandas as pd

from tlab.indicators import atr, rsi, sma
from tlab.strategies.base import empty_signals


def generate_signals(bars: pd.DataFrame, params: dict) -> pd.DataFrame:
    rsi_n, rsi_entry = int(params.get("rsi_n", 2)), float(params.get("rsi_entry", 10.0))
    trend_n, exit_n = int(params.get("trend_n", 200)), int(params.get("exit_sma_n", 5))
    k, n_atr = float(params.get("atr_mult", 3.0)), int(params.get("atr_n", 20))
    close = bars["close"]
    r, a = rsi(close, rsi_n), atr(bars, n_atr)
    out = empty_signals(bars.index)
    out["entry"] = (close > sma(close, trend_n)) & (r < rsi_entry) & a.notna()
    out["exit"] = close > sma(close, exit_n)
    out["stop_price"] = close - k * a
    out["rank"] = -r
    return out
