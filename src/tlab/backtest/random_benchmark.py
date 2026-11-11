"""Benchmark de entradas al azar: ¿la estrategia le gana a un mono con las mismas reglas?

Se generan N estrategias aleatorias (semilla fija) que se parecen a la real en todo MENOS en
cuándo entran:

- **Señales** (portfolio_sim): mismo universo, mismo nº de operaciones por activo, duraciones
  sacadas de las de la estrategia real, mismo stop (el ``stop_price`` que la estrategia daría
  ese día), mismo sizing al 1 %, mismos costes, máx. posiciones y kill switch.
- **Pesos mensuales** (allocation_sim): mismas asignaciones (los mismos "estados" de cartera),
  mismo nº de cambios (rotación) y mismos meses en cada estado; solo cambia el orden y la
  longitud de los tramos.

Si la estrategia real no queda claramente por encima de la mayoría de los monos, su ventaja
no se distingue del azar. p-valor empírico = (1 + nº de azar ≥ real) / (N + 1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from tlab.backtest.targets import (
    METRICS,
    RunOutput,
    Target,
    check_period,
    extract_metrics,
    holding_bars,
)
from tlab.indicators import atr

DEFAULT_N = 1000
DEFAULT_SEED = 42
KEEP_PATHS = 200
COMPARE = ("sharpe", "cagr", "max_dd", "mar", "expectancy_r")


# ---------------------------------------------------------------------- señales al azar


def _composition(total: int, parts: int, rng: np.random.Generator, min_part: int = 0) -> np.ndarray:
    """Reparte ``total`` en ``parts`` trozos >= min_part al azar (uniforme sobre composiciones)."""
    if parts <= 0:
        return np.array([], dtype=int)
    free = total - parts * min_part
    if free < 0:
        raise ValueError("no cabe")
    cuts = np.sort(rng.integers(0, free + 1, size=parts - 1)) if parts > 1 else np.array([], int)
    return np.diff(np.r_[0, cuts, free]).astype(int) + min_part


def random_intervals(
    n_bars: int, durations: np.ndarray, rng: np.random.Generator
) -> list[tuple[int, int]]:
    """Coloca operaciones sin solaparse: devuelve (vela de señal de entrada, vela de señal de
    salida). Entrada ejecutada en p+1 y salida en p+h+1 → dura h velas. Si no caben todas,
    se descartan las últimas (se avisa por el recuento)."""
    h = np.maximum(np.asarray(durations, dtype=int), 1)
    rng.shuffle(h)
    usable = n_bars - 1  # señales en 0..n-2 para que la salida se ejecute dentro
    while len(h) and (h + 1).sum() > usable:
        h = h[:-1]
    if not len(h):
        return []
    gaps = _composition(usable - int((h + 1).sum()), len(h) + 1, rng)
    out, cur = [], 0
    for g, d in zip(gaps[:-1], h, strict=True):
        cur += int(g)
        out.append((cur, cur + int(d)))
        cur += int(d) + 1
    return out


def _fallback_stop(bars: pd.DataFrame, params: dict) -> pd.Series:
    k = float(params.get("atr_mult", 2.0))
    return bars["close"] - k * atr(bars, int(params.get("atr_n", 20)))


@dataclass
class SignalProfile:
    """Lo que se copia de la estrategia real para construir los monos."""

    counts: dict[str, int]
    durations: dict[str, np.ndarray]
    stops: dict[str, pd.Series]
    bars: dict[str, pd.DataFrame]


def signal_profile(target: Target, real: RunOutput, period: str) -> SignalProfile:
    bb = target.sliced_bars(period)
    tr = real.trades
    sig = target.signals(target.params)
    hb_all = holding_bars(tr, bb)
    reasons = tr["exit_reason"].to_numpy() if len(tr) else np.array([])
    counts, durs, stops = {}, {}, {}
    for s, df in bb.items():
        m = (tr["symbol"] == s).to_numpy() if len(tr) else np.array([], bool)
        counts[s] = int(m.sum())
        # Duraciones planeadas: las de salidas NO por stop (el stop ya actúa solo en el mono).
        cand = hb_all[m & ~np.isin(reasons, ["stop", "stop_gap", "kill_switch"])]
        if len(cand) < 5:
            cand = hb_all[m]
        if len(cand) < 5:
            nostop = hb_all[~np.isin(reasons, ["stop", "stop_gap", "kill_switch"])]
            cand = nostop if len(nostop) >= 5 else hb_all
        durs[s] = np.maximum(cand, 1) if len(cand) else np.array([5.0])
        st = sig[s]["stop_price"].reindex(df.index)
        fb = _fallback_stop(target.bars[s], target.params).reindex(df.index)
        stops[s] = st.where(np.isfinite(st) & (st < df["close"]), fb)
    return SignalProfile(counts, durs, stops, bb)


def random_signals(
    profile: SignalProfile, rng: np.random.Generator, scale: float = 1.0
) -> dict[str, pd.DataFrame]:
    """Un mono: señales de entrada/salida al azar con el mismo nº y duración de operaciones.

    ``scale`` alarga las duraciones planeadas (calibración: el stop corta antes a los monos)."""
    out = {}
    for s, df in profile.bars.items():
        n = len(df)
        k = profile.counts[s]
        sig = pd.DataFrame(
            {
                "entry": False,
                "exit": False,
                "stop_price": profile.stops[s].to_numpy(),
                "rank": rng.random(n),
            },
            index=df.index,
        )
        if k:
            d = np.round(rng.choice(profile.durations[s], size=k, replace=True) * scale)
            ent = np.zeros(n, bool)
            ex = np.zeros(n, bool)
            for p, q in random_intervals(n, d, rng):
                ent[p], ex[q] = True, True
            sig["entry"], sig["exit"] = ent, ex
        out[s] = sig
    return out


# ---------------------------------------------------------------------- pesos al azar


def _runs(w: pd.DataFrame) -> list[tuple[tuple, int]]:
    """Tramos de meses consecutivos con la misma asignación: [(estado, nº de meses)]."""
    states = [tuple(np.round(r, 10)) for r in w.fillna(0.0).to_numpy()]
    runs: list[tuple[tuple, int]] = []
    for st in states:
        if runs and runs[-1][0] == st:
            runs[-1] = (st, runs[-1][1] + 1)
        else:
            runs.append((st, 1))
    return runs


def _arrange(counts: dict, rng: np.random.Generator, tries: int = 500) -> list | None:
    """Secuencia al azar con ``counts[estado]`` apariciones y sin dos iguales seguidos."""
    for _ in range(tries):
        left = dict(counts)
        seq: list = []
        ok = True
        for _ in range(sum(counts.values())):
            opts = [s for s, c in left.items() if c > 0 and (not seq or s != seq[-1])]
            if not opts:
                ok = False
                break
            # El estado con más tramos pendientes manda (si no, se bloquea al final).
            total = sum(left.values())
            must = [s for s in opts if left[s] > (total - left[s]) and left[s] > 0]
            pool = must or opts
            wts = np.array([left[s] for s in pool], float)
            s = pool[int(rng.choice(len(pool), p=wts / wts.sum()))]
            seq.append(s)
            left[s] -= 1
        if ok:
            return seq
    return None


def random_weights(w: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Mismos estados, mismos meses por estado y mismo nº de cambios; orden y tramos al azar."""
    runs = _runs(w)
    if len(runs) <= 1:
        return w.copy()
    counts: dict = {}
    months: dict = {}
    for st, n in runs:
        counts[st] = counts.get(st, 0) + 1
        months[st] = months.get(st, 0) + n
    seq = _arrange(counts, rng) or [st for st, _ in runs]
    lens = {
        st: list(rng.permutation(_composition(months[st], counts[st], rng, 1))) for st in counts
    }
    rows = []
    for st in seq:
        rows += [st] * int(lens[st].pop())
    return pd.DataFrame(rows, index=w.index, columns=w.columns, dtype=float)


