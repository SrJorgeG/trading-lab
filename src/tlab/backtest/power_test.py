"""R2-19 (E22/A1): test de potencia SINTÉTICO. Sin datos reales.

Series inventadas de 9 activos. En la versión «con ventaja» la deriva de cada activo persiste
unos meses (proceso de Ornstein-Uhlenbeck), de modo que la fuerza de 6 meses SÍ predice el
siguiente mes; en la versión «sin ventaja» la deriva es la misma para todos. Cada serie pasa por
`sector_mom` (parámetros por defecto del TOML) y por los criterios de §4 A que se pueden calcular
en sintético. Informativo: no cambia ningún criterio.

Criterios calculados: 0 (expectancy > 0), 3-IS (Sharpe >= 0,5), 16-IS (CAGR >= caja + 2 pp, caja
constante), 17-IS (relación frente a un «SPY» sintético = media de los 9) y 14 (p < 0,02 frente a
monos `rank`; con n monos el p mínimo es 1/(n+1), así que hacen falta n >= 50).
NO se calculan aquí: 5 (walk-forward), 6 (robustez), 7-IS, 8-IS, 10-IS, calibración de riesgo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tlab import metrics
from tlab.backtest.criteria import criterion_16, criterion_17
from tlab.backtest.custom_monkeys import run_custom_monkeys
from tlab.backtest.targets import build_target
from tlab.config import load_strategy_config

NAMES = [f"S{i}" for i in range(1, 10)]
BENCH = "SPYX"
CASH_RATE = 0.03  # caja sintética constante (anual)
START, IS_START, IS_END = "2006-01-02", "2007-07-02", "2020-12-31"


def synthetic_series(
    edge: float, seed: int, n_days: int = 4000, noise: float = 0.012, common: float = 0.0003
) -> dict[str, pd.DataFrame]:
    """9 activos + `SPYX` (media de los 9). `edge` = desviación típica DIARIA de la deriva
    persistente de cada activo (0 = sin ventaja). Derivas con memoria de ~100 sesiones."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, int(edge * 1e6)]))
    idx = pd.bdate_range(START, periods=n_days, tz="UTC")
    phi = 0.99
    sd_innov = edge * np.sqrt(1 - phi**2)
    mu = np.zeros((n_days, len(NAMES)))
    for t in range(1, n_days):
        mu[t] = phi * mu[t - 1] + rng.normal(0, sd_innov, len(NAMES))
    market = rng.normal(0, 0.008, n_days)[:, None]
    ret = common + mu + market + rng.normal(0, noise, (n_days, len(NAMES)))
    close = 100 * np.exp(np.cumsum(ret, axis=0))
    out = {}
    for j, s in enumerate(NAMES):
        out[s] = _bars(close[:, j], idx)
    out[BENCH] = _bars(close.mean(axis=1), idx)
    return out


def _bars(close: np.ndarray, idx: pd.DatetimeIndex) -> pd.DataFrame:
    o = np.r_[close[0], close[:-1]]
    return pd.DataFrame(
        {
            "open": o,
            "high": np.maximum(o, close) * 1.002,
            "low": np.minimum(o, close) * 0.998,
            "close": close,
            "volume": 1_000_000.0,
        },
        index=idx,
    )


def synthetic_config(is_end: str = IS_END) -> dict:
    """Config de `sector_mom` (parámetros por defecto del TOML) sobre nombres inventados."""
    sc = dict(load_strategy_config("sector_mom"))
    is_tranche = {"start": IS_START, "end": is_end, "universe": "universe", "slippage_bps": 5}
    sc.update(
        universe=NAMES,
        benchmark=BENCH,
        benchmark_info={},
        start=IS_START,
        is_end=is_end,
        end=is_end,
        frozen=False,
        tranches={"is": is_tranche},
    )
    return sc


def evaluate_series(
    data: dict, settings: dict, n_monkeys: int, seed: int = 42, n_jobs: int = -1
) -> dict[str, bool | float]:
    """Pasa UNA serie sintética por los criterios calculables. Devuelve booleanos por criterio
    y las cifras (sharpe, cagr, p)."""
    last = data[NAMES[0]].index[-1].strftime("%Y-%m-%d")
    sc = synthetic_config(min(IS_END, last))
    t = build_target(
        "sector_mom", data=data, settings=settings, strat_cfg=sc, kill_switch=False, tranche="is"
    )
    run = t.run(t.params, "is")
    eq, trades = run.equity, run.trades
    stats = metrics.trade_stats(trades)
    cagr, dd = metrics.cagr(eq), metrics.max_drawdown(eq)
    spy = data[BENCH]
    spy = spy[(spy.index >= eq.index[0]) & (spy.index <= eq.index[-1])]["close"]
    spy_cagr, spy_dd = metrics.cagr(spy), metrics.max_drawdown(spy)
    shp = metrics.sharpe(eq)
    res = run_custom_monkeys(t, "rank", n=n_monkeys, seed=seed, n_jobs=n_jobs)
    row: dict[str, bool | float] = {
        "c0": bool(stats["expectancy_usd"] > 0) if stats["trades"] else False,
        "c3": bool(shp >= 0.5),
        "c16": criterion_16(cagr, CASH_RATE, 0.02),
        "c17": criterion_17(cagr, dd, int(stats["trades"]), spy_cagr, spy_dd),
        "c14": bool(res.p_value < 0.02),
        "sharpe": float(shp),
        "cagr": float(cagr),
        "p": float(res.p_value),
    }
    row["todos"] = all(bool(row[k]) for k in ("c0", "c3", "c16", "c17", "c14"))
    return row


def run_power(
    edge: float,
    n_series: int,
    settings: dict,
    n_monkeys: int = 99,
    seed: int = 42,
    n_days: int = 4000,
    n_jobs: int = -1,
) -> pd.DataFrame:
    """Una fila por serie (semilla `seed` * 1000 + i)."""
    rows = [
        evaluate_series(
            synthetic_series(edge, seed * 1000 + i, n_days), settings, n_monkeys, seed, n_jobs
        )
        for i in range(n_series)
    ]
    return pd.DataFrame(rows)


def pass_rates(df: pd.DataFrame) -> pd.Series:
    """Frecuencia de «sí» por criterio y conjunta."""
    return df[["c0", "c3", "c16", "c17", "c14", "todos"]].mean()
