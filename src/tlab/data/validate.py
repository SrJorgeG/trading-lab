"""Validación de velas OHLCV."""

from __future__ import annotations

import pandas as pd

OHLC = ["open", "high", "low", "close"]


def validate_bars(
    df: pd.DataFrame, asset_class: str = "equity", max_gap_days: int | None = None
) -> list[str]:
    """Devuelve una lista de problemas (vacía = OK). Informa, no corrige ni rellena."""
    issues: list[str] = []
    if df.empty:
        return ["sin datos"]
    if not df.index.is_monotonic_increasing:
        issues.append("índice no ordenado")
    if df.index.has_duplicates:
        issues.append(f"{int(df.index.duplicated().sum())} fechas duplicadas")
    nan_rows = df[OHLC].isna().any(axis=1)
    if nan_rows.any():
        issues.append(f"{int(nan_rows.sum())} velas con NaN en OHLC")
    d = df.dropna(subset=OHLC)
    bad_hi = d["high"] < d[["open", "close"]].max(axis=1) - 1e-9
    bad_lo = d["low"] > d[["open", "close"]].min(axis=1) + 1e-9
    if bad_hi.any():
        issues.append(f"{int(bad_hi.sum())} velas con high < max(open, close)")
    if bad_lo.any():
        issues.append(f"{int(bad_lo.sum())} velas con low > min(open, close)")
    if "volume" in d and (d["volume"] < 0).any():
        issues.append("volumen negativo")
    if max_gap_days is None:
        # Cripto cotiza todos los días; acciones: un puente largo son 4 días naturales.
        max_gap_days = 1 if asset_class == "crypto" else 4
    gaps = d.index.to_series().diff().dt.days
    big = gaps[gaps > max_gap_days]
    if len(big):
        first = big.index[0].date()
        issues.append(f"{len(big)} huecos > {max_gap_days} días (primero antes de {first})")
    return issues