def turnover_changes(w: pd.DataFrame) -> int:
    return len(_runs(w)) - 1


# ---------------------------------------------------------------------- ejecución


@dataclass
class RandomResult:
    target: Target
    period: str
    n: int
    seed: int
    real: dict
    real_equity: pd.Series
    table: pd.DataFrame  # una fila por mono
    paths: pd.DataFrame  # equity de los primeros KEEP_PATHS monos (columnas = nº de mono)
    match: dict = field(default_factory=dict)

    def percentile(self, metric: str) -> float:
        """% de monos con valor <= que el real (alto = el real está arriba)."""
        x = self.table[metric].to_numpy(float)
        x = x[np.isfinite(x)]
        r = self.real.get(metric, np.nan)
        return float((x <= r).mean()) if len(x) and np.isfinite(r) else float("nan")

    def p_value(self, metric: str) -> float:
        return empirical_p(self.table[metric].to_numpy(float), self.real.get(metric, np.nan))


def empirical_p(randoms: np.ndarray, real: float) -> float:
    """p-valor de una cola (mayor = mejor): (1 + nº azar >= real) / (N + 1)."""
    x = np.asarray(randoms, float)
    x = x[np.isfinite(x)]
    if not len(x) or not np.isfinite(real):
        return float("nan")
    return float((1 + (x >= real).sum()) / (len(x) + 1))


