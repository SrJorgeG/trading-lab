"""Datos sintéticos deterministas (sin red)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def make_bars(
    n: int = 600,
    seed: int = 0,
    start: str = "2015-01-01",
    drift: float = 0.0003,
    vol: float = 0.015,
    freq: str = "B",
    p0: float = 100.0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC")
    r = rng.normal(drift, vol, n)
    close = p0 * np.exp(np.cumsum(r))
    open_ = np.concatenate([[p0], close[:-1]]) * np.exp(rng.normal(0, vol / 4, n))
    hi = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, vol / 2, n)))
    lo = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, vol / 2, n)))
    vol_ = rng.integers(1_000, 10_000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": hi, "low": lo, "close": close, "volume": vol_}, index=idx
    )


def flat_bars(
    prices: list[tuple[float, float, float, float]], start: str = "2020-01-01"
) -> pd.DataFrame:
    """Velas a mano: lista de (open, high, low, close)."""
    idx = pd.date_range(start, periods=len(prices), freq="B", tz="UTC")
    df = pd.DataFrame(prices, columns=["open", "high", "low", "close"], index=idx)
    df["volume"] = 1000.0
    return df


def manual_signals(index, entries=(), exits=(), stop=None, rank=None, target=None):
    sig = pd.DataFrame(
        {
            "entry": False,
            "exit": False,
            "stop_price": np.nan,
            "rank": np.nan if rank is None else rank,
        },
        index=index,
    )
    for i in entries:
        sig.iloc[i, sig.columns.get_loc("entry")] = True
    for i in exits:
        sig.iloc[i, sig.columns.get_loc("exit")] = True
    if stop is not None:
        sig["stop_price"] = stop
    return sig


@pytest.fixture
def bars():
    return make_bars()


@pytest.fixture
def settings():
    from tlab.config import load_settings

    return load_settings()
