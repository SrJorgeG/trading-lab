"""BASELINES de asignación mensual (pesos objetivo, sin stop por operación).

Cada función recibe `closes` (DataFrame de cierres DIARIOS, una columna por activo) y devuelve
un DataFrame de pesos objetivo indexado por la ÚLTIMA vela de cada mes presente en los datos.
El simulador aplica esos pesos a la apertura de la primera vela del mes siguiente
(la decisión usa solo cierres <= fin de mes: sin look-ahead).
Pesos que no suman 1 → el resto queda en efectivo (rentabilidad 0).
"""

from __future__ import annotations

import pandas as pd


def monthly_closes(closes: pd.DataFrame) -> pd.DataFrame:
    """Último cierre de cada mes, indexado por la fecha real de esa vela."""
    per = closes.index.year * 12 + closes.index.month
    last = pd.Series(per, index=closes.index)
    mask = last.ne(last.shift(-1))  # última vela de cada mes PRESENTE en los datos
    return closes[mask.to_numpy()]


def buy_hold(closes: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Peso fijo (por defecto 1/N) desde el primer mes."""
    m = monthly_closes(closes)
    w = params.get("weights") or {c: 1.0 / closes.shape[1] for c in closes.columns}
    return pd.DataFrame({c: float(w.get(c, 0.0)) for c in closes.columns}, index=m.index)


def faber_sma(closes: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Faber: largo (1/N) si cierre mensual > SMA de `months` cierres mensuales; si no, efectivo."""
    n = int(params.get("months", 10))
    m = monthly_closes(closes)
    sig = (m > m.rolling(n, min_periods=n).mean()).astype(float)
    return sig / closes.shape[1]


def tsmom(closes: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Momentum de series temporales: largo (1/N) si rentabilidad de `months` meses > 0.

    `skip` (opcional, por defecto 0) salta los últimos meses: con months=12, skip=1 se mide
    del mes t-12 al t-1 (el clásico "12-1"). Exige months > skip.
    """
    n, k = int(params.get("months", 12)), int(params.get("skip", 0))
    if not 0 <= k < n:
        raise ValueError(f"tsmom: hace falta 0 <= skip < months (skip={k}, months={n})")
    m = monthly_closes(closes)
    r = m.shift(k) / m.shift(n) - 1
    sig = (r > 0).astype(float).where(r.notna(), 0.0)
    return sig / closes.shape[1]


def dual_momentum(closes: pd.DataFrame, params: dict) -> pd.DataFrame:
    """GEM simplificado: el mejor de `risk` a `months` meses si supera al `tbill` (o a 0 si
    el tbill no tiene datos aún); si no, 100 % en `safe`."""
    n = int(params.get("months", 12))
    risk, safe = list(params.get("risk", ["SPY", "EFA"])), params.get("safe", "IEF")
    tbill = params.get("tbill", "BIL")
    m = monthly_closes(closes)
    r = m / m.shift(n) - 1
    w = pd.DataFrame(0.0, index=m.index, columns=closes.columns)
    for t in m.index:
        rr = r.loc[t, risk]
        if rr.isna().any():
            continue
        best = rr.idxmax()
        hurdle = r.loc[t, tbill] if tbill in r and pd.notna(r.loc[t, tbill]) else 0.0
        w.loc[t, best if rr[best] > hurdle else safe] = 1.0
    return w