def p_verdict(p: float) -> str:
    if not np.isfinite(p):
        return "sin dato"
    if p < 0.05:
        return "ventaja probable"
    if p < 0.10:
        return "indicio débil (no concluyente)"
    return "indistinguible del azar"


def _one(target: Target, period: str, seed: int, i: int, prof, w_real, keep: bool, scale=1.0):
    rng = np.random.default_rng(np.random.SeedSequence([seed, i]))
    if target.kind == "signals":
        run = target.run_with_signals(random_signals(prof, rng, scale), period)
        m = extract_metrics(run, target.ppy, prof.bars)
    else:
        wr = random_weights(w_real, rng)
        run = target.run_with_weights(wr, period)
        m = extract_metrics(run, target.ppy)
        m["changes"] = turnover_changes(wr)
    return i, m, (run.equity if keep else None)


def _chunk(target, period, seed, ids, prof, w_real, keep_n, scale=1.0):
    return [_one(target, period, seed, i, prof, w_real, i < keep_n, scale) for i in ids]


def calibrate_scale(
    target: Target,
    period: str,
    seed: int,
    prof: SignalProfile,
    real_hold: float,
    pilots: int = 24,
    rounds: int = 3,
    n_jobs: int = 1,
) -> tuple[float, list[float]]:
    """Busca el factor de duración con el que la duración media REAL de los monos (tras
    stops) se parece a la de la estrategia. Usa monos piloto con otra semilla."""
    from joblib import Parallel, delayed

    scale, hist = 1.0, []
    for k in range(rounds):
        ids = list(range(pilots))
        pseed = seed + 10_007 * (k + 1)
        if n_jobs == 1:
            outs = [_chunk(target, period, pseed, ids, prof, None, 0, scale)]
        else:
            outs = Parallel(n_jobs=n_jobs, backend="loky")(
                delayed(_chunk)(target, period, pseed, ids[j::n_jobs], prof, None, 0, scale)
                for j in range(n_jobs)
            )
        holds = [m["avg_hold"] for out in outs for _, m, _ in out if np.isfinite(m["avg_hold"])]
        got = float(np.mean(holds)) if holds else float("nan")
        hist.append(got)
        if not np.isfinite(got) or got <= 0 or abs(got / real_hold - 1) < 0.03:
            break
        scale = float(np.clip(scale * real_hold / got, 1.0, 4.0))
    return scale, hist


