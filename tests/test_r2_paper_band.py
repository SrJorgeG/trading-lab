"""R2-11: banda para el paper (casos B1–B6)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.backtest.paper_band import _block_indices, band_markdown, paper_band


def test_b1_constante():
    b = paper_band(np.full(500, 0.001))
    assert b.loc["6m"].to_numpy() == pytest.approx([0.134211] * 3, abs=1e-6)
    assert b.loc["12m"].to_numpy() == pytest.approx([0.286434] * 3, abs=1e-6)


def test_b2_reproducible():
    r = np.random.default_rng(0).normal(0.0004, 0.01, 800)
    pd.testing.assert_frame_equal(paper_band(r, n=500), paper_band(r, n=500))
    assert not paper_band(r, n=500).equals(paper_band(r, n=500, seed=1))


def test_b3_bloques_enteros():
    T = 100
    idx = _block_indices(T, 252, 21, 50, np.random.default_rng(3))
    assert idx.shape == (50, 252) and idx.max() < T and idx.min() >= 0
    for row in idx:
        for j in range(0, 252, 21):
            chunk = row[j : j + 21]
            assert (np.diff(chunk) == 1).all()


def test_b4_pocos_datos_y_nan():
    with pytest.raises(ValueError):
        paper_band(np.zeros(20), block=21)
    with pytest.raises(ValueError):
        paper_band(np.array([0.0] * 30 + [np.nan]))


def test_b5_ruido_ordenado_y_mas_ancho_a_12m():
    r = np.random.default_rng(1).normal(0.0, 0.01, 2000)
    b = paper_band(r, n=2000)
    for h in ("6m", "12m"):
        assert b.loc[h, "p5"] < b.loc[h, "p50"] < b.loc[h, "p95"]
    assert (b.loc["12m", "p95"] - b.loc["12m", "p5"]) > (b.loc["6m", "p95"] - b.loc["6m", "p5"])


def test_b6_horizonte_corto_coincide():
    r = np.random.default_rng(2).normal(0.0003, 0.01, 1000)
    solo = paper_band(r, horizons={"6m": 126}, n=300)
    junto = paper_band(r, n=300)
    assert solo.loc["6m"].to_numpy() == pytest.approx(junto.loc["6m"].to_numpy())


def test_markdown():
    txt = band_markdown(paper_band(np.full(100, 0.001), n=10), "reports/x/resumen.md")
    assert "reports/x/resumen.md" in txt and "| 6m |" in txt
