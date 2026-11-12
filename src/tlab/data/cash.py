"""Benchmark de «caja»: letras del Tesoro a 3 meses (R2-4, enmiendas E10 y E14/D3).

Toda la matemática (conversión de base, capitalización) es pura y se prueba sin red.
`load_tbill_rate` es la única función que toca red (solo scripts y tests `network`).
"""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import pandas as pd

DAYS_PER_YEAR = 365.25  # el mismo reloj que metrics.years
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
MAX_GAP_DAYS = 10  # hueco máximo (días naturales) aceptado en ^IRX entre 2000-07-01 y 2026-10-31
CHECK_FROM = pd.Timestamp("2000-07-01", tz="UTC")
CHECK_TO = pd.Timestamp("2026-10-31", tz="UTC")


def discount_to_yield(d: float | pd.Series) -> float | pd.Series:
    """Tipo de descuento (tanto por uno, base 360, letra a 91 días) → rentabilidad
    equivalente: y = 365·d / (360 − 91·d). E10."""
    return 365.0 * d / (360.0 - 91.0 * d)


def cash_equity(rate: pd.Series, index: pd.DatetimeIndex, init: float) -> pd.Series:
    """Capital en caja sobre `index`: eq[0] = init;
    eq[i] = eq[i−1] · (1 + y[i−1]) ** ((index[i] − index[i−1]).days / 365,25),
    con y = `rate` alineado a `index` rellenando hacia delante (último tipo conocido <= fecha).
    Función pura. ValueError si no hay tipo conocido en `index[0]` (no se inventa uno)."""
    if len(index) == 0:
        return pd.Series(dtype=float, index=index)
    r = rate.sort_index()
    union = r.index.union(index)
    y = r.reindex(union).ffill().reindex(index)
    if pd.isna(y.iloc[0]):
        raise ValueError(
            f"No hay tipo de caja conocido en {index[0]} (la serie empieza después): "
            "no se inventa uno."
        )
    days = pd.Series(index, index=index).diff().dt.days.to_numpy()
    yv = y.to_numpy(dtype=float)
    eq = [float(init)]
    for i in range(1, len(index)):
        eq.append(eq[-1] * (1.0 + yv[i - 1]) ** (days[i] / DAYS_PER_YEAR))
    return pd.Series(eq, index=index, name="cash")


def _fred_series(series: str) -> pd.Series:
    """CSV público de FRED (sin clave ni datos personales). «.» = sin dato."""
    with urllib.request.urlopen(FRED_URL.format(series=series), timeout=60) as resp:  # noqa: S310
        raw = resp.read().decode()
    df = pd.read_csv(io.StringIO(raw), na_values=["."])
    df.columns = ["date", "value"]
    idx = pd.to_datetime(df["date"]).dt.tz_localize("UTC")
    return pd.Series(df["value"].to_numpy(dtype=float) / 100.0, index=idx).dropna()


def _max_gap_days(s: pd.Series) -> int:
    w = s.loc[(s.index >= CHECK_FROM) & (s.index <= CHECK_TO)]
    if len(w) < 2:
        return 10**6
    return int(w.index.to_series().diff().dt.days.max())


def load_tbill_rate(
    settings: dict, cache_dir: Path | None = None, source: str | None = None
) -> tuple[pd.Series, dict]:
    """Serie diaria (índice UTC) del tipo a 3 meses en tanto por uno y YA en base de
    rentabilidad. Segundo valor: {"source", "basis_original", "converted", "first", "last",
    "max_gap_days"} para el informe. Toca red (solo scripts y tests `network`).

    `source`: None = `^IRX` y, si no sirve (no existe, empieza tarde o tiene huecos de más de
    10 días naturales), `DTB3` de FRED. "fred" o "yfinance" fuerzan una fuente.
    Base (E10): `^IRX` y `DTB3` son tipos de DESCUENTO (o no se puede confirmar otra cosa) →
    se convierten con `discount_to_yield`."""
    cfg = settings.get("data", {}).get("round2", {})
    irx, fred = cfg.get("cash_symbol", "^IRX"), cfg.get("cash_fallback", "DTB3")
    s: pd.Series | None = None
    used = ""
    if source in (None, "yfinance"):
        from tlab.data.loader import load_bars
        from tlab.data.yf_source import YFinanceSource

        bars = load_bars(
            [irx],
            "1Day",
            start=cfg.get("history_start", "1993-01-01"),
            asset_class="equity",
            source=YFinanceSource(),
            cache_dir=cache_dir,
        )[irx]
        if len(bars):
            cand = bars["close"].dropna() / 100.0
            if (
                cand.index[0] <= pd.Timestamp("2000-06-01", tz="UTC")
                and _max_gap_days(cand) <= MAX_GAP_DAYS
            ):
                s, used = cand, f"yfinance {irx}"
        if s is None and source == "yfinance":
            raise ValueError(f"{irx} no sirve (no existe, empieza tarde o tiene huecos largos).")
    if s is None:
        s, used = _fred_series(fred), f"FRED {fred}"
    converted = discount_to_yield(s)
    info = {
        "source": used,
        "basis_original": "descuento (banco, base 360); no se ha podido confirmar otra",
        "converted": True,
        "first": s.index[0],
        "last": s.index[-1],
        "max_gap_days": _max_gap_days(s),
    }
    return converted, info
