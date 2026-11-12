"""Objetivo común de las herramientas de robustez (barrido de parámetros y benchmark al azar).

Un ``Target`` junta todo lo necesario para re-ejecutar una estrategia con otros parámetros
(o con señales al azar) usando EXACTAMENTE el mismo motor, costes, reglas duras y periodo:

- estrategias por señales (``SIGNAL_STRATEGIES``) → ``portfolio_sim.simulate`` (1 % de riesgo,
  stop, máx. posiciones, kill switch opcional);
- estrategias de asignación mensual (``ALLOCATION_STRATEGIES``) → ``allocation_sim``.

Los periodos IS/OOS se calculan igual que ``runner.run_backtest``: desde 1 año después de que el
activo más joven tenga datos (o ``start``), con el corte ``is_end`` del TOML o ``is_fraction``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from tlab import metrics
from tlab.backtest.allocation_sim import simulate_weights
from tlab.backtest.costs import CostModel, cost_models
from tlab.backtest.portfolio_sim import SimConfig, SimResult, simulate
from tlab.backtest.runner import OOSGuardError, asset_entry_dates, periods_per_year
from tlab.config import ROOT, asset_class_of, load_settings, load_strategy_config
from tlab.strategies import ALLOCATION_STRATEGIES, SIGNAL_STRATEGIES

PERIODS = ("is", "oos", "full")
# Parámetros por defecto de las estrategias de asignación (no tienen TOML: son baselines).
ALLOC_DEFAULTS = {
    "buy_hold": {},
    "faber_sma10m": {"months": 10},
    "tsmom_12m": {"months": 12, "skip": 0},
    "dual_momentum": {"months": 12, "risk": ["SPY", "EFA"], "safe": "IEF", "tbill": "BIL"},
}


def check_period(period: str, confirm_oos: bool) -> None:
    """Las herramientas de robustez trabajan en in-sample. OOS/full exigen --confirm-oos."""
    if period not in PERIODS:
        raise ValueError(f"periodo desconocido: {period} (usa {', '.join(PERIODS)})")
    if period != "is" and not confirm_oos:
        raise OOSGuardError(
            f"El periodo '{period}' incluye datos out-of-sample. Barrer parámetros o comparar "
            "contra el azar ahí 'gasta' el OOS. Si de verdad procede, repite con --confirm-oos "
            "(queda anotado en reports/oos_log.csv)."
        )


@dataclass
class RunOutput:
    """Resultado mínimo de una ejecución: curva, operaciones y exposición diaria."""

    equity: pd.Series
    trades: pd.DataFrame
    exposure: pd.Series
    kill_switch_date: pd.Timestamp | None = None
    weights: pd.DataFrame | None = None


@dataclass
class Target:
    strategy: str
    kind: str  # "signals" | "weights"
    universe: list[str]
    bars: dict[str, pd.DataFrame]
    params: dict
    cfg: SimConfig
    bounds: dict[str, tuple[pd.Timestamp, pd.Timestamp]]
    ppy: int
    kill_switch: bool = True
    costs_mode: str = "base"
    label: str = ""
    meta: dict = field(default_factory=dict)
    # Candidatas: primera fecha en la que cada activo entra al universo (>= 365 velas).
    entry_from: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ identificación
    @property
    def slug(self) -> str:
        """Nombre de carpeta: estrategia + universo (asignación) + sin kill switch."""
        s = self.strategy
        if self.kind == "weights":
            s += "_" + "-".join(u.replace("/", "") for u in self.universe).lower()
        if not self.kill_switch and self.kind == "signals":
            s += "_nokill"
        return s

    def fingerprint(self) -> str:
        """Huella de datos + configuración (para la caché)."""
        d = {
            "strategy": self.strategy,
            "kind": self.kind,
            "universe": self.universe,
            "bounds": {k: [str(a), str(b)] for k, (a, b) in self.bounds.items()},
            "cfg": {
                "init": self.cfg.initial_equity,
                "risk": self.cfg.risk_per_trade,
                "maxpos": self.cfg.max_positions,
                "gross": self.cfg.max_gross_exposure,
                "kill": self.cfg.kill_switch_drawdown,
                "frac": self.cfg.allow_fractional,
                "cap": self.cfg.max_position_fraction,
                "costs": {k: repr(v) for k, v in sorted(self.cfg.costs.items())},
            },
            "data": {
                s: [
                    str(df.index[0]),
                    str(df.index[-1]),
                    len(df),
                    round(float(df["close"].sum()), 6),
                ]
                for s, df in sorted(self.bars.items())
            },
        }
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]

    # ------------------------------------------------------------------ ejecución
    def window(self, period: str) -> tuple[pd.Timestamp, pd.Timestamp]:
        return self.bounds[period]

    def sliced_bars(self, period: str) -> dict[str, pd.DataFrame]:
        a, b = self.window(period)
        out = {}
        for s, df in self.bars.items():
            lo = max(a, self.entry_from[s]) if s in self.entry_from else a
            out[s] = df[(df.index >= lo) & (df.index <= b)]
        return {s: df for s, df in out.items() if len(df)}

    def signals(self, params: dict) -> dict[str, pd.DataFrame]:
        """Señales con TODA la historia (son causales), como ``runner.run_signals``."""
        fn = SIGNAL_STRATEGIES[self.strategy]
        return {s: fn(df, params) for s, df in self.bars.items()}

    def weights(self, params: dict, period: str) -> pd.DataFrame:
        """Pesos mensuales con toda la historia, recortados a las decisiones del periodo."""
        fn = ALLOCATION_STRATEGIES[self.strategy]
        w = fn(self.closes(), params)
        a, b = self.window(period)
        return w[(w.index >= a) & (w.index <= b)]

    def closes(self) -> pd.DataFrame:
        return pd.DataFrame({s: self.bars[s]["close"] for s in self.universe}).dropna(how="all")

    def run(self, params: dict, period: str = "is") -> RunOutput:
        """Ejecuta la estrategia con ``params`` en el periodo dado."""
        if self.kind == "signals":
            sigs = self.signals(params)
            return self.run_with_signals(sigs, period)
        return self.run_with_weights(self.weights(params, period), period)

    def run_with_signals(self, sigs: dict[str, pd.DataFrame], period: str) -> RunOutput:
        a, b = self.window(period)
        bb = self.sliced_bars(period)
        ss = {s: sigs[s][(sigs[s].index >= bb[s].index[0]) & (sigs[s].index <= b)] for s in bb}
        r: SimResult = simulate(bb, ss, self.cfg)
        return RunOutput(r.equity, r.trades, r.exposure, r.kill_switch_date)

    def run_with_weights(self, w: pd.DataFrame, period: str) -> RunOutput:
        a, b = self.window(period)
        closes = self.closes()
        closes = closes[closes.index <= b]
        bars = {s: self.bars[s].reindex(closes.index) for s in self.universe}
        eq, tr = simulate_weights(
            bars, w, self.cfg.costs, self.cfg.initial_equity, start=a.tz_convert(None)
        )
        # Exposición aproximada = suma de pesos objetivo vigentes (se ejecutan la vela siguiente).
        tgt = w.sum(axis=1)
        pos_in_cal = {d: i for i, d in enumerate(closes.index)}
        ex = pd.Series(np.nan, index=closes.index)
        for d, v in tgt.items():
            i = pos_in_cal.get(d)
            if i is not None and i + 1 < len(closes.index):
                ex.iloc[i + 1] = v
        expo = ex.ffill().fillna(0.0).reindex(eq.index).fillna(0.0)
        return RunOutput(eq, tr if len(tr) else pd.DataFrame(), expo, None, w)

    def with_kill_switch(self, on: bool) -> Target:
        kill = self.meta.get("kill_threshold", 0.15) if on else None
        return replace(self, cfg=replace(self.cfg, kill_switch_drawdown=kill), kill_switch=on)


# ---------------------------------------------------------------------- métricas

# nombre → (etiqueta en español, formato, "mayor es mejor")
METRICS: dict[str, tuple[str, str, bool]] = {
    "sharpe": ("Sharpe", "f2", True),
    "cagr": ("CAGR", "pct", True),
    "max_dd": ("Máx. caída", "pct", True),  # negativa: más cerca de 0 = mejor
    "mar": ("MAR (CAGR / caída)", "f2", True),
    "expectancy_r": ("Expectancy (R)", "f3", True),
    "trades": ("Nº operaciones", "int", True),
    "exposure": ("Exposición media", "pct", True),
    "total_return": ("Rentabilidad total", "pct", True),
    "win_rate": ("Win rate", "pct", True),
    "avg_hold": ("Duración media (velas)", "f1", True),
}
SCORABLE = ("sharpe", "cagr", "max_dd", "mar", "expectancy_r")


def holding_bars(trades: pd.DataFrame, bars: dict[str, pd.DataFrame]) -> np.ndarray:
    """Duración de cada operación en VELAS del propio activo (entrada → salida)."""
    if trades is None or trades.empty or "entry_date" not in trades:
        return np.array([], dtype=float)
    out = []
    for _, t in trades.iterrows():
        idx = bars[t["symbol"]].index
        out.append(idx.get_loc(t["exit_date"]) - idx.get_loc(t["entry_date"]))
    return np.asarray(out, dtype=float)


def extract_metrics(run: RunOutput, ppy: int, bars: dict | None = None) -> dict:
    """Métricas de una ejecución (las mismas que ``metrics.summary``) + MAR y exposición."""
    eq = run.equity
    m = {
        "sharpe": metrics.sharpe(eq, ppy),
        "cagr": metrics.cagr(eq),
        "max_dd": metrics.max_drawdown(eq),
        "total_return": metrics.total_return(eq),
        "exposure": float(run.exposure.mean()) if len(run.exposure) else float("nan"),
    }
    m["mar"] = m["cagr"] / -m["max_dd"] if m["max_dd"] < 0 else float("nan")
    tr = run.trades
    if run.weights is None:  # señales: operaciones cerradas con P&L y R
        ts = metrics.trade_stats(tr)
        m["trades"] = int(ts["trades"])
        m["expectancy_r"] = ts["expectancy_r"]
        m["win_rate"] = ts["win_rate"]
        hb = holding_bars(tr, bars) if bars is not None else np.array([])
        m["avg_hold"] = float(hb.mean()) if len(hb) else float("nan")
    else:  # pesos: nº de órdenes, sin R
        m["trades"] = int(len(tr))
        m["expectancy_r"] = float("nan")
        m["win_rate"] = float("nan")
        m["avg_hold"] = float("nan")
    m["kill_switch"] = str(run.kill_switch_date.date()) if run.kill_switch_date is not None else ""
    return {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in m.items()}


# ---------------------------------------------------------------------- construcción


def _bounds(
    bars: dict[str, pd.DataFrame],
    settings: dict,
    is_end: str | None,
    start: str | None,
    exact_start: bool = False,
) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """`exact_start` (candidatas): el periodo empieza en `start` y cada activo entra cuando
    tiene historia suficiente, en vez de esperar al activo más joven."""
    first = max(df.index[0] for df in bars.values()) + pd.Timedelta(days=365)
    if start is not None:
        first = (
            pd.Timestamp(start, tz="UTC")
            if exact_start
            else max(first, pd.Timestamp(start, tz="UTC"))
        )
    last = min(df.index[-1] for df in bars.values())
    split = (
        pd.Timestamp(is_end, tz="UTC")
        if is_end
        else first + (last - first) * settings["validation"]["is_fraction"]
    )
    return {
        "is": (first, split),
        "oos": (split + pd.Timedelta(days=1), last),
        "full": (first, last),
    }


def build_target(
    strategy: str,
    universe: list[str] | None = None,
    *,
    kill_switch: bool = True,
    costs_mode: str = "base",
    data: dict[str, pd.DataFrame] | None = None,
    settings: dict | None = None,
    strat_cfg: dict | None = None,
    params: dict | None = None,
    start: str | None = None,
    is_end: str | None = None,
) -> Target:
    """Construye el objetivo con los mismos costes/reglas que ``runner.run_backtest``.

    ``data`` permite pasar velas ya cargadas (tests); si no, se leen de la caché de datos.
    """
    s = settings or load_settings()
    sc: dict = {}
    if strategy in SIGNAL_STRATEGIES:
        kind = "signals"
        sc = strat_cfg if strat_cfg is not None else load_strategy_config(strategy)
        uni = list(universe or sc["universe"])
        p = dict(sc.get("params", {}))
        is_end = is_end or sc.get("is_end")
        label = sc.get("status", "")
    elif strategy in ALLOCATION_STRATEGIES:
        kind = "weights"
        uni = list(universe or ["SPY"])
        p = json.loads(json.dumps(ALLOC_DEFAULTS.get(strategy, {})))
        label = "baseline"
    else:
        known = sorted(SIGNAL_STRATEGIES) + sorted(ALLOCATION_STRATEGIES)
        raise ValueError(f"estrategia desconocida: {strategy}. Disponibles: {', '.join(known)}")
    if params:
        p.update(params)
    if data is None:
        from tlab.data.loader import load_bars, pick_source

        src = pick_source(sc.get("data_source", s["data"]["source"]))
        data = load_bars(
            uni,
            "1Day",
            start=s["data"]["history_start"],
            source=src,
            cache_dir=ROOT / s["data"]["cache_dir"],
        )
        data_src = f"{src.name} (ajuste: {src.adjustment})"
    else:
        data_src = "datos pasados por el llamador"
    bars = {u: data[u] for u in uni}
    if "end" in sc:  # nada posterior al fin de datos pre-registrado
        end_ts = pd.Timestamp(sc["end"], tz="UTC")
        bars = {u: df[df.index <= end_ts] for u, df in bars.items()}
    exact = kind == "signals" and "start" in sc and start is None
    if exact:
        start = sc["start"]
    entry_from = (
        asset_entry_dates(bars, int(sc["min_history_bars"]))
        if exact and "min_history_bars" in sc
        else {}
    )
    costs: dict[str, CostModel] = cost_models(s, costs_mode)
    r = s["risk"]
    cfg = SimConfig(
        initial_equity=s["capital"]["virtual_equity_usd"],
        risk_per_trade=sc.get("risk_per_trade", r["risk_per_trade"]),
        max_position_fraction=r.get("max_position_fraction"),
        max_positions=r["max_positions"],
        max_gross_exposure=r["max_gross_exposure"],
        kill_switch_drawdown=r["kill_switch_drawdown"] if kill_switch else None,
        costs=costs,
    )
    if kind == "weights":
        ppy = 365 if any(asset_class_of(u) == "crypto" for u in uni) else 252
    else:
        ppy = periods_per_year(uni)
    return Target(
        strategy=strategy,
        kind=kind,
        universe=uni,
        bars=bars,
        params=p,
        cfg=cfg,
        bounds=_bounds(bars, s, is_end, start, exact_start=exact),
        ppy=ppy,
        kill_switch=kill_switch,
        costs_mode=costs_mode,
        label=label,
        meta={"data_source": data_src, "kill_threshold": r["kill_switch_drawdown"]},
        entry_from=entry_from,
    )
