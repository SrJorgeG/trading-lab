"""Protocolo común de las estrategias por señales (por activo y de panel)."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

SIGNAL_COLUMNS = ["entry", "exit", "stop_price"]  # opcionales: rank, target_price


class SignalFn(Protocol):
    def __call__(self, bars: pd.DataFrame, params: dict) -> pd.DataFrame:
        """bars: OHLCV de UN activo. Devuelve entry/exit (bool), stop_price (float), rank."""
        ...


class PanelSignalFn(Protocol):
    def __call__(self, bars: dict[str, pd.DataFrame], params: dict) -> dict[str, pd.DataFrame]:
        """bars: OHLCV por símbolo. Devuelve, por símbolo, un DataFrame con el MISMO índice
        que sus velas y columnas entry, exit (bool), stop_price, rank (float).

        Contrato (lo comprueban los tests): pura; causal (la fila `t` de cualquier símbolo
        solo depende de velas con fecha <= t de CUALQUIER símbolo); mismas claves e índices
        que `bars`; nunca entry y exit a la vez; sin estado (`exit` = «si lo tienes, véndelo»).
        """
        ...


def empty_signals(index: pd.Index) -> pd.DataFrame:
    return pd.DataFrame(
        {"entry": False, "exit": False, "stop_price": float("nan"), "rank": float("nan")},
        index=index,
    )


def as_panel(fn: SignalFn, extra_params: dict | None = None) -> PanelSignalFn:
    """Envuelve una estrategia por activo: {s: fn(df, params) for s, df in bars.items()}.
    `extra_params` se añade a una COPIA de `params` en cada llamada (p. ej. un calendario
    que no debe entrar en el hash ni en el registro)."""

    def panel(bars: dict[str, pd.DataFrame], params: dict) -> dict[str, pd.DataFrame]:
        p = {**params, **extra_params} if extra_params else params
        return {s: fn(df, p) for s, df in bars.items()}

    return panel
