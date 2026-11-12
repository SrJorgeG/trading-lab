"""Monte Carlo de robustez: ¿el backtest histórico fue un camino afortunado?

Tres métodos (vectorizados, con semilla):

* ``shuffle``: baraja el orden de las operaciones cerradas (P&L fijo en $).
  La suma (y por tanto el equity final y el CAGR) no cambia; sí cambia la
  trayectoria y el drawdown.
* ``bootstrap``: reescribe la lista de operaciones *con reemplazo*.
  Cambia también el equity final y el CAGR.
* ``block``: remuestrea *bloques* de rentabilidades diarias (adecuado para
  estrategias mensuales sin operaciones cerradas con P&L).

Las simulaciones **no paran** al tocar el kill switch: se deja seguir el
camino para medir la distribución completa, y se informa de la probabilidad
de haberlo tocado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

METHODS = ("shuffle", "bootstrap", "block")
BANDS = (5, 25, 50, 75, 95)
DEFAULT_N = 5_000
DEFAULT_SEED = 42
DEFAULT_BLOCK = 21
DEFAULT_KILL = 0.15
DEFAULT_RUIN = 0.20

Method = Literal["shuffle", "bootstrap", "block"]
Sizing = Literal["additive", "compound"]


@dataclass
class MCConfig:
    n: int = DEFAULT_N
    seed: int = DEFAULT_SEED
    method: Method = "shuffle"
    block_length: int = DEFAULT_BLOCK
    kill_switch: float = DEFAULT_KILL
    ruin_threshold: float = DEFAULT_RUIN
    sizing: Sizing = "additive"
    risk_frac: float = 0.01
    n_sample_paths: int = 60
    keep_paths: bool = False  # guarda la matriz N×T completa (vistas 3D)


@dataclass
class MCResult:
    """Resultado de una tanda de simulaciones (no guarda las  N trayectorias)."""

    method: str
    n: int
    seed: int
    block_length: int | None
    sizing: str
    years: float
    initial_equity: float
    index: pd.Index
    bands: pd.DataFrame
    sample_paths: np.ndarray
    real_path: pd.Series
    mtm_equity: pd.Series | None
    max_dd: np.ndarray
    cagr: np.ndarray
    final_equity: np.ndarray
    max_dd_days: np.ndarray
    hit_kill: np.ndarray
    ended_below_start: np.ndarray
    hit_ruin: np.ndarray
    real: dict[str, float]
    mtm: dict[str, float] = field(default_factory=dict)
    ranks: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    paths: np.ndarray | None = None

    @property
    def p_kill(self) -> float:
        return float(self.hit_kill.mean())

    @property
    def p_below_start(self) -> float:
        return float(self.ended_below_start.mean())

    @property
    def p_ruin(self) -> float:
        return float(self.hit_ruin.mean())


def load_run(folder) -> tuple[pd.Series, pd.DataFrame | None, dict]:
    """Lee ``equity.csv`` y, si existe, ``trades.csv`` de una carpeta de informe."""
    folder = Path(folder)
    eq_path = folder / "equity.csv"
    if not eq_path.exists():
        raise FileNotFoundError(f"No hay equity.csv en {folder}")
    raw = pd.read_csv(eq_path, index_col=0)
    equity = raw.iloc[:, 0].copy()
    equity.index = pd.to_datetime(equity.index, utc=True)
    equity.name = "equity"
    trades = None
    tp = folder / "trades.csv"
    if tp.exists():
        trades = pd.read_csv(tp)
    meta = {"folder": folder, "title": folder.name}
    rp = folder / "resumen.md"
    if rp.exists():
        for line in rp.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                meta["title"] = line[2:].strip()
                break
    return equity, trades, meta


def closed_trades(trades: pd.DataFrame | None) -> pd.DataFrame:
    """Filtra a operaciones cerradas con ``pnl_usd`` (las de portfolio_sim)."""
    if trades is None or trades.empty:
        return pd.DataFrame()
    if "pnl_usd" not in trades.columns:
        return pd.DataFrame()
    out = trades.dropna(subset=["pnl_usd"]).copy()
    if "exit_date" in out.columns:
        out["exit_date"] = pd.to_datetime(out["exit_date"], utc=True)
        out = out.sort_values("exit_date")
    return out.reset_index(drop=True)


def _trade_increments(trades: pd.DataFrame, cfg: MCConfig) -> np.ndarray:
    if cfg.sizing == "compound":
        if "pnl_r" not in trades.columns or trades["pnl_r"].isna().all():
            raise ValueError("sizing=compound exige la columna pnl_r")
        return 1.0 + cfg.risk_frac * trades["pnl_r"].to_numpy(dtype=float)
    return trades["pnl_usd"].to_numpy(dtype=float)


def _apply_increments(increments: np.ndarray, initial: float, sizing: str) -> np.ndarray:
    """increments: (n_sims, n_trades) → equity incluyendo el punto inicial (n_sims, n+1)."""
    if sizing == "compound":
        eq = initial * np.cumprod(increments, axis=1)
    else:
        eq = initial + np.cumsum(increments, axis=1)
    start = np.full((increments.shape[0], 1), initial, dtype=float)
    return np.concatenate([start, eq], axis=1)


def _shuffle_or_bootstrap(values: np.ndarray, n: int, seed: int, replace: bool) -> np.ndarray:
    """Devuelve una matriz (n, len(values)) con permutaciones o remuestras."""
    rng = np.random.default_rng(seed)
    k = len(values)
    if k == 0:
        raise ValueError("No hay operaciones para barajar o remuestrear")
    if replace:
        idx = rng.integers(0, k, size=(n, k), endpoint=False)
        return values[idx]
    keys = rng.random((n, k))
    return values[np.argsort(keys, axis=1)]


def block_bootstrap_returns(returns: np.ndarray, n: int, block: int, seed: int) -> np.ndarray:
    """Remuestra bloques contiguos (sin envolver). Devuelve (n, T)."""
    t = len(returns)
    if t == 0:
        raise ValueError("No hay rentabilidades diarias")
    if block < 1:
        raise ValueError("block_length tiene que ser >= 1")
    if block > t:
        raise ValueError(f"block_length ({block}) no puede ser mayor que el nº de días ({t})")
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(t / block))
    max_start = t - block + 1
    starts = rng.integers(0, max_start, size=(n, n_blocks), endpoint=False)
    offsets = np.arange(block)
    idx = starts[..., None] + offsets
    boot = returns[idx].reshape(n, n_blocks * block)[:, :t]
    return boot


def _max_dd(eq: np.ndarray) -> np.ndarray:
    """Drawdown máximo (negativo) por fila."""
    peak = np.maximum.accumulate(eq, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        dd = eq / peak - 1.0
    return np.nanmin(dd, axis=1)


def _hit_threshold(eq: np.ndarray, frac: float, *, from_peak: bool) -> np.ndarray:
    """True si en algún momento se cae más de ``frac``.

    ``from_peak=True`` compara con el máximo (kill switch);
    ``from_peak=False`` compara con el equity inicial (ruina).
    """
    if from_peak:
        peak = np.maximum.accumulate(eq, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            dd = 1.0 - eq / peak
        return np.nanmax(dd, axis=1) > frac
    return np.nanmin(eq, axis=1) <= eq[:, 0] * (1.0 - frac)


def _max_dd_days(eq: np.ndarray, index: pd.Index) -> np.ndarray:
    """Mayor tiempo bajo el agua, en días naturales (0 si el índice no es de fechas)."""
    n, t = eq.shape
    if t == 0:
        return np.zeros(n, dtype=int)
    if isinstance(index, pd.DatetimeIndex) and len(index) == t:
        days = (index - index[0]).days.to_numpy(dtype=np.int64)
    else:
        days = np.arange(t, dtype=np.int64)
    peak = np.maximum.accumulate(eq, axis=1)
    under = eq < peak
    padded = np.pad(under.astype(np.int8), ((0, 0), (1, 1)), constant_values=0)
    diff = np.diff(padded, axis=1)
    starts = np.argwhere(diff == 1)
    ends = np.argwhere(diff == -1)
    out = np.zeros(n, dtype=np.int64)
    if len(starts) == 0:
        return out
    if len(starts) != len(ends):
        raise RuntimeError("inicios y finales de drawdown no emparejan")
    s_row, s_col = starts[:, 0], starts[:, 1]
    e_col = ends[:, 1]
    # e_col es la barra de recuperación (primera no-bajo-el-agua). Si el
    # camino termina aún bajo el agua, e_col == T y usamos el último índice,
    # como metrics.max_dd_duration_days.
    rec_days = days[np.minimum(e_col, t - 1)]
    dur = rec_days - days[s_col]
    np.maximum.at(out, s_row, dur)
    return out


def _cagr(final: np.ndarray, initial: float, years: float) -> np.ndarray:
    if years <= 0:
        return np.full_like(final, np.nan, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.clip(final / initial, 1e-12, None)
        return ratio ** (1.0 / years) - 1.0


def _years_from_index(index: pd.Index) -> float:
    if len(index) < 2:
        return 0.0
    a, b = index[0], index[-1]
    if isinstance(index, pd.DatetimeIndex) or (
        hasattr(a, "to_pydatetime") and hasattr(b, "to_pydatetime")
    ):
        return (pd.Timestamp(b) - pd.Timestamp(a)).days / 365.25
    return float(len(index) - 1) / 365.25


def _percentile_rank(samples: np.ndarray, value: float) -> float:
    """Porcentaje de simulaciones con valor <= al observado (0–100)."""
    s = samples[np.isfinite(samples)]
    if len(s) == 0 or not np.isfinite(value):
        return float("nan")
    # Si todas las sims coinciden (p. ej. equity final al barajar), el rango no aporta.
    if float(s.std(ddof=0)) < 1e-12 * max(1.0, abs(float(s.mean()))):
        return 50.0
    return float((s <= value).mean() * 100.0)


def _real_trade_path(
    trades: pd.DataFrame, initial: float, cfg: MCConfig
) -> tuple[np.ndarray, pd.Index]:
    inc = _trade_increments(trades, cfg).reshape(1, -1)
    eq = _apply_increments(inc, initial, cfg.sizing)[0]
    if "exit_date" in trades.columns:
        start = pd.Timestamp(trades["exit_date"].iloc[0])
        if "entry_date" in trades.columns:
            start = min(start, pd.Timestamp(pd.to_datetime(trades["entry_date"].iloc[0], utc=True)))
        idx = pd.DatetimeIndex([start, *pd.to_datetime(trades["exit_date"], utc=True)])
    else:
        idx = pd.RangeIndex(len(eq), name="trade")
    return eq, idx


def run_montecarlo(
    equity: pd.Series,
    trades: pd.DataFrame | None = None,
    cfg: MCConfig | None = None,
) -> MCResult:
    """Lanza N simulaciones sobre un backtest (curva de equity y/o operaciones)."""
    cfg = cfg or MCConfig()
    if cfg.method not in METHODS:
        raise ValueError(f"método desconocido: {cfg.method}")
    if cfg.n < 1:
        raise ValueError("n tiene que ser >= 1")
    equity = equity.astype(float).dropna()
    if equity.empty:
        raise ValueError("la curva de equity está vacía")
    initial = float(equity.iloc[0])
    closed = closed_trades(trades)
    notes: list[str] = []

    if cfg.method in ("shuffle", "bootstrap"):
        if closed.empty:
            raise ValueError(
                f"El método {cfg.method} necesita operaciones cerradas con pnl_usd. "
                "Para estrategias mensuales (Faber, TSMOM, …) usa --method block."
            )
        values = _trade_increments(closed, cfg)
        sampled = _shuffle_or_bootstrap(
            values, cfg.n, cfg.seed, replace=(cfg.method == "bootstrap")
        )
        paths = _apply_increments(sampled, initial, cfg.sizing)
        real_eq, idx = _real_trade_path(closed, initial, cfg)
        if cfg.sizing == "additive":
            notes.append(
                "Se baraja el P&L en dólares de cada operación ya cerrada "
                "(tamaño fijo, no se recompone el 1 % sobre el equity del momento)."
            )
        else:
            notes.append(
                f"Se barajan los múltiplos R y se capitaliza con fracción fija "
                f"({cfg.risk_frac:.2%} por operación)."
            )
        notes.append(
            "La trayectoria solo se actualiza al cerrar cada operación: no captura "
            "el drawdown intradía ni el de posiciones aún abiertas."
        )
        if cfg.method == "shuffle":
            notes.append(
                "Al barajar sin reemplazo, la suma de P&L (sizing aditivo) y el "
                "producto de factores (sizing compuesto) no cambian: el equity "
                "final y el CAGR son idénticos en todas las simulaciones. Solo "
                "cambia el camino y el drawdown."
            )
    else:
        rets = equity.pct_change().to_numpy()[1:]
        boot = block_bootstrap_returns(rets, cfg.n, cfg.block_length, cfg.seed)
        paths = initial * np.cumprod(1.0 + boot, axis=1)
        start = np.full((cfg.n, 1), initial, dtype=float)
        paths = np.concatenate([start, paths], axis=1)
        idx = equity.index
        real_eq = equity.to_numpy(dtype=float)
        notes.append(
            f"Remuestreo por bloques de {cfg.block_length} rentabilidades diarias "
            "(conserva un poco la autocorrelación; asume que los bloques son intercambiables)."
        )

    # El CAGR se anualiza con el periodo de la curva de equity original,
    # para que sea comparable con el informe del backtest.
    years = _years_from_index(equity.index)

    # Métricas por simulación
    final = paths[:, -1]
    max_dd = _max_dd(paths)
    cagr = _cagr(final, initial, years)
    dd_days = _max_dd_days(paths, idx)
    hit_kill = _hit_threshold(paths, cfg.kill_switch, from_peak=True)
    hit_ruin = _hit_threshold(paths, cfg.ruin_threshold, from_peak=False)
    below = final < initial

    # Bandas y muestra de caminos (para no guardar 5000 × T)
    qs = np.percentile(paths, BANDS, axis=0)
    bands = pd.DataFrame(
        {f"p{b}": qs[i] for i, b in enumerate(BANDS)},
        index=idx,
    )
    rng = np.random.default_rng(cfg.seed)
    k = min(cfg.n_sample_paths, cfg.n)
    sample_idx = (
        np.sort(rng.choice(cfg.n, size=k, replace=False)) if cfg.n else np.array([], dtype=int)
    )
    sample = paths[sample_idx]

    real_path = pd.Series(real_eq, index=idx, name="real")
    real_metrics = {
        "final_equity": float(real_eq[-1]),
        "cagr": float(_cagr(np.array([real_eq[-1]]), initial, years)[0]),
        "max_dd": float(_max_dd(real_eq.reshape(1, -1))[0]),
        "max_dd_days": int(_max_dd_days(real_eq.reshape(1, -1), idx)[0]),
        "hit_kill": bool(
            _hit_threshold(real_eq.reshape(1, -1), cfg.kill_switch, from_peak=True)[0]
        ),
        "hit_ruin": bool(
            _hit_threshold(real_eq.reshape(1, -1), cfg.ruin_threshold, from_peak=False)[0]
        ),
        "below_start": bool(real_eq[-1] < initial),
    }
    mtm: dict[str, float] = {}
    mtm_eq: pd.Series | None = None
    if cfg.method in ("shuffle", "bootstrap"):
        mtm_eq = equity
        mtm_years = _years_from_index(equity.index)
        mtm = {
            "final_equity": float(equity.iloc[-1]),
            "cagr": float(_cagr(np.array([float(equity.iloc[-1])]), initial, mtm_years)[0]),
            "max_dd": float(_max_dd(equity.to_numpy().reshape(1, -1))[0]),
            "max_dd_days": int(_max_dd_days(equity.to_numpy().reshape(1, -1), equity.index)[0]),
        }
        notes.append(
            "El drawdown «a mercado» del backtest (marcado cada día, con posiciones abiertas) "
            "puede ser peor que el de la trayectoria de P&L realizado que se compara con las "
            "simulaciones."
        )

    ranks = {
        "final_equity": _percentile_rank(final, real_metrics["final_equity"]),
        "cagr": _percentile_rank(cagr, real_metrics["cagr"]),
        "max_dd": _percentile_rank(max_dd, real_metrics["max_dd"]),
        "max_dd_days": _percentile_rank(dd_days, real_metrics["max_dd_days"]),
    }

    return MCResult(
        method=cfg.method,
        n=cfg.n,
        seed=cfg.seed,
        block_length=cfg.block_length if cfg.method == "block" else None,
        sizing=cfg.sizing,
        years=years,
        initial_equity=initial,
        index=idx,
        bands=bands,
        sample_paths=sample,
        real_path=real_path,
        mtm_equity=mtm_eq,
        max_dd=max_dd,
        cagr=cagr,
        final_equity=final,
        max_dd_days=dd_days,
        hit_kill=hit_kill,
        ended_below_start=below,
        hit_ruin=hit_ruin,
        real=real_metrics,
        mtm=mtm,
        ranks=ranks,
        notes=notes,
        paths=paths if cfg.keep_paths else None,
    )


def stats_table(result: MCResult) -> pd.DataFrame:
    """Tabla de percentiles + rango del valor real, una fila por métrica."""
    rows = []

    def add(name, samples, real, kind):
        s = samples[np.isfinite(samples)]
        q = np.percentile(s, BANDS) if len(s) else [np.nan] * len(BANDS)
        rows.append(
            {
                "metric": name,
                "kind": kind,
                "real": real,
                "p5": q[0],
                "p25": q[1],
                "p50": q[2],
                "p75": q[3],
                "p95": q[4],
                "mean": float(s.mean()) if len(s) else np.nan,
                "std": float(s.std(ddof=1)) if len(s) > 1 else np.nan,
                "percentile_rank": result.ranks.get(name, np.nan),
            }
        )

    add("final_equity", result.final_equity, result.real["final_equity"], "usd")
    add("cagr", result.cagr, result.real["cagr"], "pct")
    add("max_dd", result.max_dd, result.real["max_dd"], "pct")
    add("max_dd_days", result.max_dd_days.astype(float), result.real["max_dd_days"], "days")
    rows.append(
        {
            "metric": "p_kill_switch",
            "kind": "prob",
            "real": float(result.real["hit_kill"]),
            "p5": np.nan,
            "p25": np.nan,
            "p50": result.p_kill,
            "p75": np.nan,
            "p95": np.nan,
            "mean": result.p_kill,
            "std": np.nan,
            "percentile_rank": np.nan,
        }
    )
    rows.append(
        {
            "metric": "p_below_start",
            "kind": "prob",
            "real": float(result.real["below_start"]),
            "p5": np.nan,
            "p25": np.nan,
            "p50": result.p_below_start,
            "p75": np.nan,
            "p95": np.nan,
            "mean": result.p_below_start,
            "std": np.nan,
            "percentile_rank": np.nan,
        }
    )
    rows.append(
        {
            "metric": "p_ruin",
            "kind": "prob",
            "real": float(result.real["hit_ruin"]),
            "p5": np.nan,
            "p25": np.nan,
            "p50": result.p_ruin,
            "p75": np.nan,
            "p95": np.nan,
            "mean": result.p_ruin,
            "std": np.nan,
            "percentile_rank": np.nan,
        }
    )
    return pd.DataFrame(rows)


def luck_comment(result: MCResult) -> str:
    """Texto corto sobre si el camino histórico parece típico, afortunado o desafortunado."""
    if result.method == "shuffle" and result.sizing in ("additive", "compound"):
        cagr_note = (
            "El CAGR y el equity final no cambian al barajar, así que no sirven "
            "para hablar de suerte en el resultado final: mira el drawdown."
        )
        r = result.ranks.get("max_dd", float("nan"))
        if not np.isfinite(r):
            return cagr_note
        # max_dd es negativo: un rango alto significa que muchas sims fueron *peores*
        # (más negativas) o iguales → el histórico tuvo un DD relativamente suave.
        if r >= 95:
            return (
                cagr_note + f" El drawdown histórico es más suave que el de ~{r:.0f} % de las "
                "simulaciones: el camino real pudo ser afortunado en el orden de las "
                "operaciones."
            )
        if r <= 5:
            return (
                cagr_note + f" El drawdown histórico es de los peores (solo un {r:.0f} % de las "
                "simulaciones lo igualan o lo empeoran): el orden real fue exigente."
            )
        return (
            cagr_note + f" El drawdown histórico queda alrededor del percentil {r:.0f} de las "
            "simulaciones (ni extremo)."
        )

    rc, rd = result.ranks.get("cagr", float("nan")), result.ranks.get("max_dd", float("nan"))
    bits = []
    if np.isfinite(rc):
        if rc >= 95:
            bits.append(
                f"el CAGR histórico supera al de ~{rc:.0f} % de las simulaciones "
                "(cola buena: posible suerte en la muestra)"
            )
        elif rc <= 5:
            bits.append(
                f"el CAGR histórico queda por debajo del de ~{100 - rc:.0f} % de las "
                "simulaciones (camino exigente)"
            )
        else:
            bits.append(f"el CAGR histórico queda en el percentil {rc:.0f} (típico)")
    if np.isfinite(rd):
        if rd >= 95:
            bits.append(
                f"el drawdown fue más suave que en ~{rd:.0f} % de las simulaciones "
                "(también puede ser suerte en el orden/bloques)"
            )
        elif rd <= 5:
            bits.append("el drawdown histórico está en la cola mala de la distribución")
        else:
            bits.append(f"el drawdown queda en el percentil {rd:.0f}")
    if not bits:
        return "No se pudo comparar el backtest con la distribución."
    text = bits[0]
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    if len(bits) > 1:
        text += "; " + bits[1]
    return text + "."


def _fmt_pct(x) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x * 100:.1f} %"


def _fmt_usd(x) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x:,.0f} $".replace(",", ".")


def _fmt_num(x, nd=1) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    if nd == 0:
        return f"{int(round(x))}"
    return f"{x:.{nd}f}"


def _fmt_rank(x) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x:.0f}"


METHOD_ES = {
    "shuffle": "barajar el orden de las operaciones (sin reemplazo)",
    "bootstrap": "remuestrear operaciones con reemplazo",
    "block": "remuestrear bloques de rentabilidades diarias",
}


def write_resumen_md(
    result: MCResult,
    path,
    title: str,
    cfg: MCConfig,
    extra: str = "",
) -> None:
    """Informe en español, sin jerga innecesaria."""
    from tlab.report import now_madrid

    path = Path(path)
    st = stats_table(result)
    by = {r["metric"]: r for r in st.to_dict(orient="records")}

    def _fmt_days(x):
        return _fmt_num(x, 0)

    def row(metric, label, fmt):
        r = by[metric]
        f = {"pct": _fmt_pct, "usd": _fmt_usd}.get(fmt, _fmt_days)
        return (
            f"| {label} | {f(r['real'])} | {f(r['p5'])} | {f(r['p25'])} | "
            f"{f(r['p50'])} | {f(r['p75'])} | {f(r['p95'])} | "
            f"{_fmt_rank(r['percentile_rank'])} |"
        )

    eje = (
        "número de operación (el equity solo se actualiza al cerrar)"
        if result.method in ("shuffle", "bootstrap")
        else "días del calendario (misma longitud que el backtest)"
    )
    mtm_lines = []
    if result.mtm:
        mtm_lines = [
            "",
            "## Backtest original (marcado a mercado, cada día)",
            "",
            "Estas cifras sí incluyen el vaivén de las posiciones abiertas. "
            "No se comparan directamente con las bandas de arriba.",
            "",
            f"- Equity final: {_fmt_usd(result.mtm['final_equity'])}",
            f"- CAGR: {_fmt_pct(result.mtm['cagr'])}",
            f"- Máx. drawdown: {_fmt_pct(result.mtm['max_dd'])}",
            f"- Máx. días bajo el agua: {_fmt_num(result.mtm['max_dd_days'], 0)}",
        ]

    notes = "\n".join(f"- {n}" for n in result.notes)
    ruin_level = _fmt_usd(result.initial_equity * (1 - cfg.ruin_threshold))
    hit = "sí" if result.real["hit_kill"] else "no"
    ruin = "sí" if result.real["hit_ruin"] else "no"
    below = "sí" if result.real["below_start"] else "no"
    lines = [
        f"# Monte Carlo — {title}",
        "",
        f"Generado: {now_madrid()}",
        "",
        "## Qué se ha hecho",
        "",
        f"- Método: **{result.method}** ({METHOD_ES[result.method]}).",
        f"- Simulaciones: **{result.n}**, semilla **{result.seed}**.",
        (
            f"- Capital inicial: {_fmt_usd(result.initial_equity)}. "
            f"Periodo aproximado: {result.years:.2f} años."
        ),
        f"- Eje de las trayectorias: {eje}.",
        (
            "- Kill switch (parada de emergencia): caída **mayor** del "
            f"{cfg.kill_switch:.0%} desde el máximo."
        ),
        (
            f"- Umbral de ruina: el equity toca o baja de {ruin_level} "
            f"({cfg.ruin_threshold:.0%} de pérdida desde el inicio)."
        ),
        (
            "- Las simulaciones **no se detienen** al tocar el kill switch; "
            "se deja seguir el camino y se cuenta cuántas lo habrían tocado."
        ),
        "",
        "## Resultados",
        "",
        "| Métrica | Backtest (misma construcción) | p5 | p25 | "
        "p50 (mediana) | p75 | p95 | Rango del real (%) |",
        "|---|---|---|---|---|---|---|---|",
        row("final_equity", "Equity final", "usd"),
        row("cagr", "CAGR (crecimiento anualizado)", "pct"),
        row("max_dd", "Máx. drawdown", "pct"),
        row("max_dd_days", "Máx. días bajo el agua", "days"),
        "",
        "«Rango del real» es el porcentaje de simulaciones con un valor "
        "**menor o igual** al del backtest. En el CAGR, un rango alto "
        "significa que el histórico ganó más que la mayoría. En el "
        "drawdown (que es negativo), un rango alto significa que el "
        "histórico cayó *menos* que la mayoría (camino más suave).",
        "",
        "## Probabilidades",
        "",
        "| Pregunta | Probabilidad |",
        "|---|---|",
        (
            f"| ¿Tocar el kill switch (caída > {cfg.kill_switch:.0%} "
            f"desde el máximo)? | {_fmt_pct(result.p_kill)} |"
        ),
        (f"| ¿Terminar por debajo del capital inicial? | {_fmt_pct(result.p_below_start)} |"),
        (
            f"| ¿Tocar el umbral de ruina (pérdida ≥ {cfg.ruin_threshold:.0%} "
            f"desde el inicio)? | {_fmt_pct(result.p_ruin)} |"
        ),
        "",
        (
            "En el backtest (misma construcción que las sims): "
            f"kill switch = {hit}; ruina = {ruin}; "
            f"termina por debajo del inicio = {below}."
        ),
        "",
        "## ¿Fue suerte?",
        "",
        luck_comment(result),
        *mtm_lines,
        "",
        "## Cómo leer los gráficos",
        "",
        (
            "- **Abanico (fan chart):** las bandas sombreadas cubren el 90 % "
            "(p5–p95) y el 50 % (p25–p75) de los caminos simulados. La línea "
            f"gruesa es el backtest. Las líneas finas son una muestra, no las {result.n}."
        ),
        (
            "- **Histograma de drawdown:** la línea roja es el kill switch "
            f"({cfg.kill_switch:.0%}). Si mucha masa queda a la izquierda, la "
            "estrategia salta la parada de emergencia a menudo cuando se "
            "reordena el azar."
        ),
        (
            "- **Histograma de CAGR:** en el método ``shuffle`` suele ser una "
            "sola barra (el CAGR no cambia). En ``bootstrap`` y ``block`` "
            "sí hay distribución."
        ),
        "",
        "## Advertencias",
        "",
        notes,
        (
            "- Se asume que las operaciones (o los bloques de días) son "
            "intercambiables: en la realidad una racha de pérdidas puede "
            "tener causa común (un régimen de mercado), y barajarla las "
            "trata como independientes."
        ),
        (
            "- Un Monte Carlo no convierte un backtest en predicción. "
            "Sirve para ver si el camino que ya vimos era frágil al orden "
            "o a la muestra."
        ),
        extra,
        "",
    ]
    md = "\n".join(lines)

    path.write_text(md, encoding="utf-8")


def render_html(result: MCResult, path, title: str, cfg: MCConfig, *, offline: bool = True) -> None:
    """HTML interactivo autónomo (plotly). ``offline=False`` usa el CDN (más ligero)."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    path = Path(path)
    x_all = _x_values(result)
    keep = _downsample_idx(len(x_all))
    x = x_all[keep] if not isinstance(x_all, list) else [x_all[i] for i in keep]
    if isinstance(x_all, np.ndarray) and x_all.dtype == object:
        x = x_all[keep]
    bands = result.bands.iloc[keep]
    samples = result.sample_paths[:, keep]
    real = result.real_path.to_numpy()[keep]
    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=(
            "Abanico de trayectorias de equity",
            "Distribución del máx. drawdown (línea = kill switch)",
            "Distribución del CAGR",
        ),
        vertical_spacing=0.10,
        row_heights=[0.5, 0.25, 0.25],
    )
    fig.add_trace(
        go.Scatter(
            x=list(x) + list(x[::-1]),
            y=list(bands["p95"]) + list(bands["p5"][::-1]),
            fill="toself",
            fillcolor="rgba(31, 119, 180, 0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="p5–p95",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=list(x) + list(x[::-1]),
            y=list(bands["p75"]) + list(bands["p25"][::-1]),
            fill="toself",
            fillcolor="rgba(31, 119, 180, 0.30)",
            line=dict(color="rgba(0,0,0,0)"),
            name="p25–p75",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=bands["p50"],
            mode="lines",
            line=dict(color="rgb(31, 119, 180)", width=1, dash="dash"),
            name="mediana",
        ),
        row=1,
        col=1,
    )
    for i, row in enumerate(samples[:25]):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=row,
                mode="lines",
                line=dict(color="rgba(80,80,80,0.15)", width=0.7),
                name="muestra" if i == 0 else None,
                legendgroup="muestra",
                showlegend=(i == 0),
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=real,
            mode="lines",
            line=dict(color="rgb(214, 39, 40)", width=2.2),
            name="backtest",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Histogram(
            x=result.max_dd * 100,
            nbinsx=40,
            marker_color="rgb(31, 119, 180)",
            name="máx. DD",
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    fig.add_vline(
        x=-cfg.kill_switch * 100,
        line_color="rgb(214, 39, 40)",
        line_dash="dash",
        row=2,
        col=1,
        annotation_text="kill switch",
        annotation_position="top",
    )
    fig.add_vline(
        x=result.real["max_dd"] * 100,
        line_color="rgb(44, 160, 44)",
        line_dash="dot",
        row=2,
        col=1,
        annotation_text="backtest",
        annotation_position="top right",
    )

    fig.add_trace(
        go.Histogram(
            x=result.cagr * 100,
            nbinsx=40,
            marker_color="rgb(255, 127, 14)",
            name="CAGR",
            showlegend=False,
        ),
        row=3,
        col=1,
    )
    fig.add_vline(
        x=result.real["cagr"] * 100,
        line_color="rgb(44, 160, 44)",
        line_dash="dot",
        row=3,
        col=1,
        annotation_text="backtest",
        annotation_position="top right",
    )

    xlab = "nº de operación" if result.method in ("shuffle", "bootstrap") else "fecha"
    fig.update_xaxes(title_text=xlab, row=1, col=1)
    fig.update_yaxes(title_text="equity ($)", row=1, col=1)
    fig.update_xaxes(title_text="máx. drawdown (%)", row=2, col=1)
    fig.update_xaxes(title_text="CAGR (%)", row=3, col=1)
    fig.update_layout(
        title=f"Monte Carlo ({result.method}, n={result.n}, semilla={result.seed}) — {title}",
        template="plotly_white",
        height=980,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=60, r=30, t=80, b=50),
    )
    if offline:
        js_file = shared_plotly_js()
        try:
            js = str(js_file.resolve().relative_to(path.resolve().parent, walk_up=True))
        except TypeError:
            # pathlib sin walk_up (no debería pasar en 3.12, pero por si acaso)
            js = str(js_file)
        except ValueError:
            js = str(js_file)
    else:
        js = "cdn"
    path.write_text(
        fig.to_html(include_plotlyjs=js, full_html=True, config={"displaylogo": False}),
        encoding="utf-8",
    )


