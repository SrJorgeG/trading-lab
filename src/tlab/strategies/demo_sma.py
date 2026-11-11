"""DEMO — cruce de medias simple. Solo para probar la tubería; NO es una candidata."""

from __future__ import annotations

import pandas as pd

from tlab.indicators import atr, sma
from tlab.strategies.base import empty_signals


def generate_signals(bars: pd.DataFrame, params: dict) -> pd.DataFrame:
    fast, slow = int(params.get("fast", 20)), int(params.get("slow", 100))
    k, n_atr = float(params.get("atr_mult", 2.0)), int(params.get("atr_n", 14))
    f, s = sma(bars["close"], fast), sma(bars["close"], slow)
    above = f > s
    out = empty_signals(bars.index)
    out["entry"] = above & ~above.shift(1, fill_value=False)
    out["exit"] = (~above) & above.shift(1, fill_value=False)
    out["stop_price"] = bars["close"] - k * atr(bars, n_atr)
    out["rank"] = bars["close"] / s - 1
    return out
