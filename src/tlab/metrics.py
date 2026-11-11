"""Métricas puras sobre la curva de equity y la lista de operaciones."""

from __future__ import annotations

import numpy as np
import pandas as pd


def total_return(eq: pd.Series) -> float:
    return float(eq.iloc[-1] / eq.iloc[0] - 1)


def years(eq: pd.Series) -> float:
    return (eq.index[-1] - eq.index[0]).days / 365.25


def cagr(eq: pd.Series) -> float:
    y = years(eq)
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / y) - 1) if y > 0 else float("nan")


def daily_returns(eq: pd.Series) -> pd.Series:
    return eq.pct_change().dropna()


def ann_vol(eq: pd.Series, periods: int = 252) -> float:
    return float(daily_returns(eq).std(ddof=1) * np.sqrt(periods))


def sharpe(eq: pd.Series, periods: int = 252) -> float:
    r = daily_returns(eq)
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(periods)) if sd > 0 else float("nan")


def sortino(eq: pd.Series, periods: int = 252) -> float:
    r = daily_returns(eq)
    dd = np.sqrt((np.minimum(r, 0) ** 2).mean())
    return float(r.mean() / dd * np.sqrt(periods)) if dd > 0 else float("nan")


def drawdown(eq: pd.Series) -> pd.Series:
    return eq / eq.cummax() - 1


def max_drawdown(eq: pd.Series) -> float:
    """Caída máxima desde un máximo (negativa, p. ej. -0.25)."""
    return float(drawdown(eq).min())


def max_dd_duration_days(eq: pd.Series) -> int:
    """Máximo tiempo bajo el agua (días naturales)."""
    under = drawdown(eq) < 0
    best, start = 0, None
    for t, u in under.items():
        if u and start is None:
            start = t
        elif not u and start is not None:
            best = max(best, (t - start).days)
            start = None
    if start is not None:
        best = max(best, (eq.index[-1] - start).days)
    return best


def calmar(eq: pd.Series) -> float:
    m = max_drawdown(eq)
    return float(cagr(eq) / -m) if m < 0 else float("nan")


def trade_stats(trades: pd.DataFrame) -> dict:
    """Nº, win rate, expectancy ($ y R), profit factor, duración media (días)."""
    n = len(trades)
    if n == 0:
        return {
            "trades": 0,
            "win_rate": np.nan,
            "expectancy_usd": np.nan,
            "expectancy_r": np.nan,
            "profit_factor": np.nan,
            "avg_days": np.nan,
        }
    p = trades["pnl_usd"]
    gains, losses = p[p > 0].sum(), -p[p < 0].sum()
    dur = (pd.to_datetime(trades["exit_date"]) - pd.to_datetime(trades["entry_date"])).dt.days
    return {
        "trades": n,
        "win_rate": float((p > 0).mean()),
        "expectancy_usd": float(p.mean()),
        "expectancy_r": float(trades["pnl_r"].mean()) if "pnl_r" in trades else np.nan,
        "profit_factor": float(gains / losses) if losses > 0 else float("inf"),
        "avg_days": float(dur.mean()),
    }


def summary(
    eq: pd.Series,
    trades: pd.DataFrame | None = None,
    periods: int = 252,
    exposure: pd.Series | None = None,
) -> dict:
    """Todas las métricas en un dict."""
    out = {
        "start": str(eq.index[0].date()),
        "end": str(eq.index[-1].date()),
        "total_return": total_return(eq),
        "cagr": cagr(eq),
        "vol": ann_vol(eq, periods),
        "sharpe": sharpe(eq, periods),
        "sortino": sortino(eq, periods),
        "max_dd": max_drawdown(eq),
        "max_dd_days": max_dd_duration_days(eq),
        "calmar": calmar(eq),
    }
    if exposure is not None:
        out["avg_exposure"] = float(exposure.mean())
    if trades is not None:
        out.update(trade_stats(trades))
    return out
