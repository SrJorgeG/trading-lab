"""Fuente de respaldo: yfinance (precios ajustados, sin claves)."""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)


def to_yf_symbol(symbol: str) -> str:
    """BTC/USD -> BTC-USD."""
    return symbol.replace("/", "-")


class YFinanceSource:
    name = "yfinance"
    adjustment = "auto_adjust"
    feed = "yahoo"

    def fetch(
        self, symbol: str, timeframe: str, start: pd.Timestamp, end: pd.Timestamp, asset_class: str
    ) -> pd.DataFrame:
        """Descarga velas diarias ajustadas. Índice UTC a las 00:00 de la fecha de sesión."""
        import yfinance as yf

        if timeframe != "1Day":
            raise ValueError("yf_source solo implementa 1Day")
        raw = yf.download(
            to_yf_symbol(symbol),
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=True,
            progress=False,
            multi_level_index=False,
            threads=False,
        )
        if raw is None or raw.empty:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = raw.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
        idx = pd.DatetimeIndex(df.index)
        idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
        df.index = idx.normalize()
        # Conservador: descartamos la vela de hoy (UTC), que puede estar sin cerrar.
        today = pd.Timestamp.now(tz="UTC").normalize()
        df = df[df.index < today]
        return df.astype(float)
