"""H5 `sector_mom` y H7 `sector_lowvol`: ranking mensual de un panel de ETFs (R2-7).

Cada primer día de sesión del mes (día de revisión) se ordenan los activos *aptos* por una
clave (momentum de `lookback` sesiones, o menos volatilidad). Entran los `top_n` primeros y
salen los que dejan de ser aptos o caen por debajo del puesto `keep_n`. Funciones PURAS.

Las dos funciones auxiliares (`panel_features`, `signals_from_order`) existen para que los
monos (R2-9) reutilicen EL MISMO código y solo cambien el orden.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.indicators import atr
from tlab.strategies.base import empty_signals

RANK_BY = ("mom", "lowvol")


@dataclass(frozen=True)
class PanelFeatures:
    review: pd.DatetimeIndex  # días de revisión (unión de índices, E7)
    eligible: pd.DataFrame  # bool, filas = review, columnas = símbolos ordenados
    key: pd.DataFrame  # float: clave verdadera (mom o −vol); NaN si no hay fila
    stop: dict[str, pd.Series]  # close − atr_mult·ATR, por símbolo, índice propio


def _check(bars: dict[str, pd.DataFrame], params: dict) -> None:
    if not bars:
        raise ValueError("`bars` está vacío")
    for s, df in bars.items():
        if not isinstance(df.index, pd.DatetimeIndex) or df.index.tz is None:
            raise ValueError(f"{s}: el índice debe ser DatetimeIndex con zona horaria (UTC)")
    top_n, keep_n = int(params.get("top_n", 3)), int(params.get("keep_n", 5))
    if int(params.get("lookback", 126)) < 1 or top_n < 1 or keep_n < top_n:
        raise ValueError("parámetros inválidos: lookback >= 1, top_n >= 1, keep_n >= top_n")
    if params.get("rank_by", "mom") not in RANK_BY:
        raise ValueError(f"rank_by debe ser uno de {RANK_BY}")


def review_days_union(bars: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Primera fecha de cada mes en la UNIÓN de índices; la primera fecha de la unión no cuenta."""
    union = pd.DatetimeIndex(sorted(set().union(*[df.index for df in bars.values()])))
    if len(union) == 0:
        return union
    month = union.tz_localize(None).to_period("M")
    first = pd.Series(~pd.Series(month).duplicated().to_numpy(), index=union)
    first.iloc[0] = False
    return union[first.to_numpy()]


def panel_features(bars: dict[str, pd.DataFrame], params: dict) -> PanelFeatures:
    """Aptitud, clave verdadera y stop de cada símbolo en los días de revisión."""
    _check(bars, params)
    lb = int(params.get("lookback", 126))
    mult, n_atr = float(params.get("atr_mult", 3.0)), int(params.get("atr_n", 20))
    rank_by = params.get("rank_by", "mom")
    symbols = sorted(bars)
    review = review_days_union(bars)
    elig = pd.DataFrame(False, index=review, columns=symbols)
    key = pd.DataFrame(np.nan, index=review, columns=symbols)
    stop: dict[str, pd.Series] = {}
    for s in symbols:
        df = bars[s]
        c = df["close"]
        mom = c / c.shift(lb) - 1
        vol = np.log(c / c.shift(1)).rolling(lb, min_periods=lb).std(ddof=1)
        a = atr(df, n_atr)
        k = mom if rank_by == "mom" else -vol
        apto = (mom > 0) & a.notna() & k.notna()
        stop[s] = c - mult * a
        here = review[review.isin(df.index)]
        elig.loc[here, s] = apto.reindex(here).to_numpy()
        key.loc[here, s] = k.reindex(here).to_numpy()
    return PanelFeatures(review=review, eligible=elig, key=key, stop=stop)


def signals_from_order(
    bars: dict[str, pd.DataFrame], feats: PanelFeatures, order_key: pd.DataFrame, params: dict
) -> dict[str, pd.DataFrame]:
    """Señales a partir de una clave de orden (mismas filas y columnas que `feats.key`).
    Orden de los aptos: (clave NaN al final, clave descendente, símbolo)."""
    _check(bars, params)
    top_n, keep_n = int(params.get("top_n", 3)), int(params.get("keep_n", 5))
    out = {s: empty_signals(df.index) for s, df in bars.items()}
    for s in bars:
        out[s]["stop_price"] = feats.stop[s].to_numpy()
    for t in feats.review:
        names = [s for s in feats.eligible.columns if t in bars[s].index]  # solo con vela en t
        aptos = [s for s in names if bool(feats.eligible.at[t, s])]
        ok = order_key.loc[t]
        aptos.sort(key=lambda s: (pd.isna(ok[s]), -ok[s] if pd.notna(ok[s]) else 0.0, s))
        puesto = {s: i + 1 for i, s in enumerate(aptos)}
        for s in names:
            apto = s in puesto
            o = out[s]
            o.at[t, "entry"] = apto and puesto[s] <= top_n
            o.at[t, "exit"] = (not apto) or puesto[s] > keep_n
            o.at[t, "rank"] = ok[s]
    for o in out.values():
        o["entry"] = o["entry"].astype(bool)
        o["exit"] = o["exit"].astype(bool)
    return out


def generate_signals_panel(bars: dict[str, pd.DataFrame], params: dict) -> dict[str, pd.DataFrame]:
    """= signals_from_order(bars, f, f.key, params) con f = panel_features(bars, params)."""
    f = panel_features(bars, params)
    return signals_from_order(bars, f, f.key, params)
