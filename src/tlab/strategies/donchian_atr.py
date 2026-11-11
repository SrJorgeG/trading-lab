"""BASELINE — ruptura Donchian long-only con stop inicial = cierre_señal − k·ATR.

Entrada: cierre_t > máximo de los `entry_n` máximos anteriores.
Salida: cierre_t < mínimo de los `exit_n` mínimos anteriores.
Stop (fijo, no se mueve): close_t − atr_mult × ATR_Wilder(atr_n)_t, calculado en la vela de señal.
Rank: (close − canal) / ATR (cuánto ha roto, en ATRs).
"""

from __future__ import annotations

import pandas as pd

from tlab.indicators import atr, donchian_high, donchian_low
from tlab.strategies.base import empty_signals


def generate_signals(bars: pd.DataFrame, params: dict) -> pd.DataFrame:
    en, ex = int(params.get("entry_n", 20)), int(params.get("exit_n", 10))
    k, n_atr = float(params.get("atr_mult", 2.0)), int(params.get("atr_n", 20))
    hi, lo, a = donchian_high(bars, en), donchian_low(bars, ex), atr(bars, n_atr)
    out = empty_signals(bars.index)
    out["entry"] = (bars["close"] > hi) & a.notna()
    out["exit"] = bars["close"] < lo
    out["stop_price"] = bars["close"] - k * a
    out["rank"] = (bars["close"] - hi) / a
    return out
