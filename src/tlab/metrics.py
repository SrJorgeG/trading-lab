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


# --- Ronda 2 (R2-10): métricas nuevas, funciones puras ----------------------------------------


def return_dd_ratio(cagr_value: float, max_dd: float, n_trades: int | None = None) -> float:
    """CAGR / |caída máxima|. Caída 0: +inf si ``n_trades`` es None o > 0 y el CAGR es > 0;
    en otro caso NaN."""
    if max_dd == 0:
        if (n_trades is None or n_trades > 0) and cagr_value > 0:
            return float("inf")
        return float("nan")
    if not np.isfinite(max_dd):
        return float("nan")
    return float(cagr_value / abs(max_dd))


def joint_cagr(g_old: float, years_old: float, g_new: float, years_new: float) -> float:
    """(g_old · g_new) ** (1 / (años_old + años_new)) − 1. Criterio 16a."""
    return float((g_old * g_new) ** (1.0 / (years_old + years_new)) - 1.0)


def worst_calendar_year(eq: pd.Series) -> tuple[int, float]:
    """(año, rentabilidad) del peor año natural: último valor del año / último valor del año
    anterior − 1 (el primer año, contra el primer valor de la serie)."""
    last = eq.groupby(eq.index.year).last()
    prev = last.shift(1)
    prev.iloc[0] = float(eq.iloc[0])
    ret = last / prev - 1.0
    year = int(ret.idxmin())
    return year, float(ret.loc[year])


def losing_streaks(trades: pd.DataFrame) -> dict:
    """Rachas de operaciones perdedoras seguidas, ordenadas por (exit_date, entry_date, symbol).
    ``longest_n``: más pérdidas seguidas; ``longest_usd``: su suma (a igual longitud, la peor);
    ``deepest_usd``: la racha con peor suma. pnl == 0 corta la racha."""
    empty = {"longest_n": 0, "longest_usd": 0.0, "deepest_usd": 0.0}
    if len(trades) == 0:
        return empty
    cols = [c for c in ("exit_date", "entry_date", "symbol") if c in trades.columns]
    ordered = trades.sort_values(cols, kind="stable") if cols else trades
    streaks: list[tuple[int, float]] = []
    n, s = 0, 0.0
    for p in ordered["pnl_usd"].to_numpy(float):
        if p < 0:
            n, s = n + 1, s + p
        else:
            if n:
                streaks.append((n, s))
            n, s = 0, 0.0
    if n:
        streaks.append((n, s))
    if not streaks:
        return empty
    longest = max(streaks, key=lambda x: (x[0], -x[1]))
    return {
        "longest_n": longest[0],
        "longest_usd": float(longest[1]),
        "deepest_usd": float(min(x[1] for x in streaks)),
    }


def cash_adjusted_equity(eq: pd.Series, exposure: pd.Series, cash_eq: pd.Series) -> pd.Series:
    """Informativo (D13): efectivo parado rindiendo como la caja.
    adj[0] = eq[0];
    adj[t] = adj[t-1] · (eq[t]/eq[t-1] + (1 - exposure[t-1]) · (cash[t]/cash[t-1] - 1))."""
    e = eq.to_numpy(float)
    x = exposure.reindex(eq.index).to_numpy(float)
    c = cash_eq.reindex(eq.index).to_numpy(float)
    out = np.empty(len(e))
    out[0] = e[0]
    for t in range(1, len(e)):
        out[t] = out[t - 1] * (e[t] / e[t - 1] + (1.0 - x[t - 1]) * (c[t] / c[t - 1] - 1.0))
    return pd.Series(out, index=eq.index)
