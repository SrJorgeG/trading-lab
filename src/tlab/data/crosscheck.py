"""Contraste yfinance ↔ Alpaca (hipotesis.md §3 "Motor de datos", tareas_sonnet.md tarea 2).

Se comparan las RENTABILIDADES DIARIAS cierre a cierre (no los precios: los ajustes por
dividendos cambian el nivel pero no deberían cambiar las rentabilidades) en el tramo común.

Tolerancias (fijadas aquí, antes de ver ningún contraste real):
- ETFs: |Δ rentabilidad| ≤ 10 pb en ≥ 99 % de los días comunes y correlación ≥ 0,999.
  Misma bolsa y mismo cierre oficial; las diferencias esperables son puntuales (día del
  dividendo si el ajuste se aplica distinto). Un 1 % de días ≈ 25 días en 10 años.
- Cripto: |Δ rentabilidad| ≤ 100 pb en ≥ 95 % de los días comunes y correlación ≥ 0,99.
  Son mercados distintos (Yahoo agrega varios exchanges; Alpaca es su propio mercado), los
  dos con vela diaria que corta a las 00:00 UTC; LTC y BCH tienen poca liquidez en Alpaca.
- En los dos: ≤ 2 % de días que estén en una fuente y falten en la otra, y el desfase de
  calendario con mayor correlación debe ser 0 (si es ±1, las velas están desplazadas un día).
Si algún activo no cumple, el veredicto es REVISAR y el script termina con código 1 (parar).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

TOLERANCES = {
    "equity": {"abs_diff": 0.0010, "share_ok": 0.99, "min_corr": 0.999},
    "crypto": {"abs_diff": 0.0100, "share_ok": 0.95, "min_corr": 0.99},
}
MAX_MISSING_SHARE = 0.02
COMMON_START = {"equity": "2016-01-01", "crypto": "2021-01-01"}


@dataclass
class CheckResult:
    symbol: str
    asset_class: str
    first_yf: str
    first_alpaca: str
    common_days: int
    missing_in_alpaca: int
    missing_in_yf: int
    corr: float
    best_lag: int
    median_abs_diff_bp: float
    p99_abs_diff_bp: float
    max_abs_diff_bp: float
    max_diff_date: str
    share_within_tol: float
    verdict: str
    reasons: str


def compare_returns(
    symbol: str,
    asset_class: str,
    yf: pd.DataFrame,
    alp: pd.DataFrame,
    start,
    end,
) -> tuple[CheckResult, pd.DataFrame]:
    """Compara dos series OHLCV del mismo activo. Devuelve el resumen y el detalle diario."""
    tol = TOLERANCES[asset_class]
    s, e = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    a = yf.loc[(yf.index >= s) & (yf.index <= e), "close"]
    b = alp.loc[(alp.index >= s) & (alp.index <= e), "close"]
    first_yf = str(yf.index[0].date()) if len(yf) else "—"
    first_alp = str(alp.index[0].date()) if len(alp) else "—"
    common = a.index.intersection(b.index)
    miss_alp = len(a.index.difference(b.index))
    miss_yf = len(b.index.difference(a.index))
    ra = a.loc[common].pct_change()
    rb = b.loc[common].pct_change()
    det = pd.DataFrame({"ret_yf": ra, "ret_alpaca": rb}).dropna()
    det["abs_diff"] = (det["ret_yf"] - det["ret_alpaca"]).abs()
    reasons = []
    if len(det) < 20:
        res = CheckResult(symbol, asset_class, first_yf, first_alp, len(det), miss_alp, miss_yf,
                          float("nan"), 0, float("nan"), float("nan"), float("nan"), "—", 0.0,
                          "REVISAR", "menos de 20 días comunes")  # fmt: skip
        return res, det
    corr = float(det["ret_yf"].corr(det["ret_alpaca"]))
    lags = {}
    for lag in (-1, 0, 1):
        lags[lag] = float(ra.corr(rb.shift(lag)))
    best_lag = max(lags, key=lambda k: lags[k] if np.isfinite(lags[k]) else -np.inf)
    share = float((det["abs_diff"] <= tol["abs_diff"]).mean())
    n_ref = max(len(a), 1)
    if share < tol["share_ok"]:
        reasons.append(
            f"solo {share * 100:.1f} % de días dentro de ±{tol['abs_diff'] * 1e4:.0f} pb "
            f"(mínimo {tol['share_ok'] * 100:.0f} %)"
        )
    if corr < tol["min_corr"]:
        reasons.append(f"correlación {corr:.4f} < {tol['min_corr']}")
    if (miss_alp + miss_yf) / n_ref > MAX_MISSING_SHARE:
        reasons.append(f"días que faltan: {miss_alp} en Alpaca, {miss_yf} en yfinance")
    if best_lag != 0:
        reasons.append(f"mejor correlación con desfase {best_lag:+d} día(s)")
    imax = det["abs_diff"].idxmax()
    res = CheckResult(
        symbol=symbol,
        asset_class=asset_class,
        first_yf=first_yf,
        first_alpaca=first_alp,
        common_days=len(det),
        missing_in_alpaca=miss_alp,
        missing_in_yf=miss_yf,
        corr=corr,
        best_lag=best_lag,
        median_abs_diff_bp=float(det["abs_diff"].median() * 1e4),
        p99_abs_diff_bp=float(det["abs_diff"].quantile(0.99) * 1e4),
        max_abs_diff_bp=float(det["abs_diff"].max() * 1e4),
        max_diff_date=str(pd.Timestamp(imax).date()),
        share_within_tol=share,
        verdict="OK" if not reasons else "REVISAR",
        reasons="; ".join(reasons) or "-",
    )
    return res, det


def results_table(results: list[CheckResult]) -> str:
    """Tabla markdown con un activo por fila."""
    lines = [
        "| activo | 1.ª vela yf | 1.ª vela Alpaca | días comunes | faltan (Alp/yf) | corr | "
        "desfase | mediana pb | p99 pb | máx pb (fecha) | % dentro tol. | veredicto | motivo |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        d = asdict(r)
        lines.append(
            f"| {d['symbol']} | {d['first_yf']} | {d['first_alpaca']} | {d['common_days']} | "
            f"{d['missing_in_alpaca']}/{d['missing_in_yf']} | {d['corr']:.4f} | "
            f"{d['best_lag']:+d} | {d['median_abs_diff_bp']:.1f} | {d['p99_abs_diff_bp']:.1f} | "
            f"{d['max_abs_diff_bp']:.1f} ({d['max_diff_date']}) | "
            f"{d['share_within_tol'] * 100:.1f} % | **{d['verdict']}** | {d['reasons']} |"
        )
    return "\n".join(lines)


def _as_utc_midnight(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Fecha de sesión a medianoche UTC (igual que las velas de equity del loader)."""
    idx = pd.DatetimeIndex(idx)
    if len(idx) == 0:
        return pd.DatetimeIndex([], tz="UTC")
    if idx.tz is None:
        return idx.normalize().tz_localize("UTC")
    return idx.tz_convert("America/New_York").normalize().tz_localize(None).tz_localize("UTC")


