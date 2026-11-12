"""Mapa de sensibilidad de parámetros: ¿la estrategia vive en una MESETA o en un PICO?

Se prueba una rejilla de 1–3 parámetros con el motor real (mismos costes, slippage y reglas
duras que el veredicto) y se mide si el buen resultado aguanta al mover los parámetros:

- meseta (plateau): muchas combinaciones vecinas dan casi lo mismo → robusto;
- pico (spike): solo una combinación concreta sale bien → probable sobreajuste.

Anti-snooping: por defecto solo se usa el periodo in-sample; el OOS exige ``confirm_oos``.
Cada barrido se anota en ``docs/registro_pruebas.md`` con el nº de configuraciones probadas.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from tlab.backtest.overfit import deflated_sharpe, pbo_cscv, sharpe_per_period
from tlab.backtest.targets import METRICS, SCORABLE, Target, check_period, extract_metrics
from tlab.config import ROOT, load_settings

CACHE_VERSION = 2
DEFAULT_TOL = 0.20  # "casi igual" = dentro del 20 % del mejor
DEFAULT_CACHE = ROOT / "state" / "cache" / "param_sweep"

# Rejillas listas para usar (lo que se corrió en las baselines).
PRESETS: dict[str, dict] = {
    "donchian": {
        "strategy": "donchian_atr",
        "grid": ["entry_n=10:60:5", "exit_n=5:30:5", "atr_mult=1.5,2,2.5,3,3.5"],
        "kill_switch": False,
        "title": "Donchian (SPY, QQQ, BTC) sin kill switch",
    },
    "donchian2d": {
        "strategy": "donchian_atr",
        "grid": ["entry_n=10:60:5", "exit_n=5:30:5"],
        "kill_switch": False,
        "title": "Donchian (SPY, QQQ, BTC) sin kill switch",
    },
    "tsmom_spy": {
        "strategy": "tsmom_12m",
        "universe": ["SPY"],
        "grid": ["months=1:24", "skip=0:2"],
        "start": "2005-01-01",
        "title": "TSMOM (SPY): meses de lookback × meses saltados",
    },
    "faber_spy": {
        "strategy": "faber_sma10m",
        "universe": ["SPY"],
        "grid": ["months=2:20"],
        "start": "2005-01-01",
        "title": "Faber SMA (SPY): meses de la media",
    },
}


# ---------------------------------------------------------------------- rejilla


def _num(x: str):
    x = x.strip()
    return float(x) if any(c in x for c in ".eE") else int(x)


def parse_axis(spec: str, default=None) -> tuple[str, list]:
    """``nombre=a:b[:paso]`` (ambos incluidos) o ``nombre=v1,v2,...``."""
    if "=" not in spec:
        raise ValueError(f"eje mal escrito: {spec!r} (usa nombre=10:60:5 o nombre=1,2,3)")
    name, rhs = (s.strip() for s in spec.split("=", 1))
    if ":" in rhs:
        parts = [_num(p) for p in rhs.split(":")]
        if len(parts) not in (2, 3):
            raise ValueError(f"rango mal escrito: {spec!r}")
        a, b = parts[0], parts[1]
        step = parts[2] if len(parts) == 3 else 1
        if step <= 0 or b < a:
            raise ValueError(f"rango vacío o paso no positivo: {spec!r}")
        n = int(math.floor((b - a) / step + 1e-9)) + 1
        vals = [a + i * step for i in range(n)]
    else:
        vals = [_num(p) for p in rhs.split(",") if p.strip()]
    if isinstance(default, int) and all(float(v).is_integer() for v in vals):
        vals = [int(v) for v in vals]
    elif isinstance(default, float) or any(isinstance(v, float) for v in vals):
        vals = [round(float(v), 10) for v in vals]
    if len(set(vals)) != len(vals) or not vals:
        raise ValueError(f"valores repetidos o vacíos en {spec!r}")
    return name, vals


def build_grid(axes: dict[str, list], base: dict) -> list[dict]:
    """Producto cartesiano de los ejes sobre los parámetros base (orden C: último eje rápido)."""
    names = list(axes)
    return [
        {**base, **dict(zip(names, combo, strict=True))}
        for combo in itertools.product(*axes.values())
    ]


def grid_index(axes: dict[str, list], params: dict) -> tuple[int, ...] | None:
    """Posición de ``params`` en la rejilla (None si algún valor no está)."""
    out = []
    for k, vals in axes.items():
        v = params.get(k)
        hit = [i for i, x in enumerate(vals) if v is not None and np.isclose(float(x), float(v))]
        if not hit:
            return None
        out.append(hit[0])
    return tuple(out)


# ---------------------------------------------------------------------- evaluación + caché


def _key(target: Target, params: dict, period: str) -> str:
    d = {"v": CACHE_VERSION, "fp": target.fingerprint(), "p": params, "period": period}
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:24]


def evaluate(target: Target, params: dict, period: str) -> tuple[dict, pd.Series]:
    """Métricas + rentabilidades diarias de una configuración (NaN si es inválida)."""
    try:
        run = target.run(params, period)
    except ValueError as e:  # combinación imposible (p. ej. skip >= months)
        return {"error": str(e)}, pd.Series(dtype=float)
    m = extract_metrics(run, target.ppy, target.sliced_bars(period))
    return m, run.equity.pct_change().fillna(0.0)


def _eval_chunk(target: Target, items: list[tuple[str, dict]], period: str, cache_dir):
    out = []
    for key, params in items:
        m, r = evaluate(target, params, period)
        if cache_dir is not None:
            _cache_write(Path(cache_dir), key, m, r)
        out.append((key, m, r))
    return out


def _cache_write(cache_dir: Path, key: str, m: dict, r: pd.Series) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    tmp = cache_dir / f"{key}.tmp.npz"
    np.savez(
        tmp,
        metrics=np.array(json.dumps(m)),
        idx=r.index.as_unit("ns").asi8 if len(r) else np.array([], dtype="int64"),
        ret=r.to_numpy(dtype=float),
    )
    tmp.replace(cache_dir / f"{key}.npz")


def _cache_read(cache_dir: Path, key: str) -> tuple[dict, pd.Series] | None:
    p = cache_dir / f"{key}.npz"
    if not p.exists():
        return None
    try:
        z = np.load(p)
        m = json.loads(str(z["metrics"]))
        idx = pd.to_datetime(z["idx"], unit="ns", utc=True)
        return m, pd.Series(z["ret"], index=idx)
    except Exception:  # caché corrupta: se recalcula
        return None


@dataclass
class SweepResult:
    target: Target
    axes: dict[str, list]
    period: str
    table: pd.DataFrame  # una fila por configuración: ejes + métricas
    returns: pd.DataFrame  # T × N rentabilidades diarias (columnas = nº de fila de ``table``)
    default_idx: tuple[int, ...] | None
    n_cached: int = 0
    n_computed: int = 0
    meta: dict = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(len(v) for v in self.axes.values())

    @property
    def n_configs(self) -> int:
        return len(self.table)

    def grid(self, metric: str) -> np.ndarray:
        """Valores de ``metric`` con la forma de la rejilla (NaN = combinación inválida)."""
        return self.table[metric].to_numpy(dtype=float).reshape(self.shape)


def run_sweep(
    target: Target,
    axes: dict[str, list],
    period: str = "is",
    *,
    confirm_oos: bool = False,
    n_jobs: int = -1,
    cache_dir: Path | None = DEFAULT_CACHE,
    progress: bool = False,
) -> SweepResult:
    """Evalúa todas las combinaciones (en paralelo y con caché en disco)."""
    check_period(period, confirm_oos)
    unknown = [k for k in axes if k not in target.params]
    if unknown:
        raise ValueError(
            f"parámetro(s) {unknown} no existen en {target.strategy}; "
            f"disponibles: {sorted(target.params)}"
        )
    if not 1 <= len(axes) <= 3:
        raise ValueError("la rejilla tiene que tener 1, 2 o 3 parámetros")
    grid = build_grid(axes, target.params)
    keys = [_key(target, p, period) for p in grid]
    res: dict[str, tuple[dict, pd.Series]] = {}
    if cache_dir is not None:
        for k in set(keys):
            hit = _cache_read(Path(cache_dir), k)
            if hit is not None:
                res[k] = hit
    todo = [(k, p) for k, p in zip(keys, grid, strict=True) if k not in res]
    todo = list({k: (k, p) for k, p in todo}.values())
    n_cached = len(grid) - len(todo)
    if todo:
        from joblib import Parallel, delayed, effective_n_jobs

        nj = 1 if len(todo) < 4 else max(1, min(effective_n_jobs(n_jobs), len(todo)))
        chunks = [todo[i::nj] for i in range(nj)] if nj > 1 else [todo]
        if nj == 1:
            outs = [_eval_chunk(target, todo, period, cache_dir)]
        else:
            outs = Parallel(n_jobs=nj, backend="loky", verbose=5 if progress else 0)(
                delayed(_eval_chunk)(target, c, period, cache_dir) for c in chunks
            )
        for out in outs:
            for k, m, r in out:
                res[k] = (m, r)
    rows, rets = [], {}
    for i, (k, p) in enumerate(zip(keys, grid, strict=True)):
        m, r = res[k]
        rows.append(
            {
                **{a: p[a] for a in axes},
                **{x: m.get(x, np.nan) for x in METRICS},
                "kill_switch": m.get("kill_switch", ""),
                "error": m.get("error", ""),
            }
        )
        if len(r):
            rets[i] = r.set_axis(r.index.as_unit("ns"))  # misma unidad, venga o no de caché
    table = pd.DataFrame(rows)
    for x in METRICS:
        table[x] = pd.to_numeric(table[x], errors="coerce")
    returns = pd.DataFrame(rets).sort_index().fillna(0.0) if rets else pd.DataFrame()
    return SweepResult(
        target=target,
        axes=axes,
        period=period,
        table=table,
        returns=returns,
        default_idx=grid_index(axes, target.params),
        n_cached=n_cached,
        n_computed=len(todo),
    )


# ---------------------------------------------------------------------- robustez


def _neighbors(idx: tuple[int, ...], shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    """Vecinos a distancia 1 en cualquier dirección (8 en 2D, 26 en 3D), dentro de la rejilla."""
    out = []
    for d in itertools.product((-1, 0, 1), repeat=len(shape)):
        if not any(d):
            continue
        j = tuple(i + k for i, k in zip(idx, d, strict=True))
        if all(0 <= x < n for x, n in zip(j, shape, strict=True)):
            out.append(j)
    return out


def _within(v: float, ref: float, tol: float) -> bool:
    return bool(np.isfinite(v) and v >= ref - tol * abs(ref))


def robustness(
    values: np.ndarray,
    default_idx: tuple[int, ...] | None = None,
    tol: float = DEFAULT_TOL,
    higher_is_better: bool = True,
) -> dict:
    """Puntuación de robustez (0–100) de una superficie de resultados.

    Componentes (todos en [0, 1]):
      - ``neighbor_share``: vecinos del mejor que quedan dentro del ``tol`` del mejor;
      - ``plateau_share``: tamaño de la meseta CONECTADA al mejor (celdas dentro del ``tol``),
        como fracción de la rejilla; se satura al 30 %;
      - ``median_ratio``: mediana de la rejilla / mejor (1 = todo igual de bueno).
    score = 100 × (0,5·vecinos + 0,3·min(1, meseta/0,3) + 0,2·mediana/mejor).
    Si el mejor valor no es positivo (p. ej. Sharpe ≤ 0 en todo el mapa) el score es 0.
    """
    from scipy import ndimage

    v = np.asarray(values, dtype=float)
    if not higher_is_better:
        v = -v
    shape = v.shape
    finite = np.isfinite(v)
    if not finite.any():
        return {"score": 0.0, "verdict": "sin datos", "best_idx": None, "n_valid": 0}
    vv = np.where(finite, v, -np.inf)
    best_idx = tuple(int(i) for i in np.unravel_index(np.argmax(vv), shape))
    best = float(v[best_idx])
    med = float(np.nanmedian(v))
    thr = best - tol * abs(best)
    nb = _neighbors(best_idx, shape)
    nshare = float(np.mean([_within(v[j], best, tol) for j in nb])) if nb else float("nan")
    ok = finite & (vv >= thr)
    lab, _ = ndimage.label(ok, structure=np.ones((3,) * len(shape)))
    comp = lab == lab[best_idx]
    plateau = float(comp.sum() / finite.sum())
    widths = {}
    for ax in range(len(shape)):
        other = tuple(i for i in range(len(shape)) if i != ax)
        present = comp.any(axis=other) if other else comp
        widths[ax] = float(present.sum() / shape[ax])
    on_edge = [
        ax
        for ax, (i, n) in enumerate(zip(best_idx, shape, strict=True))
        if n > 2 and i in (0, n - 1)
    ]
    ratio = best / med if med > 0 else float("inf") if best > 0 else float("nan")
    if best <= 0:
        score = 0.0
    else:
        mr = float(np.clip(med / best, 0, 1)) if np.isfinite(med) else 0.0
        ns = nshare if np.isfinite(nshare) else 0.0
        score = 100 * (0.5 * ns + 0.3 * min(1.0, plateau / 0.3) + 0.2 * mr)
    out = {
        "score": float(round(score, 1)),
        "verdict": verdict(score, best),
        "best_idx": best_idx,
        "best": best if higher_is_better else -best,
        "median": med if higher_is_better else -med,
        "best_median_ratio": float(ratio),
        "neighbor_share": nshare,
        "n_neighbors": len(nb),
        "plateau_share": plateau,
        "plateau_cells": int(comp.sum()),
        "plateau_width": widths,
        "share_within_tol": float(ok.sum() / finite.sum()),
        "share_positive": float((v[finite] > 0).mean()),
        "best_on_edge": on_edge,
        "n_valid": int(finite.sum()),
        "tol": tol,
    }
    if default_idx is not None and finite[default_idx]:
        d = float(v[default_idx])
        dn = _neighbors(default_idx, shape)
        out.update(
            default_value=d if higher_is_better else -d,
            default_pct_rank=float((v[finite] <= d).mean()),
            default_gap=float((best - d) / abs(best)) if best else float("nan"),
            default_neighbor_share=float(np.mean([_within(v[j], d, tol) for j in dn]))
            if dn
            else float("nan"),
            default_in_plateau=bool(comp[default_idx]),
        )
    return out


def verdict(score: float, best: float = 1.0) -> str:
    if best <= 0:
        return "sin zona buena: ninguna combinación sale positiva"
    if score >= 70:
        return "meseta: robusto a los parámetros"
    if score >= 40:
        return "mixto: hay zona buena pero estrecha, mirar con lupa"
    return "pico: probable sobreajuste"


def overfit_stats(sw: SweepResult, n_blocks: int = 16, registry_trials: int | None = None) -> dict:
    """DSR del mejor por Sharpe y PBO (CSCV) con las rentabilidades de todas las configs."""
    r = sw.returns
    out: dict = {}
    if r.shape[1] < 2:
        return out
    srs = np.array([sharpe_per_period(r[c].to_numpy()) for c in r.columns])
    if not np.isfinite(srs).any():
        return out
    bi = int(np.nanargmax(srs))
    best_r = r.iloc[:, bi].to_numpy()
    out["dsr"] = deflated_sharpe(best_r, srs)
    if registry_trials and registry_trials > len(srs):
        out["dsr_registry"] = deflated_sharpe(best_r, srs, n_trials=registry_trials)
    try:
        nb = n_blocks
        while nb > 2 and len(r) // nb < 20:
            nb -= 2
        p = pbo_cscv(r.to_numpy(), nb)
        out["pbo"] = {k: v for k, v in p.items() if k != "logits"}
        out["pbo_logits"] = p["logits"]
    except ValueError as e:
        out["pbo_error"] = str(e)
    return out


def warnings_for(sw: SweepResult, metric: str, rob: dict, ov: dict) -> list[str]:
    """Avisos de sobreajuste, en español llano."""
    w = []
    names = list(sw.axes)
    if sw.period != "is":
        w.append(
            f"⚠️ Este barrido usa el periodo **{sw.period}** (incluye out-of-sample). Ya no sirve "
            "como prueba limpia: cualquier decisión tomada mirándolo está contaminada."
        )
    w.append(
        f"Se han probado **{sw.n_configs} configuraciones**. Quedarse con la mejor de "
        f"{sw.n_configs} "
        "infla el resultado por pura suerte (sesgo de selección). Usa el mapa para ver la FORMA "
        "(meseta o pico), no para elegir el máximo."
    )
    if rob.get("best_on_edge"):
        ax = ", ".join(names[i] for i in rob["best_on_edge"])
        w.append(
            f"El mejor resultado está en el **borde** de la rejilla ({ax}): el óptimo podría "
            "estar fuera. Ampliar la rejilla suma configuraciones (y anótalo en el registro)."
        )
    ns = rob.get("neighbor_share", np.nan)
    if np.isfinite(ns) and ns < 0.5:
        w.append(
            f"**Pico aislado**: solo el {ns:.0%} de los vecinos del mejor está dentro del "
            f"{rob['tol']:.0%} de su valor. Huele a sobreajuste."
        )
    ratio = rob.get("best_median_ratio", np.nan)
    if np.isfinite(ratio) and ratio > 2:
        w.append(
            f"El mejor es **{ratio:.1f} veces la mediana** del mapa: muy por encima del típico."
        )
    if rob.get("share_positive", 1) < 0.7 and metric in ("sharpe", "cagr", "mar", "expectancy_r"):
        w.append(
            f"Solo el {rob['share_positive']:.0%} de las combinaciones da {METRICS[metric][0]} "
            "positivo: el resultado depende mucho de los parámetros."
        )
    if rob.get("best_idx") is not None:
        bt = sw.table.iloc[int(np.ravel_multi_index(rob["best_idx"], sw.shape))]
        if sw.target.kind == "signals" and bt["trades"] < 30:
            w.append(
                f"La mejor combinación tiene solo {int(bt['trades'])} operaciones: muestra "
                "pequeña, "
                "el número es poco fiable."
            )
    if "default_in_plateau" in rob and not rob["default_in_plateau"]:
        w.append(
            "Los parámetros por defecto **no** están en la meseta del mejor: si se cambian para "
            "'subirse' al máximo, eso es una variante nueva que hay que re-validar."
        )
    pbo = ov.get("pbo", {}).get("pbo")
    if pbo is not None and pbo >= 0.5:
        msg = (
            f"**PBO = {pbo:.0%}**: la configuración que gana en una mitad de la historia queda "
            "por debajo de la mediana en la otra mitad la mayoría de las veces. Elegir 'la mejor' "
            "aquí no aporta nada."
        )
        if rob.get("score", 0) >= 70:
            msg += (
                " Con una meseta ancha es lo esperable: las combinaciones dan casi lo mismo y su "
                "orden cambia por ruido. Lectura práctica: no optimices, quédate con los "
                "parámetros pre-registrados (o los de manual)."
            )
        w.append(msg)
    elif pbo is not None and pbo >= 0.25:
        w.append(f"PBO = {pbo:.0%}: riesgo de sobreajuste moderado al elegir la mejor.")
    dsr = ov.get("dsr", {}).get("dsr")
    if dsr is not None and np.isfinite(dsr) and dsr < 0.95:
        w.append(
            f"**Deflated Sharpe = {dsr:.2f}** (< 0,95): teniendo en cuenta los "
            f"{ov['dsr']['n_trials']} intentos, el Sharpe del mejor no es claramente distinto "
            "del que saldría por suerte al elegir el máximo."
        )
    if sw.target.kind == "weights":
        w.append(
            "Estrategia mensual por pesos (allocation_sim): sin stop ni 1 % de riesgo ni kill "
            "switch. Es una referencia, no cumple las reglas duras tal cual."
        )
    elif not sw.target.kill_switch:
        w.append(
            "Barrido SIN kill switch (como en las baselines). Con la regla del "
            f"{load_settings()['risk']['kill_switch_drawdown']:.0%} activada los "
            "números cambian mucho; repite con kill switch antes de cualquier veredicto."
        )
    return w


def score_metric(sw: SweepResult, metric: str, tol: float = DEFAULT_TOL) -> dict:
    """``robustness`` sobre una métrica de la tabla, con las cifras en su unidad original.

    La caída máxima es negativa: se puntúa con 1/|caída| (mayor = mejor, siempre positiva),
    así "dentro del 20 %" significa una caída como mucho un 25 % más profunda que la mejor.
    """
    if metric not in SCORABLE:
        raise ValueError(f"métrica no puntuable: {metric} (usa {', '.join(SCORABLE)})")
    raw = sw.grid(metric)
    vals = 1.0 / np.abs(np.where(raw < 0, raw, np.nan)) if metric == "max_dd" else raw
    rob = robustness(vals, sw.default_idx, tol)
    if rob.get("best_idx") is not None:
        rob["best"] = float(raw[rob["best_idx"]])
        rob["median"] = float(np.nanmedian(raw))
        if sw.default_idx is not None and "default_value" in rob:
            rob["default_value"] = float(raw[sw.default_idx])
    rob["metric"] = metric
    return rob
