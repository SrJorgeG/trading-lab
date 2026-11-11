"""Benchmark al azar: reproducibilidad, emparejamiento y p-valores con ventaja conocida."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.backtest.random_benchmark import (
    _runs,
    empirical_p,
    p_verdict,
    random_intervals,
    random_weights,
    run_random_benchmark,
    summary_table,
    turnover_changes,
)
from tlab.backtest.robust_reports import load_random, registry_trials, write_random_outputs
from tlab.backtest.runner import OOSGuardError
from tlab.backtest.targets import build_target
from tlab.strategies import ALLOCATION_STRATEGIES, SIGNAL_STRATEGIES
from tlab.strategies.base import empty_signals

HOLD = 10
FLAG = 99_999.0  # volumen marcado = "día de evento" que la estrategia oráculo ve al cierre


def oracle_signals(bars: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Entra el día marcado (causal: lo ve al cierre) y sale HOLD velas después."""
    out = empty_signals(bars.index)
    flag = (bars["volume"] == FLAG).to_numpy()
    ex = np.zeros(len(bars), bool)
    ex[HOLD:] = flag[:-HOLD]
    out["entry"] = flag
    out["exit"] = ex
    out["stop_price"] = bars["close"] * float(params.get("stop_frac", 0.8))
    return out


def edge_bars(n: int, seed: int, edge: bool) -> pd.DataFrame:
    """Paseo aleatorio; cada ~45 velas un día marcado. Con ``edge`` las HOLD velas siguientes
    suben un 1 % diario (la ventaja que solo el oráculo conoce)."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2015-01-01", periods=n, freq="B", tz="UTC")
    r = rng.normal(0, 0.01, n)
    flags = np.arange(400, n - HOLD - 2, 45)
    if edge:
        for f in flags:
            r[f + 1 : f + 1 + HOLD] += 0.01
    close = 100 * np.exp(np.cumsum(r))
    open_ = np.r_[100, close[:-1]]
    hi, lo = np.maximum(open_, close) * 1.002, np.minimum(open_, close) * 0.998
    vol = np.full(n, 1000.0)
    vol[flags] = FLAG
    return pd.DataFrame(
        {"open": open_, "high": hi, "low": lo, "close": close, "volume": vol}, index=idx
    )


@pytest.fixture
def oracle(monkeypatch):
    monkeypatch.setitem(SIGNAL_STRATEGIES, "oracle_test", oracle_signals)
    return {"universe": ["SPY"], "params": {"stop_frac": 0.8}, "status": "test"}


def _target(settings, cfg, bars, kill=False):
    return build_target(
        "oracle_test", kill_switch=kill, data={"SPY": bars}, settings=settings, strat_cfg=cfg
    )


# ------------------------------------------------------------------ piezas


def test_empirical_p_and_verdicts():
    x = np.array([1.0, 2.0, 3.0, np.nan])
    assert empirical_p(x, 4.0) == pytest.approx(1 / 4)
    assert empirical_p(x, 0.0) == pytest.approx(1.0)
    assert empirical_p(x, 2.0) == pytest.approx(3 / 4)
    assert np.isnan(empirical_p(x, np.nan))
    assert p_verdict(0.01) == "ventaja probable"
    assert p_verdict(0.07).startswith("indicio")
    assert p_verdict(0.5) == "indistinguible del azar"


def test_random_intervals_no_overlap_and_exact_durations():
    rng = np.random.default_rng(3)
    d = np.array([5, 10, 3, 8, 1, 20])
    iv = random_intervals(200, d, rng)
    assert len(iv) == len(d)
    assert sorted(q - p for p, q in iv) == sorted(d)
    iv = sorted(iv)
    assert all(iv[i][1] < iv[i + 1][0] for i in range(len(iv) - 1))  # sin solaparse
    assert iv[0][0] >= 0 and iv[-1][1] <= 200 - 2
    # si no caben todas, se descartan (nunca se solapan ni se salen)
    assert len(random_intervals(30, np.full(10, 9), rng)) == 2


def test_random_weights_keep_states_months_and_turnover():
    idx = pd.date_range("2010-01-31", periods=60, freq="ME", tz="UTC")
    state = np.r_[np.ones(14), np.zeros(5), np.ones(20), np.zeros(9), np.ones(12)]
    w = pd.DataFrame({"SPY": state}, index=idx)
    rng = np.random.default_rng(0)
    for _ in range(20):
        r = random_weights(w, rng)
        assert r.shape == w.shape and r.index.equals(w.index)
        assert r["SPY"].sum() == w["SPY"].sum()  # mismos meses invertido
        assert turnover_changes(r) == turnover_changes(w) == 4  # misma rotación
    # varios estados (tipo dual momentum)
    st = [(1, 0, 0)] * 6 + [(0, 1, 0)] * 4 + [(0, 0, 1)] * 5 + [(1, 0, 0)] * 3 + [(0, 1, 0)] * 6
    w3 = pd.DataFrame(st, index=idx[:24], columns=["A", "B", "C"], dtype=float)
    r3 = random_weights(w3, rng)
    assert turnover_changes(r3) == turnover_changes(w3)
    assert (r3.sum() == w3.sum()).all()
    assert sorted(len(_runs(r3)) for _ in [0]) == [len(_runs(w3))]


# ------------------------------------------------------------------ benchmark completo


def test_reproducible_with_seed_and_independent_of_jobs(settings, oracle):
    t = _target(settings, oracle, edge_bars(900, 1, edge=True))
    a = run_random_benchmark(t, n=30, seed=7, n_jobs=1, calibrate=False)
    b = run_random_benchmark(t, n=30, seed=7, n_jobs=2, calibrate=False)
    c = run_random_benchmark(t, n=30, seed=8, n_jobs=1, calibrate=False)
    cols = ["sharpe", "cagr", "max_dd", "trades"]
    pd.testing.assert_frame_equal(a.table[cols], b.table[cols])
    assert not a.table["sharpe"].equals(c.table["sharpe"])
    assert a.paths.shape[1] == 30


def test_matched_trade_count_and_holding(settings, oracle):
    # Stop muy lejano: ni la real ni los monos salen por stop → el emparejamiento es exacto.
    oracle["params"]["stop_frac"] = 0.2
    t = _target(settings, oracle, edge_bars(900, 2, edge=False))
    rr = run_random_benchmark(t, n=40, seed=1, n_jobs=1)
    m = rr.match
    assert m["trades"]["real"] >= 5
    assert m["trades"]["azar_media"] == pytest.approx(m["trades"]["real"], abs=0.5)
    assert m["avg_hold"]["azar_media"] == pytest.approx(m["avg_hold"]["real"], rel=0.05)
    assert m["exposure"]["azar_media"] == pytest.approx(m["exposure"]["real"], rel=0.25)


def test_known_edge_beats_random_and_no_edge_does_not(settings, oracle):
    good = run_random_benchmark(
        _target(settings, oracle, edge_bars(1000, 3, edge=True)), n=80, seed=42, n_jobs=1
    )
    assert good.p_value("sharpe") < 0.05
    assert good.percentile("sharpe") > 0.95
    assert summary_table(good).set_index("metrica").loc["sharpe", "veredicto"] == "ventaja probable"
    # Sin ventaja el p-valor tiene que repartirse más o menos uniforme entre caminos al azar:
    # casi nunca < 0,05 y con la mediana lejos de 0.
    ps = []
    for path_seed in range(6):
        t = _target(settings, oracle, edge_bars(1000, path_seed, edge=False))
        rr = run_random_benchmark(t, n=30, seed=1, n_jobs=1, calibrate=False)
        ps.append(rr.p_value("sharpe"))
    assert sum(p < 0.05 for p in ps) <= 1
    assert np.median(ps) > 0.15


def test_weights_benchmark_known_edge(settings, monkeypatch):
    """Oráculo mensual: invierte solo en los meses que suben (los conoce por adelantado a
    propósito); los monos con la misma rotación no pueden igualarlo."""
    n = 1600
    idx = pd.date_range("2010-01-01", periods=n, freq="B", tz="UTC")
    rng = np.random.default_rng(5)
    month = idx.year * 12 + idx.month
    good_m = {m for m in np.unique(month) if rng.random() < 0.5}
    r = rng.normal(0, 0.006, n) + np.where(np.isin(month, list(good_m)), 0.003, -0.003)
    close = 100 * np.exp(np.cumsum(r))
    bars = pd.DataFrame(
        {
            "open": np.r_[100, close[:-1]],
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1.0,
        },
        index=idx,
    )

    def oracle_w(closes, params):
        from tlab.strategies.allocation import monthly_closes

        mc = monthly_closes(closes)
        nxt = pd.Series([(t.year * 12 + t.month + 1) in good_m for t in mc.index], index=mc.index)
        return pd.DataFrame({"SPY": nxt.astype(float)})

    monkeypatch.setitem(ALLOCATION_STRATEGIES, "oracle_w", oracle_w)
    t = build_target("oracle_w", ["SPY"], data={"SPY": bars}, settings=settings)
    rr = run_random_benchmark(t, n=60, seed=1, n_jobs=1)
    assert rr.p_value("sharpe") < 0.05
    assert rr.match["changes"]["azar_media"] == rr.match["changes"]["real"]
    assert rr.match["exposure"]["azar_media"] == pytest.approx(
        rr.match["exposure"]["real"], abs=0.02
    )


def test_random_oos_guard(settings, oracle):
    t = _target(settings, oracle, edge_bars(900, 1, edge=True))
    with pytest.raises(OOSGuardError):
        run_random_benchmark(t, n=5, period="oos")
    with pytest.raises(OOSGuardError):
        run_random_benchmark(t, n=5, period="full")


def test_random_outputs_registry_not_counted_as_variant(settings, oracle, tmp_path):
    t = _target(settings, oracle, edge_bars(900, 1, edge=True))
    rr = run_random_benchmark(t, n=25, seed=3, n_jobs=1, calibrate=False)
    reg = tmp_path / "reg.md"
    res = write_random_outputs(rr, tmp_path / "r", registry=reg, png=False, html=True)
    txt = reg.read_text(encoding="utf-8")
    assert "benchmark azar" in txt and "25 monos" in txt
    assert registry_trials(reg, "oracle_test") == 0  # no cuenta como variante probada
    for k in ("csv", "summary", "json", "curves", "md", "html"):
        assert res["paths"][k].exists()
    md = res["paths"]["md"].read_text(encoding="utf-8")
    assert "## Veredicto" in md and "p-valor" in md
    rl, meta = load_random(tmp_path / "r")
    assert rl.p_value("sharpe") == pytest.approx(rr.p_value("sharpe"))
    assert rl.paths.shape[1] == min(25, rr.paths.shape[1])
    from tlab.backtest import robust_viz as viz

    assert viz.fig_random_png(rl, "sharpe", "t") is not None
    assert viz.fig_random_violin(rl) is not None
