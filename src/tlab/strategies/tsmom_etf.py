"""H2 — `tsmom_etf`: momentum de series temporales con revisión mensual (docs/hipotesis.md §6.2).

mom_t = cierre_t / cierre_{t−lookback} − 1 (cierres ajustados).
Día de revisión: la vela cuyo año-mes es distinto del de la vela anterior del mismo activo
(la primera vela de los datos NO es día de revisión).
Entrada: revisión y mom > 0 (y ATR disponible). Salida: revisión y mom <= 0.
Stop (fijo, de catástrofe): cierre_t − atr_mult × ATR_Wilder(atr_n)_t. Rank: mom.
Si mom es NaN: ni entrada ni salida.
"""

from __future__ import annotations

import pandas as pd

from tlab.indicators import atr
from tlab.strategies.base import empty_signals


def review_days(index: pd.DatetimeIndex) -> pd.Series:
    """True en la primera vela de cada mes presente en los datos (la primera vela: False)."""
    ym = pd.Series(index.year * 12 + index.month, index=index)
    prev = ym.shift(1)
    return (ym != prev) & prev.notna()


def generate_signals(bars: pd.DataFrame, params: dict) -> pd.DataFrame:
    lb = int(params.get("lookback", 252))
    k, n_atr = float(params.get("atr_mult", 4.0)), int(params.get("atr_n", 20))
    close = bars["close"]
    mom = close / close.shift(lb) - 1
    a = atr(bars, n_atr)
    rev = review_days(bars.index)
    has_mom = mom.notna()
    out = empty_signals(bars.index)
    out["entry"] = rev & has_mom & (mom > 0) & a.notna()
    out["exit"] = rev & has_mom & (mom <= 0)
    out["stop_price"] = close - k * a
    out["rank"] = mom
    return out
