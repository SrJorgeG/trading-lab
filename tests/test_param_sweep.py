"""Mapa de parámetros: rejilla, caché, métricas, robustez, guard OOS y registro (sin red)."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from conftest import make_bars

from tlab.backtest.param_sweep import (
    build_grid,
    grid_index,
    parse_axis,
    robustness,
    run_sweep,
    score_metric,
    warnings_for,
)
from tlab.backtest.robust_reports import (
    load_sweep,
    registry_trials,
    rob_from_meta,
    write_sweep_outputs,
)
from tlab.backtest.runner import OOSGuardError
from tlab.backtest.targets import RunOutput, build_target, check_period, extract_metrics

DONCH = {
    "universe": ["SPY", "QQQ"],
    "params": {"entry_n": 20, "exit_n": 10, "atr_mult": 2.0, "atr_n": 20},
    "status": "test",
}


@pytest.fixture(scope="module")
def data():
    return {"SPY": make_bars(700, seed=11, drift=0.0006), "QQQ": make_bars(700, seed=12)}


@pytest.fixture
def target(data, settings):
    return build_target(
        "donchian_atr", kill_switch=False, data=data, settings=settings, strat_cfg=DONCH
    )


# ------------------------------------------------------------------ rejilla


def test_parse_axis_range_list_and_types():
    assert parse_axis("entry_n=10:30:10", 20) == ("entry_n", [10, 20, 30])
    assert parse_axis("months=1:4") == ("months", [1, 2, 3, 4])
    name, v = parse_axis("atr_mult=1.5:3:0.5", 2.0)
    assert name == "atr_mult" and v == [1.5, 2.0, 2.5, 3.0]
    assert parse_axis("atr_mult=2,3", 2.0) == ("atr_mult", [2.0, 3.0])
    assert all(isinstance(x, float) for x in parse_axis("atr_mult=2,3", 2.0)[1])
    for bad in ("entry_n", "entry_n=10:5", "entry_n=1,1", "entry_n=1:5:0"):
        with pytest.raises(ValueError):
            parse_axis(bad)


def test_build_grid_order_and_index():
    axes = {"a": [1, 2, 3], "b": [10, 20]}
    g = build_grid(axes, {"a": 2, "b": 10, "c": 7})
    assert len(g) == 6 and all(p["c"] == 7 for p in g)
    assert [(p["a"], p["b"]) for p in g[:3]] == [(1, 10), (1, 20), (2, 10)]  # último eje rápido
    assert grid_index(axes, {"a": 2, "b": 10}) == (1, 0)
    assert grid_index(axes, {"a": 5, "b": 10}) is None


def test_sweep_shape_cache_and_fingerprint(target, settings, data, tmp_path):
    axes = {"entry_n": [10, 20, 30], "exit_n": [5, 10]}
    sw = run_sweep(target, axes, n_jobs=1, cache_dir=tmp_path)
    assert sw.shape == (3, 2) and sw.n_configs == 6 and sw.n_computed == 6
    assert sw.grid("sharpe").shape == (3, 2)
    assert sw.default_idx == (1, 1)
    assert sw.returns.shape[1] == 6 and len(sw.returns) > 100
    # mismo resultado que una ejecución directa
    direct = extract_metrics(target.run({**target.params, "entry_n": 30, "exit_n": 5}), target.ppy)
    assert sw.grid("sharpe")[2, 0] == pytest.approx(direct["sharpe"])
    again = run_sweep(target, axes, n_jobs=1, cache_dir=tmp_path)
    assert again.n_cached == 6 and again.n_computed == 0
    pd.testing.assert_frame_equal(sw.table, again.table)
    pd.testing.assert_frame_equal(sw.returns, again.returns, check_freq=False)
    assert again.returns.index.equals(sw.returns.index)
    # otra configuración de costes → otra huella → no reutiliza la caché
    t2 = build_target(
        "donchian_atr",
        kill_switch=False,
        costs_mode="stress",
        data=data,
        settings=settings,
        strat_cfg=DONCH,
    )
    assert t2.fingerprint() != target.fingerprint()
    assert run_sweep(t2, axes, n_jobs=1, cache_dir=tmp_path).n_cached == 0


def test_sweep_rejects_unknown_param_and_too_many_axes(target):
    with pytest.raises(ValueError, match="no existen"):
        run_sweep(target, {"foo": [1, 2]}, cache_dir=None)
    four = {k: [1, 2] for k in ("entry_n", "exit_n", "atr_n", "atr_mult")}
    with pytest.raises(ValueError, match="1, 2 o 3"):
        run_sweep(target, four, cache_dir=None)


def test_weights_sweep_marks_invalid_combos(settings):
    data = {"SPY": make_bars(1500, seed=5, drift=0.0004)}
    t = build_target("tsmom_12m", ["SPY"], data=data, settings=settings)
    sw = run_sweep(t, {"months": [1, 3, 6], "skip": [0, 1]}, n_jobs=1, cache_dir=None)
    g = sw.grid("sharpe")
    assert np.isnan(g[0, 1])  # months=1, skip=1 es imposible
    assert np.isfinite(g[1:, :]).all()
    assert "skip" in sw.table.loc[1, "error"]


# ------------------------------------------------------------------ métricas


def test_extract_metrics_signals_and_weights():
    idx = pd.date_range("2020-01-01", periods=400, freq="D", tz="UTC")
    eq = pd.Series(np.linspace(10_000, 12_000, 400), index=idx)
    eq.iloc[100:150] *= 0.9  # caída del 10 %
    trades = pd.DataFrame(
        {
            "symbol": ["X", "X"],
            "entry_date": [idx[10], idx[200]],
            "exit_date": [idx[20], idx[230]],
            "pnl_usd": [100.0, -50.0],
            "pnl_r": [1.0, -0.5],
        }
    )
    bars = {"X": pd.DataFrame({"close": 1.0}, index=idx)}
    run = RunOutput(eq, trades, pd.Series(0.5, index=idx))
    m = extract_metrics(run, 365, bars)
    assert m["trades"] == 2 and m["expectancy_r"] == pytest.approx(0.25)
    assert m["avg_hold"] == pytest.approx(20.0)
    assert m["exposure"] == pytest.approx(0.5)
    assert m["mar"] == pytest.approx(m["cagr"] / -m["max_dd"])
    assert m["max_dd"] < -0.09
    w = RunOutput(
        eq, pd.DataFrame({"x": [1, 2, 3]}), pd.Series(1.0, index=idx), weights=pd.DataFrame()
    )
    mw = extract_metrics(w, 252)
    assert mw["trades"] == 3 and np.isnan(mw["expectancy_r"])


# ------------------------------------------------------------------ robustez


def _surface(kind: str) -> np.ndarray:
    x, y = np.meshgrid(np.arange(11), np.arange(6), indexing="ij")
    if kind == "plateau":
        return 1.0 * np.exp(-(((x - 5) / 6.0) ** 2 + ((y - 2.5) / 4.0) ** 2))
    rng = np.random.default_rng(0)
    z = 0.15 + 0.05 * rng.random((11, 6))
    z[7, 3] = 1.0  # aguja aislada
    return z


def test_robustness_plateau_vs_spike():
    plat = robustness(_surface("plateau"), default_idx=(5, 2))
    spike = robustness(_surface("spike"), default_idx=(5, 2))
    assert plat["score"] >= 70 and plat["verdict"].startswith("meseta")
    assert spike["score"] < 40 and spike["verdict"].startswith("pico")
    assert plat["neighbor_share"] == 1.0 and spike["neighbor_share"] == 0.0
    assert spike["best_idx"] == (7, 3) and spike["best_median_ratio"] > 4
    assert plat["default_in_plateau"] and not spike["default_in_plateau"]
    assert plat["plateau_share"] > spike["plateau_share"]


def test_robustness_edges_negative_and_3d():
    z = _surface("plateau")
    edge = robustness(z[6:, :])  # el máximo queda en el borde del 1.er eje
    assert 0 in edge["best_on_edge"]
    neg = robustness(-np.abs(z) - 0.1)
    assert neg["score"] == 0 and neg["verdict"].startswith("sin zona")
    cube = np.ones((3, 3, 3))
    cube[1, 1, 1] = 1.1
    r3 = robustness(cube)
    assert r3["n_neighbors"] == 26 and r3["neighbor_share"] == 1.0
    nan = z.copy()
    nan[0, 0] = np.nan
    assert robustness(nan)["n_valid"] == z.size - 1


def test_score_metric_max_dd_uses_shallowest(target):
    sw = run_sweep(target, {"entry_n": [10, 20, 30], "exit_n": [5, 10]}, n_jobs=1, cache_dir=None)
    r = score_metric(sw, "max_dd")
    dd = sw.grid("max_dd")
    assert r["best"] == pytest.approx(np.nanmax(dd))  # la caída menos profunda
    with pytest.raises(ValueError):
        score_metric(sw, "trades")
    ws = warnings_for(sw, "sharpe", score_metric(sw, "sharpe"), {})
    assert any("6 configuraciones" in w for w in ws)
    assert any("SIN kill switch" in w for w in ws)


# ------------------------------------------------------------------ OOS y registro


def test_oos_guard_refuses_without_confirm(target):
    with pytest.raises(OOSGuardError):
        check_period("oos", False)
    with pytest.raises(OOSGuardError):
        run_sweep(target, {"entry_n": [10, 20]}, period="oos", cache_dir=None)
    with pytest.raises(OOSGuardError):
        run_sweep(target, {"entry_n": [10, 20]}, period="full", cache_dir=None)
    sw = run_sweep(target, {"entry_n": [10, 20]}, period="oos", confirm_oos=True, cache_dir=None)
    a, b = target.window("oos")
    assert sw.returns.index.min() >= a and sw.returns.index.max() <= b
    assert any(
        "out-of-sample" in w for w in warnings_for(sw, "sharpe", score_metric(sw, "sharpe"), {})
    )
    with pytest.raises(ValueError):
        check_period("train", True)


def test_sweep_default_window_is_in_sample_only(target):
    sw = run_sweep(target, {"entry_n": [10, 20]}, n_jobs=1, cache_dir=None)
    _, is_end = target.window("is")
    assert sw.returns.index.max() <= is_end


def test_outputs_and_registry_logging(target, tmp_path):
    reg = tmp_path / "registro.md"
    axes = {"entry_n": [10, 20, 30], "exit_n": [5, 10]}
    sw = run_sweep(target, axes, n_jobs=1, cache_dir=None)
    res = write_sweep_outputs(sw, tmp_path / "s1", registry=reg, png=False, html=True)
    txt = reg.read_text(encoding="utf-8")
    assert "N=6 configuraciones" in txt and "| donchian_atr |" in txt
    assert "sweep-is/base/sin kill switch" in txt
    assert registry_trials(reg, "donchian_atr") == 6
    for k in ("csv", "json", "md", "html"):
        assert res["paths"][k].exists()
    md = res["paths"]["md"].read_text(encoding="utf-8")
    assert "## Veredicto" in md and "Deflated Sharpe" in md and "PBO" in md
    meta = json.loads(res["paths"]["json"].read_text(encoding="utf-8"))
    assert meta["n_configs"] == 6 and meta["registry_trials_before"] == 0
    # segundo barrido: el registro acumula y el DSR usa el total
    sw2 = run_sweep(target, {"entry_n": [15, 25]}, n_jobs=1, cache_dir=None)
    res2 = write_sweep_outputs(sw2, tmp_path / "s2", registry=reg, png=False, html=False)
    assert registry_trials(reg, "donchian_atr") == 8
    assert res2["meta"]["registry_trials_before"] == 6
    assert res2["overfit"]["dsr_registry"]["n_trials"] == 8
    # relectura para el visor
    sw_l, meta_l = load_sweep(tmp_path / "s1")
    assert sw_l.shape == (3, 2) and sw_l.default_idx == (1, 1)
    np.testing.assert_allclose(sw_l.grid("sharpe"), sw.grid("sharpe"))
    rob = rob_from_meta(meta_l, "sharpe")
    assert isinstance(rob["best_idx"], tuple)


def test_figures_build_for_1d_2d_3d(target):
    from tlab.backtest import robust_viz as viz

    for axes in (
        {"entry_n": [10, 20, 30]},
        {"entry_n": [10, 20], "exit_n": [5, 10]},
        {"entry_n": [10, 20], "exit_n": [5, 10], "atr_mult": [2.0, 3.0]},
    ):
        sw = run_sweep(target, axes, n_jobs=1, cache_dir=None)
        rob = score_metric(sw, "sharpe")
        assert viz.fig_heatmap(sw, "sharpe", rob) is not None
        surf = viz.fig_surface(sw, "sharpe", rob)
        assert (surf is None) == (len(axes) == 1)
        if len(axes) == 3:
            assert len(viz.fig_heatmap(sw, "sharpe", rob).layout.sliders[0].steps) == 2
        assert viz.fig_sweep_png(sw, "sharpe", rob, "t") is not None