def run_random_benchmark(
    target: Target,
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
    period: str = "is",
    *,
    confirm_oos: bool = False,
    n_jobs: int = -1,
    keep_paths: int = KEEP_PATHS,
    calibrate: bool = True,
    progress: bool = False,
) -> RandomResult:
    """Corre la estrategia real y ``n`` monos con la misma semilla → resultados reproducibles
    (cada mono usa su propia sub-semilla, así que da igual cuántos procesos se usen)."""
    check_period(period, confirm_oos)
    real = target.run(target.params, period)
    if target.kind == "signals":
        if real.trades.empty:
            raise ValueError("la estrategia real no tiene operaciones en este periodo")
        prof, w_real = signal_profile(target, real, period), None
        real_m = extract_metrics(real, target.ppy, prof.bars)
    else:
        prof, w_real = None, real.weights
        real_m = extract_metrics(real, target.ppy)
        real_m["changes"] = turnover_changes(w_real)
    ids = list(range(n))
    from joblib import Parallel, delayed, effective_n_jobs

    nj = max(1, min(effective_n_jobs(n_jobs), max(1, n // 20)))
    scale, calib = 1.0, []
    if target.kind == "signals" and calibrate and np.isfinite(real_m.get("avg_hold", np.nan)):
        scale, calib = calibrate_scale(target, period, seed, prof, real_m["avg_hold"], n_jobs=nj)
    if nj == 1:
        outs = [_chunk(target, period, seed, ids, prof, w_real, keep_paths, scale)]
    else:
        parts = [ids[i::nj] for i in range(nj)]
        outs = Parallel(n_jobs=nj, backend="loky", verbose=5 if progress else 0)(
            delayed(_chunk)(target, period, seed, p, prof, w_real, keep_paths, scale) for p in parts
        )
    rows, paths = {}, {}
    for out in outs:
        for i, m, eq in out:
            rows[i] = m
            if eq is not None:
                paths[i] = eq
    table = pd.DataFrame([rows[i] for i in ids])
    for c in METRICS:
        if c in table:
            table[c] = pd.to_numeric(table[c], errors="coerce")
    pmat = pd.DataFrame({i: paths[i] for i in sorted(paths)}) if paths else pd.DataFrame()
    res = RandomResult(target, period, n, seed, real_m, real.equity, table, pmat)
    res.match = match_report(res)
    res.match["_calibracion"] = {"factor_duracion": scale, "pilotos_duracion_media": calib}
    return res


def match_report(res: RandomResult) -> dict:
    """¿Se parecen los monos a la real en lo que debían parecerse?"""
    t, r = res.table, res.real
    keys = ["trades", "avg_hold", "exposure"] + (["changes"] if "changes" in t else [])
    out = {}
    for k in keys:
        if k in t and np.isfinite(r.get(k, np.nan)):
            out[k] = {
                "real": float(r[k]),
                "azar_media": float(t[k].mean()),
                "azar_p5": float(t[k].quantile(0.05)),
                "azar_p95": float(t[k].quantile(0.95)),
            }
    return out


def summary_table(res: RandomResult) -> pd.DataFrame:
    rows = []
    for k in COMPARE:
        if k not in res.table or not np.isfinite(res.real.get(k, np.nan)):
            continue
        x = res.table[k].dropna()
        if not len(x):
            continue
        rows.append(
            {
                "metrica": k,
                "real": res.real[k],
                "azar_p5": x.quantile(0.05),
                "azar_mediana": x.median(),
                "azar_p95": x.quantile(0.95),
                "percentil_real": res.percentile(k),
                "p_valor": res.p_value(k),
                "veredicto": p_verdict(res.p_value(k)),
            }
        )
    return pd.DataFrame(rows)
