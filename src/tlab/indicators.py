"""Indicadores causales (solo usan datos <= t). Nada de shift(-1) ni center=True."""

from __future__ import annotations

import pandas as pd


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift(1)
    return pd.concat(
        [df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1
    ).max(axis=1)


def wilder(s: pd.Series, n: int) -> pd.Series:
    """Media de Wilder (alpha = 1/n)."""
    return s.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """ATR de Wilder."""
    return wilder(true_range(df), n)


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """RSI de Wilder."""
    d = s.diff()
    up, down = wilder(d.clip(lower=0), n), wilder(-d.clip(upper=0), n)
    return 100 - 100 / (1 + up / down)


def donchian_high(df: pd.DataFrame, n: int) -> pd.Series:
    """Máximo de los n máximos ANTERIORES (excluye la vela actual)."""
    return df["high"].shift(1).rolling(n, min_periods=n).max()


def donchian_low(df: pd.DataFrame, n: int) -> pd.Series:
    """Mínimo de los n mínimos ANTERIORES (excluye la vela actual)."""
    return df["low"].shift(1).rolling(n, min_periods=n).min()


def roc(s: pd.Series, n: int) -> pd.Series:
    """Rentabilidad de n periodos: s_t / s_{t-n} - 1."""
    return s / s.shift(n) - 1
