"""Control del sobreajuste al elegir entre muchas configuraciones.

- **Deflated Sharpe Ratio** (Bailey y López de Prado, 2014): probabilidad de que el Sharpe del
  MEJOR de N intentos sea mayor que el que saldría por pura suerte al elegir el máximo de N.
- **PBO por CSCV** (Bailey, Borwein, López de Prado y Zhu, 2015): parte la historia en S bloques,
  elige la mejor configuración en la mitad de los bloques y mira en qué puesto queda en la otra
  mitad, para todas las combinaciones. PBO = proporción de veces que la "mejor" queda por
  debajo de la mediana fuera de muestra.

Todo trabaja con Sharpe POR PERIODO (diario, sin anualizar), como en los artículos.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
from scipy import stats

EULER_GAMMA = 0.5772156649015329


def sharpe_per_period(r: np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    r = r[np.isfinite(r)]
    if len(r) < 2:
        return float("nan")
    sd = r.std(ddof=1)
    return float(r.mean() / sd) if sd > 0 else float("nan")


def probabilistic_sharpe(sr: float, sr0: float, t: int, skew: float, kurt: float) -> float:
    """PSR: P(SR verdadero > sr0) dado el SR observado en t periodos (kurt NO en exceso)."""
    den = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2
    if t < 2 or den <= 0 or not np.isfinite(sr):
        return float("nan")
    z = (sr - sr0) * math.sqrt(t - 1) / math.sqrt(den)
    return float(stats.norm.cdf(z))


def expected_max_sharpe(var_sr: float, n_trials: int) -> float:
    """SR0: Sharpe máximo esperado entre N intentos sin ventaja (SR verdadero = 0)."""
    if n_trials <= 1 or var_sr <= 0:
        return 0.0
    n = float(n_trials)
    q1 = stats.norm.ppf(1.0 - 1.0 / n)
    q2 = stats.norm.ppf(1.0 - 1.0 / (n * math.e))
    return float(math.sqrt(var_sr) * ((1.0 - EULER_GAMMA) * q1 + EULER_GAMMA * q2))


def deflated_sharpe(
    best_returns: np.ndarray, trial_sharpes: np.ndarray, n_trials: int | None = None
) -> dict:
    """DSR del mejor intento. ``trial_sharpes`` = Sharpe por periodo de TODOS los intentos.

    ``n_trials`` permite usar un N mayor que los intentos de este barrido (p. ej. el total
    del registro de pruebas); por defecto, el nº de intentos con Sharpe finito.
    """
    r = np.asarray(best_returns, dtype=float)
    r = r[np.isfinite(r)]
    srs = np.asarray(trial_sharpes, dtype=float)
    srs = srs[np.isfinite(srs)]
    n = int(n_trials or len(srs))
    sr = sharpe_per_period(r)
    var = float(srs.var(ddof=1)) if len(srs) > 1 else 0.0
    sr0 = expected_max_sharpe(var, n)
    sk = float(stats.skew(r)) if len(r) > 2 else 0.0
    ku = float(stats.kurtosis(r, fisher=False)) if len(r) > 3 else 3.0
    return {
        "dsr": probabilistic_sharpe(sr, sr0, len(r), sk, ku),
        "psr0": probabilistic_sharpe(sr, 0.0, len(r), sk, ku),
        "sr": sr,
        "sr0": sr0,
        "n_trials": n,
        "t": int(len(r)),
        "skew": sk,
        "kurt": ku,
        "var_sr": var,
    }


def pbo_cscv(returns: np.ndarray, n_blocks: int = 16) -> dict:
    """Probabilidad de sobreajuste del backtest (CSCV) con Sharpe como criterio.

    ``returns``: matriz T × N (periodos × configuraciones). ``n_blocks`` par (S). Devuelve
    ``pbo``, los logits λ de cada combinación y la media del Sharpe fuera de muestra del elegido.
    """
    m = np.asarray(returns, dtype=float)
    if m.ndim != 2 or m.shape[1] < 2:
        raise ValueError("PBO necesita una matriz T×N con N >= 2 configuraciones")
    if n_blocks % 2 or n_blocks < 2:
        raise ValueError("n_blocks tiene que ser par y >= 2")
    m = np.nan_to_num(m, nan=0.0)
    t = (m.shape[0] // n_blocks) * n_blocks
    if t < n_blocks * 2:
        raise ValueError("muy pocos periodos para tantos bloques")
    m = m[:t]
    blocks = m.reshape(n_blocks, t // n_blocks, m.shape[1])
    s1, s2 = blocks.sum(axis=1), (blocks**2).sum(axis=1)  # S × N
    cnt = t // n_blocks
    combos = np.array(list(itertools.combinations(range(n_blocks), n_blocks // 2)))
    mask = np.zeros((len(combos), n_blocks), dtype=float)
    np.put_along_axis(mask, combos, 1.0, axis=1)

    def _sr(mk):
        n = mk.sum(axis=1, keepdims=True) * cnt
        a, b = mk @ s1, mk @ s2
        mean = a / n
        var = (b - n * mean**2) / (n - 1)
        with np.errstate(invalid="ignore", divide="ignore"):
            sr = mean / np.sqrt(var)
        return np.where(np.isfinite(sr) & (var > 1e-18), sr, -np.inf)

    sr_in, sr_out = _sr(mask), _sr(1.0 - mask)
    best = np.argmax(sr_in, axis=1)
    ranks = stats.rankdata(sr_out, axis=1)  # 1 = peor, N = mejor (empates: media)
    n = m.shape[1]
    w = ranks[np.arange(len(combos)), best] / (n + 1.0)
    logits = np.log(w / (1.0 - w))
    oos = sr_out[np.arange(len(combos)), best]
    return {
        "pbo": float(np.mean(logits <= 0)),
        "logits": logits,
        "n_combos": int(len(combos)),
        "n_blocks": n_blocks,
        "oos_sr_of_best_median": float(np.median(oos[np.isfinite(oos)])) if len(oos) else np.nan,
    }
