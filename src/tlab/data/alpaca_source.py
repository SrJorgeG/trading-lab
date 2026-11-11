"""Fuente principal: Alpaca Market Data (claves PAPER desde .env; nunca se registran)."""

from __future__ import annotations

import logging
import os
import time

import pandas as pd

log = logging.getLogger(__name__)


class RateLimiter:
    """Limitador simple: como mucho `per_minute` llamadas en 60 s."""

    def __init__(self, per_minute: int = 200) -> None:
        self.min_interval = 60.0 / per_minute
        self._last = 0.0

    def wait(self) -> None:
        dt = time.monotonic() - self._last
        if dt < self.min_interval:
            time.sleep(self.min_interval - dt)
        self._last = time.monotonic()


def has_keys() -> bool:
    """True si hay claves de Alpaca en el entorno (.env cargado)."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:  # pragma: no cover
        pass
    return bool(os.getenv("ALPACA_API_KEY")) and bool(os.getenv("ALPACA_SECRET_KEY"))


_ADJUSTMENTS = ("all", "split", "raw", "dividend")


class AlpacaSource:
    name = "alpaca"

    def __init__(self, feed: str = "sip", adjustment: str = "all") -> None:
        if adjustment not in _ADJUSTMENTS:
            raise ValueError(f"ajuste Alpaca no soportado: {adjustment!r}")
        self.feed = feed
        self.adjustment = adjustment
        self.limiter = RateLimiter(200)
        self._stock = None
        self._crypto = None

    def _clients(self):
        from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient

        key, secret = os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY")
        if self._stock is None:
            self._stock = StockHistoricalDataClient(key, secret)
            self._crypto = CryptoHistoricalDataClient(key, secret)
        return self._stock, self._crypto

    def fetch(
        self, symbol: str, timeframe: str, start: pd.Timestamp, end: pd.Timestamp, asset_class: str
    ) -> pd.DataFrame:
        """Descarga velas (alpaca-py pagina con next_page_token internamente)."""
        from alpaca.data.enums import Adjustment, DataFeed
        from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        if timeframe != "1Day":
            raise ValueError("alpaca_source: de momento solo 1Day")
        stock, crypto = self._clients()
        # SIP histórico exige que el final sea de hace > 15 min.
        end = min(end, pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=16))
        self.limiter.wait()
        if asset_class == "crypto":
            req = CryptoBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start.to_pydatetime(),
                end=end.to_pydatetime(),
            )
            bars = crypto.get_crypto_bars(req)
        else:
            feed = DataFeed.SIP if self.feed == "sip" else DataFeed.IEX
            req = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start.to_pydatetime(),
                end=end.to_pydatetime(),
                adjustment=Adjustment(self.adjustment),
                feed=feed,
            )
            try:
                bars = stock.get_stock_bars(req)
            except Exception as e:  # error de suscripción SIP -> IEX
                if self.feed == "sip" and "subscription" in str(e).lower():
                    log.warning("SIP no permitido para %s; reintento con IEX", symbol)
                    self.feed = "iex"
                    return self.fetch(symbol, timeframe, start, end, asset_class)
                raise
        df = bars.df
        if df.empty:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol, level=0)
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        idx = pd.DatetimeIndex(df.index).tz_convert("UTC")
        # Normalizamos la vela diaria a las 00:00 UTC de su fecha (igual que yfinance).
        df.index = (
            idx.tz_convert("America/New_York").normalize().tz_localize(None).tz_localize("UTC")
            if asset_class == "equity"
            else idx.normalize()
        )
        return df
