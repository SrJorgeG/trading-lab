"""Preparación de datos de las vistas 3D (sin depender del navegador)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.backtest.montecarlo import MCConfig, run_montecarlo
from tlab.backtest.montecarlo3d import (
    anim_payload,
    density_grid,
    first_hit_index,
    money_ticks,
    outcome_percentile,
    outcomes_data,
    relative_density,
    select_paths,
    spaghetti_data,
    time_axis,
    write_html_3d,
)


def _result(n=300, t=400, keep=True, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2015-01-01", periods=t, freq="D", tz="UTC")
    eq = pd.Series(10_000 * np.cumprod(1 + rng.normal(0.0004, 0.01, t)), index=idx)
    cfg = MCConfig(n=n, seed=42, method="block", block_length=10, keep_paths=keep)
    return run_montecarlo(eq, None, cfg), cfg


def test_keep_paths_flag():
    r, _ = _result(keep=True)
    assert r.paths is not None and r.paths.shape == (300, 400)
    np.testing.assert_allclose(r.paths[:, -1], r.final_equity)
    r2, _ = _result(keep=False)
    assert r2.paths is None


def test_density_grid_shape_and_normalization():
    rng = np.random.default_rng(0)
    paths = 10_000 * np.cumprod(1 + rng.normal(0, 0.01, (500, 60)), axis=1)
    levels, dens = density_grid(paths, n_levels=40)
    assert levels.shape == (40,)
    assert dens.shape == (40, 60)
    np.testing.assert_allclose(dens.sum(axis=0), 1.0, atol=1e-9)
    assert np.all(np.diff(levels) > 0)
    assert (dens >= 0).all()


def test_density_spreads_over_time():
    rng = np.random.default_rng(0)
    paths = 10_000 * np.cumprod(1 + rng.normal(0, 0.01, (2000, 200)), axis=1)
    _, dens = density_grid(paths, n_levels=60, smooth=0)
    # Al principio todo está concentrado; al final, repartido (pico más bajo).
    assert dens[:, 1].max() > dens[:, -1].max()


def test_density_grid_rejects_empty():
    with pytest.raises(ValueError):
        density_grid(np.empty((0, 0)))


def test_relative_density_peak_is_one():
    rng = np.random.default_rng(3)
    d = rng.random((30, 20))
    rel = relative_density(d, time_smooth=3)
    assert rel.shape == d.shape
    np.testing.assert_allclose(rel.max(axis=0), 1.0)


def test_select_paths_sorted_and_includes_extremes():
    rng = np.random.default_rng(5)
    final = rng.normal(100, 20, 1000)
    sel = select_paths(final, 50)
    assert len(sel) == 50
    assert len(set(sel.tolist())) == 50
    assert np.all(np.diff(final[sel]) >= 0)
    assert final[sel[0]] == final.min() and final[sel[-1]] == final.max()
    # k >= n devuelve todo ordenado
    small = np.array([3.0, 1.0, 2.0])
    np.testing.assert_array_equal(select_paths(small, 10), [1, 2, 0])


def test_outcome_percentile_range():
    p = outcome_percentile(np.array([5.0, 1.0, 3.0]))
    np.testing.assert_allclose(p, [1.0, 0.0, 0.5])


def test_first_hit_index():
    p = np.array([[100, 110, 95, 120], [100, 101, 102, 103]], dtype=float)
    np.testing.assert_array_equal(first_hit_index(p, 0.10), [2, -1])


def test_spaghetti_data_consistent():
    r, _ = _result()
    d = spaghetti_data(r, k=40, max_t=50)
    assert d["z"].shape == (40, len(d["x"]))
    assert len(d["x"]) <= 50
    assert np.all(np.diff(r.final_equity[d["sel"]]) >= 0)
    assert 0 <= d["real_y"] <= 39
    assert d["xlab"] == "Año"
    x, _ = time_axis(r)
    assert np.all(np.diff(x) > 0)


def test_spaghetti_needs_paths():
    r, _ = _result(keep=False)
    with pytest.raises(ValueError):
        spaghetti_data(r)


def test_outcomes_and_anim_payload():
    r, _ = _result()
    o = outcomes_data(r, max_points=100)
    assert all(len(o[k]) == 100 for k in ("cagr", "dd", "days", "pct"))
    a = anim_payload(r, k=20, max_t=30)
    assert len(a["z"]) == 20 and len(a["z"][0]) == len(a["x"]) == len(a["real"])


def test_money_ticks():
    pos, txt = money_ticks(9_000, 120_000, log=True)
    assert "10k $" in txt and "100k $" in txt
    assert pos == sorted(pos)


def test_write_html_3d(tmp_path):
    pytest.importorskip("plotly")
    r, cfg = _result(n=200, t=200)
    out = write_html_3d(r, cfg, tmp_path / "mc3d.html", "Prueba", k=30)
    html = out.read_text(encoding="utf-8")
    assert "Cómo leerlo" in html and '"spag"' in html and '"dens"' in html
    assert "<script src=" not in html  # autocontenido: plotly.js va incrustado
    assert out.stat().st_size < 15e6