def attach_dividends(det: pd.DataFrame, dividends: pd.Series) -> pd.DataFrame:
    """Añade `div_amount`, `is_exdiv` y `abs_diff_bp` al detalle diario de compare_returns."""
    out = det.copy()
    if "abs_diff" in out.columns and "abs_diff_bp" not in out.columns:
        out["abs_diff_bp"] = out["abs_diff"] * 1e4
    if dividends is None or len(dividends) == 0:
        out["div_amount"] = float("nan")
        out["is_exdiv"] = False
        return out
    div = dividends.copy()
    div.index = _as_utc_midnight(pd.DatetimeIndex(div.index))
    div = div[~div.index.duplicated(keep="last")]
    aligned = div.reindex(out.index)
    out["div_amount"] = aligned.astype(float)
    out["is_exdiv"] = out["div_amount"].notna() & (out["div_amount"] != 0)
    return out


def exdiv_overlap_stats(det: pd.DataFrame, tol: float = 0.001) -> dict:
    """Cruza días fuera de tolerancia con fechas ex-dividendo (`is_exdiv` de attach_dividends)."""
    if "is_exdiv" not in det.columns or "abs_diff" not in det.columns:
        raise ValueError("hace falta el detalle de compare_returns tras attach_dividends")
    over = det["abs_diff"] > tol
    n_over = int(over.sum())
    n_ex = int(det["is_exdiv"].sum())
    n_both = int((over & det["is_exdiv"]).sum())
    return {
        "n_over": n_over,
        "n_exdiv": n_ex,
        "n_over_and_exdiv": n_both,
        "share_over_that_are_exdiv": (n_both / n_over) if n_over else float("nan"),
        "share_exdiv_that_are_over": (n_both / n_ex) if n_ex else float("nan"),
    }
