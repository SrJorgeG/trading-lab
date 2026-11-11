"""Carga de velas con caché parquet incremental."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

import pandas as pd

from tlab.config import ROOT, asset_class_of
from tlab.data.validate import validate_bars

log = logging.getLogger(__name__)
COLS = ["open", "high", "low", "close", "volume"]


class Source(Protocol):
    name: str
    adjustment: str
    feed: str

    def fetch(
        self, symbol: str, timeframe: str, start: pd.Timestamp, end: pd.Timestamp, asset_class: str
    ) -> pd.DataFrame: ...


def pick_source(source: str = "auto") -> Source:
    """auto: Alpaca si hay claves; si no, yfinance (y lo registra)."""
    from tlab.data.alpaca_source import AlpacaSource, has_keys
    from tlab.data.yf_source import YFinanceSource

    if source == "alpaca" or (source == "auto" and has_keys()):
        return AlpacaSource()
    if source == "auto":
        log.warning("Sin claves de Alpaca: uso yfinance como fuente de datos")
    return YFinanceSource()


def _ts(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def cache_path(cache_dir: Path, src: Source, symbol: str, timeframe: str) -> Path:
    safe = symbol.replace("/", "_").replace("-", "_")
    return cache_dir / f"{src.name}__{safe}__{timeframe}__{src.adjustment}__{src.feed}.parquet"


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df[COLS].astype(float)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def load_bars(
    symbols: list[str],
    timeframe: str = "1Day",
    start=None,
    end=None,
    asset_class: str | None = None,
    source: Source | str = "auto",
    cache_dir: Path | str | None = None,
) -> dict[str, pd.DataFrame]:
    """Devuelve {símbolo: DataFrame OHLCV} con índice UTC ordenado y sin duplicados.

    La caché guarda el rango pedido en un .json al lado; si el rango nuevo está dentro,
    no se hace ninguna llamada de red. Si no, solo se pide lo que falta.
    """
    src = pick_source(source) if isinstance(source, str) else source
    cdir = Path(cache_dir) if cache_dir else ROOT / "data_cache"
    cdir.mkdir(parents=True, exist_ok=True)
    start_ts = _ts(start or "2003-01-01")
    end_ts = _ts(end) if end is not None else pd.Timestamp.now(tz="UTC").normalize()
    out: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        ac = asset_class or asset_class_of(sym)
        p = cache_path(cdir, src, sym, timeframe)
        meta_p = p.with_suffix(".json")
        df = pd.read_parquet(p) if p.exists() else pd.DataFrame(columns=COLS)
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else None
        parts = [df] if len(df) else []
        if meta is None:
            parts.append(src.fetch(sym, timeframe, start_ts, end_ts, ac))
            m_start, m_end = start_ts, end_ts
        else:
            m_start, m_end = _ts(meta["start"]), _ts(meta["end"])
            if start_ts < m_start:
                parts.append(src.fetch(sym, timeframe, start_ts, m_start, ac))
                m_start = start_ts
            if end_ts > m_end:
                # Repedimos desde la última vela guardada (puede haberse cerrado después).
                last = df.index.max() if len(df) else m_end
                parts.append(src.fetch(sym, timeframe, min(last, m_end), end_ts, ac))
                m_end = end_ts
        parts = [x for x in parts if len(x)]
        full = _clean(pd.concat(parts)) if parts else pd.DataFrame(columns=COLS)
        if meta is None or m_start != _ts(meta["start"]) or m_end != _ts(meta["end"]):
            full.to_parquet(p)
            meta_p.write_text(
                json.dumps(
                    {"start": str(m_start), "end": str(m_end), "source": src.name, "symbol": sym}
                )
            )
        issues = validate_bars(full, ac)
        if issues:
            log.info("%s: %s", sym, "; ".join(issues))
        out[sym] = full.loc[(full.index >= start_ts) & (full.index <= end_ts)]
    return out
