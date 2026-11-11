"""Deflated Sharpe Ratio y PBO (CSCV) con casos de resultado conocido."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from tlab.backtest.overfit import (
    deflated_sharpe,
    expected_max_sharpe,
    pbo_cscv,
    probabilistic_sharpe,
)


def test_psr_matches_formula():
    # SR diario 0,1, 252 días, normal (asimetría 0, curtosis 3)
    z = 0.1 * math.sqrt(251) / math.sqrt(1 + (3 - 1) / 4 * 0.01)
    assert probabilistic_sharpe(0.1, 0.0, 252, 0.0, 3.0) == pytest.approx(stats.norm.cdf(z))
    assert probabilistic_sharpe(0.0, 0.0, 252, 0.0, 3.0) == pytest.approx(0.5)
    # colas gordas y asimetría negativa → menos confianza
    assert probabilistic_sharpe(0.1, 0, 252, -1.0, 10.0) < probabilistic_sharpe(0.1, 0, 252, 0, 3)


def test_expected_max_sharpe_grows_with_trials():
    assert expected_max_sharpe(0.01, 1) == 0.0
    a, b, c = (expected_max_sharpe(0.0004, n) for n in (10, 100, 1000))
    assert 0 < a < b < c
    # valor de referencia: N=100, sd 0,02 → ≈ 0,02 × 2,53
    assert b == pytest.approx(0.02 * 2.5306, rel=0.01)


def test_dsr_penalises_many_trials():
    rng = np.random.default_rng(1)
    best = rng.normal(0.0008, 0.01, 1500)
    few = deflated_sharpe(best, rng.normal(0.03, 0.02, 5))
    many = deflated_sharpe(best, rng.normal(0.03, 0.02, 500))
    assert many["dsr"] < few["dsr"]
    assert few["psr0"] == pytest.approx(many["psr0"])
    more = deflated_sharpe(best, rng.normal(0.03, 0.02, 5), n_trials=5000)
    assert more["n_trials"] == 5000 and more["dsr"] < few["dsr"]


def test_pbo_noise_is_high_and_true_edge_is_low():
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 0.01, (1600, 20))
    p_noise = pbo_cscv(noise, 16)["pbo"]
    assert 0.25 < p_noise < 0.85  # sin ventaja: elegir el mejor no ayuda
    edge = noise.copy()
    edge[:, 3] += 0.004  # una configuración con ventaja real y estable
    res = pbo_cscv(edge, 16)
    assert res["pbo"] < 0.05
    assert res["n_combos"] == math.comb(16, 8)
    assert len(res["logits"]) == res["n_combos"]


def test_pbo_input_validation():
    with pytest.raises(ValueError):
        pbo_cscv(np.zeros((100, 1)))
    with pytest.raises(ValueError):
        pbo_cscv(np.zeros((100, 3)), n_blocks=5)
    with pytest.raises(ValueError):
        pbo_cscv(np.zeros((10, 3)), n_blocks=16)