def render_png(result: MCResult, path, title: str, cfg: MCConfig) -> None:
    """Abanico + histogramas en PNG (matplotlib)."""
    import matplotlib.pyplot as plt

    path = Path(path)
    x = _x_values(result)
    bands = result.bands
    fig, axes = plt.subplots(3, 1, figsize=(10.5, 11), gridspec_kw={"height_ratios": [2, 1, 1]})
    ax = axes[0]
    ax.fill_between(x, bands["p5"], bands["p95"], color="#1f77b4", alpha=0.18, label="p5–p95")
    ax.fill_between(x, bands["p25"], bands["p75"], color="#1f77b4", alpha=0.35, label="p25–p75")
    ax.plot(x, bands["p50"], color="#1f77b4", ls="--", lw=1, label="mediana")
    for row in result.sample_paths:
        ax.plot(x, row, color="0.5", lw=0.4, alpha=0.25)
    ax.plot(x, result.real_path.to_numpy(), color="#d62728", lw=2, label="backtest")
    ax.set_ylabel("equity ($)")
    ax.set_xlabel("nº de operación" if result.method in ("shuffle", "bootstrap") else "fecha")
    ax.set_title(f"Monte Carlo ({result.method}, n={result.n}, semilla={result.seed}) — {title}")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.hist(result.max_dd * 100, bins=40, color="#1f77b4", alpha=0.85)
    ax.axvline(-cfg.kill_switch * 100, color="#d62728", ls="--", label="kill switch")
    ax.axvline(result.real["max_dd"] * 100, color="#2ca02c", ls=":", label="backtest")
    ax.set_xlabel("máx. drawdown (%)")
    ax.set_ylabel("simulaciones")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    ax.hist(result.cagr * 100, bins=40, color="#ff7f0e", alpha=0.85)
    ax.axvline(result.real["cagr"] * 100, color="#2ca02c", ls=":", label="backtest")
    ax.set_xlabel("CAGR (%)")
    ax.set_ylabel("simulaciones")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _x_values(result: MCResult):
    idx = result.index
    if result.method in ("shuffle", "bootstrap"):
        return np.arange(len(idx))
    if isinstance(idx, pd.DatetimeIndex):
        return idx.to_pydatetime()
    return np.arange(len(idx))


