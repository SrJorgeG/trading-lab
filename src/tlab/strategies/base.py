"""Protocolo común de las estrategias por señales."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

SIGNAL_COLUMNS = ["entry", "exit", "stop_price"]  # opcionales: rank, target_price


class SignalFn(Protocol):
    def __call__(self, bars: pd.DataFrame, params: dict) -> pd.DataFrame:
        """bars: OHLCV de UN activo. Devuelve entry/exit (bool), stop_price (float), rank."""
        ...


def empty_signals(index: pd.Index) -> pd.DataFrame:
    return pd.DataFrame(
        {"entry": False, "exit": False, "stop_price": float("nan"), "rank": float("nan")},
        index=index,
    )