def _downsample_idx(n: int, max_points: int = 1_200) -> np.ndarray:
    """Índices para pintar sin hinchar el HTML (las métricas usan toda la serie)."""
    if n <= max_points:
        return np.arange(n)
    # Siempre incluye el primero y el último.
    step = (n - 1) / (max_points - 1)
    idx = np.unique(np.r_[0, np.round(np.arange(1, max_points - 1) * step).astype(int), n - 1])
    return idx


def shared_plotly_js() -> Path:
    """Copia única de plotly.min.js en reports/assets/ (para no repetir 3–4 MB)."""
    import plotly

    from tlab.config import ROOT

    dest = ROOT / "reports" / "assets" / "plotly.min.js"
    if not dest.exists() or dest.stat().st_size < 1_000:
        src = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
        if not src.exists():
            # Respaldo en instalaciones que lo traen en otro sitio.
            import plotly.offline as off

            src = Path(off.__file__).parent / "plotly.min.js"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
    return dest


def write_outputs(
    result: MCResult,
    out_dir,
    title: str,
    cfg: MCConfig,
    *,
    html: bool = True,
    png: bool = True,
    offline_html: bool = True,
) -> dict:
    """Escribe md, csv, html y png en ``out_dir``. Devuelve las rutas."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"montecarlo_{result.method}"
    paths = {
        "md": out_dir / f"{prefix}_resumen.md",
        "csv": out_dir / f"{prefix}_stats.csv",
    }
    stats_table(result).to_csv(paths["csv"], index=False)
    write_resumen_md(result, paths["md"], title, cfg)
    if html:
        paths["html"] = out_dir / f"{prefix}.html"
        try:
            render_html(result, paths["html"], title, cfg, offline=offline_html)
        except ImportError:
            paths.pop("html", None)
    if png:
        paths["png"] = out_dir / f"{prefix}_fan.png"
        try:
            render_png(result, paths["png"], title, cfg)
        except ImportError:
            paths.pop("png", None)
    return paths
