"""Candidatas pre-registradas (docs/hipotesis.md): casos a mano de §6 e infraestructura §6.4."""

import math
import tomllib

import numpy as np
import pandas as pd
import pytest
from conftest import make_bars, manual_signals

from tlab.backtest.costs import CostModel
from tlab.backtest.portfolio_sim import SimConfig, simulate
from tlab.backtest.robustness import (
    calibrate_risk,
    drop_best_asset,
    expectancy_by_asset,
    expectancy_by_period,
    kill_switch_episodes,
    param_grid,
)
from tlab.backtest.walkforward import fixed_windows, pick_best
from tlab.config import CONFIG_DIR, load_strategy_config
from tlab.risk import apply_limits, position_size
from tlab.strategies import CANDIDATES, SIGNAL_STRATEGIES

ETF = CostModel(slippage_bps=5)
CRYPTO = CostModel(slippage_bps=20, fee_rate=0.0025)
F, T = False, True


def bars_from(rows, index):
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=index)
    df["volume"] = 1000.0
    return df


# ---------------------------------------------------------------- §6.1 Donchian (H1, H4)
D_ROWS = [(10, 11, 9, 10), (10, 12, 9, 11), (11, 12, 10, 11), (11, 14, 11, 13), (13, 13, 11, 12),
          (12, 12, 8, 9)]  # fmt: skip
D_PARAMS = {"entry_n": 3, "exit_n": 2, "atr_mult": 2, "atr_n": 1}
D_IDX = pd.date_range("2024-01-01", periods=6, freq="D", tz="UTC")


@pytest.mark.parametrize("sid", ["donchian_crypto", "donchian_etf"])
def test_case_d1(sid):
    out = SIGNAL_STRATEGIES[sid](bars_from(D_ROWS, D_IDX), D_PARAMS)
    assert out["entry"].tolist() == [F, F, F, T, F, F]
    assert out["exit"].tolist() == [F, F, F, F, F, T]
    assert out["stop_price"].iloc[3] == pytest.approx(7.0)
    assert out["rank"].iloc[3] == pytest.approx(1 / 3)


@pytest.mark.parametrize("sid", ["donchian_crypto", "donchian_etf"])
def test_case_d2_equal_is_not_breakout(sid):
    rows = list(D_ROWS)
    rows[3] = (11, 14, 11, 12)
    out = SIGNAL_STRATEGIES[sid](bars_from(rows, D_IDX), D_PARAMS)
    assert not out["entry"].any()


@pytest.mark.parametrize("sid", ["donchian_crypto", "donchian_etf"])
def test_case_d3_no_lookahead(sid):
    fn = SIGNAL_STRATEGIES[sid]
    full = fn(bars_from(D_ROWS, D_IDX), D_PARAMS)
    part = fn(bars_from(D_ROWS[:4], D_IDX[:4]), D_PARAMS)
    pd.testing.assert_series_equal(part.iloc[3], full.iloc[3])


# ---------------------------------------------------------------- §6.2 TSMOM (H2)
T_IDX = pd.DatetimeIndex(
    ["2024-01-29", "2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02", "2024-02-05"], tz="UTC"
)
T_PARAMS = {"lookback": 3, "atr_mult": 4, "atr_n": 1}


def tsmom_bars(closes, feb1=None):
    rows = [(c, c, c, c) for c in closes]
    if feb1 is not None:
        rows[3] = feb1
    return bars_from(rows, T_IDX)


def test_case_t1():
    out = SIGNAL_STRATEGIES["tsmom_etf"](
        tsmom_bars([100, 101, 102, 104, 105, 106], (102, 105, 102, 104)), T_PARAMS
    )
    assert out["entry"].tolist() == [F, F, F, T, F, F]
    assert not out["exit"].any()
    assert out["stop_price"].iloc[3] == pytest.approx(92.0)
    assert out["rank"].iloc[3] == pytest.approx(0.04)
    # 02-02 y 02-05: mom > 0 pero no son día de revisión
    assert (out["rank"].iloc[4:] > 0).all()


def test_case_t2():
    out = SIGNAL_STRATEGIES["tsmom_etf"](tsmom_bars([100, 99, 98, 97, 96, 95]), T_PARAMS)
    assert out["exit"].tolist() == [F, F, F, T, F, F]
    assert not out["entry"].any()
    assert out["rank"].iloc[3] == pytest.approx(-0.03)


def test_case_t3_zero_is_not_positive():
    out = SIGNAL_STRATEGIES["tsmom_etf"](tsmom_bars([100, 101, 102, 100, 101, 102]), T_PARAMS)
    assert out["exit"].tolist() == [F, F, F, T, F, F]
    assert not out["entry"].any()


def test_tsmom_first_bar_not_review_and_nan_mom():
    # Arranca el 1 de febrero: la primera vela NO es revisión; con mom NaN no hay señales.
    idx = pd.date_range("2024-02-01", periods=40, freq="B", tz="UTC")
    b = bars_from([(100.0, 101.0, 99.0, 100.0)] * 40, idx)
    out = SIGNAL_STRATEGIES["tsmom_etf"](b, {"lookback": 252, "atr_mult": 4, "atr_n": 1})
    assert not out["entry"].any() and not out["exit"].any()


# ---------------------------------------------------------------- §6.3 RSI(2) (H3)
R_PARAMS = {"rsi_n": 2, "rsi_entry": 10, "trend_n": 20, "exit_sma_n": 2, "atr_mult": 3, "atr_n": 1}


def rsi_bars(closes):
    rows, prev = [], None
    for c in closes:
        o = c if prev is None else prev
        rows.append((o, max(o, c), min(o, c), c))
        prev = c
    return bars_from(rows, pd.date_range("2024-01-01", periods=len(closes), freq="D", tz="UTC"))


def test_case_r1():
    closes = list(range(100, 126)) + [121, 117, 120]
    out = SIGNAL_STRATEGIES["rsi2_etf"](rsi_bars(closes), R_PARAMS)
    from tlab.indicators import rsi, sma

    r = rsi(pd.Series(closes, dtype=float), 2)
    assert r.iloc[26] == pytest.approx(20.0)
    assert r.iloc[27] == pytest.approx(100 * 0.25 / 3.25)
    assert sma(pd.Series(closes, dtype=float), 20).iloc[27] == pytest.approx(116.75)
    expected_entry = [F] * 29
    expected_entry[27] = T
    assert out["entry"].tolist() == expected_entry
    assert out["stop_price"].iloc[27] == pytest.approx(105.0)
    assert out["rank"].iloc[27] == pytest.approx(-100 * 0.25 / 3.25)
    expected_exit = [F] + [T] * 25 + [F, F, T]
    assert out["exit"].tolist() == expected_exit


def test_case_r2_trend_filter_fails():
    closes = list(range(100, 126)) + [121, 113, 120]
    out = SIGNAL_STRATEGIES["rsi2_etf"](rsi_bars(closes), R_PARAMS)
    from tlab.indicators import rsi, sma

    s = pd.Series(closes, dtype=float)
    assert rsi(s, 2).iloc[27] == pytest.approx(100 * 0.25 / 5.25)  # ≈ 4,76
    assert sma(s, 20).iloc[27] == pytest.approx(116.55)
    assert not out["entry"].any()


def test_case_r3_extremes_no_nan_true():
    out = SIGNAL_STRATEGIES["rsi2_etf"](rsi_bars(list(range(100, 160))), R_PARAMS)
    assert not out["entry"].any()
    assert out["entry"].dtype == bool and out["exit"].dtype == bool
    # Serie plana: RSI = 0/0 = NaN → nunca entrada ni salida
    flat = SIGNAL_STRATEGIES["rsi2_etf"](rsi_bars([100.0] * 40), R_PARAMS)
    assert not flat["entry"].any() and not flat["exit"].any()


# ---------------------------------------------------------------- §6.4 sizing y tope equity/3
def _limit(qty, price, costs, cap=0.3333, ac="equity"):
    return apply_limits(qty, price, costs, 10_000, 10_000, 0.0, 0, 3, 1.0, ac, False, cap)


def test_cap_ief():
    q = position_size(10_000, 95, 93.20, 0.01, ETF)
    assert q == 52
    assert _limit(q, 95, ETF, cap=None) == 52
    assert _limit(q, 95, ETF) == 35


def test_cap_spy():
    q = position_size(10_000, 600, 576, 0.01, ETF)
    assert q == 4 and _limit(q, 600, ETF) == 4
    q = position_size(10_000, 600, 588, 0.01, ETF)
    assert q == 7 and _limit(q, 600, ETF) == 5


def test_sizing_crypto_example():
    q = position_size(10_000, 100_000, 93_000, 0.01, CRYPTO, "crypto")
    assert q == pytest.approx(0.012708, abs=1e-9)
    assert _limit(q, 100_000, CRYPTO, ac="crypto") == pytest.approx(0.012708, abs=1e-9)


def test_sizing_gld_and_qqq_examples():
    assert position_size(10_000, 380, 363.20, 0.01, ETF) == 5
    assert position_size(10_000, 500, 479, 0.01, ETF) == 4


def test_simulator_applies_position_cap():
    """Con stop muy cercano el riesgo pediría casi todo el equity; el tope lo deja en ~1/3."""
    b = make_bars(30, seed=1, vol=0.001)
    s = manual_signals(b.index, entries=[2], stop=b["close"] * 0.995)
    cfg = SimConfig(costs={"equity": ETF, "crypto": CRYPTO}, max_position_fraction=0.3333)
    r = simulate({"SPY": b}, {"SPY": s}, cfg)
    assert len(r.trades) >= 1
    assert r.exposure.max() <= 0.3333 * 1.02  # holgura por la variación del precio
    r2 = simulate({"SPY": b}, {"SPY": s}, SimConfig(costs={"equity": ETF, "crypto": CRYPTO}))
    assert r2.exposure.max() > 0.5


# ---------------------------------------------------------------- informes P1 y robustez
def test_kill_switch_episodes_reset_peak():
    idx = pd.date_range("2024-01-01", periods=8, freq="D", tz="UTC")
    eq = pd.Series([100, 110, 98, 97, 100, 86, 90, 89], index=idx, dtype=float)
    eps = kill_switch_episodes(eq, 0.10)
    # 98 < 110×0,9=99 → episodio 1 (máximo pasa a 98); luego máx 100 → 86 < 90 → episodio 2.
    assert eps == [idx[2], idx[5]]
    assert kill_switch_episodes(pd.Series([100.0, 91.0], index=idx[:2]), 0.10) == []


def test_calibrate_risk():
    lim = 0.10  # R2-2: el límite ya no tiene valor por defecto
    assert calibrate_risk({0.01: -0.15, 0.0075: -0.099, 0.005: -0.07}, lim) == 0.0075
    assert calibrate_risk({0.01: -0.08, 0.0075: -0.06, 0.005: -0.04}, lim) == 0.01
    assert calibrate_risk({0.01: -0.30, 0.0075: -0.2, 0.005: -0.11}, lim) is None


def _trades():
    d = pd.Timestamp
    return pd.DataFrame(
        {
            "symbol": ["BTC/USD", "BTC/USD", "ETH/USD", "LTC/USD"],
            "entry_date": [d("2019-01-05", tz="UTC"), d("2020-03-01", tz="UTC"),
                           d("2019-06-30", tz="UTC"), d("2021-01-01", tz="UTC")],
            "pnl_usd": [500.0, -100.0, 50.0, -80.0],
            "pnl_r": [5.0, -1.0, 0.5, -0.8],
        }
    )  # fmt: skip


def test_drop_best_asset_and_by_asset():
    best, rest = drop_best_asset(_trades())
    assert best == "BTC/USD" and rest == pytest.approx(-30.0)
    ba = expectancy_by_asset(_trades())
    assert ba.loc["BTC/USD", "trades"] == 2 and ba.loc["BTC/USD", "expectancy_r"] == 2.0


def test_expectancy_by_period_uses_entry_date():
    u = lambda x: pd.Timestamp(x, tz="UTC")  # noqa: E731
    per = [(u("2015-10-01"), u("2019-06-30")), (u("2019-07-01"), u("2023-02-28"))]
    rows = expectancy_by_period(_trades(), per)
    assert [r["trades"] for r in rows] == [2, 2]
    assert rows[0]["expectancy_r"] == pytest.approx(2.75)


def test_fixed_windows_etf_and_crypto():
    w = fixed_windows(pd.Timestamp("2007-07-01", tz="UTC"), "2013-01-01", 12, 8, "2020-12-31")
    assert [x.test_start.year for x in w] == list(range(2013, 2021))
    assert all(x.train_start == pd.Timestamp("2007-07-01", tz="UTC") for x in w)
    assert w[0].train_end.date().isoformat() == "2012-12-31"
    c = fixed_windows(pd.Timestamp("2015-10-01", tz="UTC"), "2019-01-01", 9, 6, "2023-06-30")
    got = [(x.test_start.date().isoformat(), x.test_end.date().isoformat()) for x in c]
    assert got[0] == ("2019-01-01", "2019-09-30")
    assert got[1] == ("2019-10-01", "2020-06-30")
    assert got[-1] == ("2022-10-01", "2023-06-30")
    with pytest.raises(ValueError):
        fixed_windows(pd.Timestamp("2015-10-01", tz="UTC"), "2019-01-01", 9, 5, "2023-06-30")


def test_pick_best_tie_goes_to_default():
    d = {"a": 10, "b": 2.0}
    scored = [({"a": 8, "b": 2.0}, 1.0), ({"a": 10, "b": 2.0}, 1.0), ({"a": 12, "b": 1.5}, 0.5)]
    assert pick_best(scored, d, ["a", "b"]) == {"a": 10, "b": 2.0}
    scored = [({"a": 8, "b": 2.0}, float("nan")), ({"a": 12, "b": 2.5}, 0.1)]
    assert pick_best(scored, d, ["a", "b"]) == {"a": 12, "b": 2.5}


# ---------------------------------------------------------------- configuración pre-registrada
EXPECTED = {
    "donchian_crypto": (
        ["BTC/USD", "ETH/USD", "LTC/USD", "BCH/USD"], "BTC/USD", "2015-10-01", "2023-06-30",
        {"entry_n": 55, "exit_n": 20, "atr_mult": 2.0, "atr_n": 20},
        {"entry_n": [41, 55, 69], "exit_n": [15, 20, 25], "atr_mult": [1.5, 2.0, 2.5]},
    ),
    "donchian_etf": (
        ["SPY", "EFA", "EEM", "IEF", "GLD", "DBC", "VNQ"], "SPY", "2007-07-01", "2020-12-31",
        {"entry_n": 55, "exit_n": 20, "atr_mult": 2.0, "atr_n": 20},
        {"entry_n": [41, 55, 69], "exit_n": [15, 20, 25], "atr_mult": [1.5, 2.0, 2.5]},
    ),
    "tsmom_etf": (
        ["SPY", "EFA", "EEM", "IEF", "GLD", "DBC", "VNQ"], "SPY", "2007-07-01", "2020-12-31",
        {"lookback": 252, "atr_mult": 4.0, "atr_n": 20},
        {"lookback": [189, 252, 315], "atr_mult": [3.0, 4.0, 5.0]},
    ),
    "rsi2_etf": (
        ["SPY", "QQQ", "IWM", "DIA", "EFA", "EEM"], "SPY", "2007-07-01", "2020-12-31",
        {"rsi_n": 2, "rsi_entry": 10.0, "trend_n": 200, "exit_sma_n": 5, "atr_mult": 3.0,
         "atr_n": 20},
        {"rsi_entry": [7.5, 10.0, 12.5], "exit_sma_n": [4, 5, 6], "atr_mult": [2.25, 3.0, 3.75]},
    ),
}  # fmt: skip


@pytest.mark.parametrize("sid", CANDIDATES)
def test_candidate_toml_matches_hipotesis(sid):
    sc = load_strategy_config(sid)
    uni, bench, start, is_end, params, grid = EXPECTED[sid]
    # Tras el veredicto del paso 3 el status cambia, pero lo pre-registrado no.
    assert sc["status"] in ("preregistrada", "rechazada", "aprobada_paper") and sc["id"] == sid
    assert sc["universe"] == uni and sc["benchmark"] == bench
    assert (sc["start"], sc["is_end"], sc["end"]) == (start, is_end, "2026-10-31")
    assert sc["params"] == params
    assert sc["data_source"] == "yfinance"
    assert sc["min_history_bars"] == 365 and sc["kill_switch_in_backtest"] is False
    assert sc["risk_levels"] == [0.01, 0.0075, 0.005] and sc["risk_per_trade"] <= 0.01
    g = param_grid(sc["params"], sc["robust_keys"])
    for k, vals in grid.items():
        assert sorted({p[k] for p in g}) == pytest.approx(vals)
    assert len(g) + len(sc.get("extra_variants", [])) + 2 <= 40  # presupuesto §3
    assert sid in SIGNAL_STRATEGIES


def test_settings_paso2():
    with open(CONFIG_DIR / "settings.toml", "rb") as f:
        s = tomllib.load(f)
    assert s["costs"]["crypto"]["slippage_bps"] == 20
    assert s["costs"]["crypto"]["fee_rate"] == 0.0025
    assert s["costs"]["equity"]["slippage_bps"] == 5 and s["costs"]["stress"]["multiplier"] == 2
    assert math.isclose(s["risk"]["max_position_fraction"], 0.3333)
    for sym in ("DBC", "VNQ", "DIA"):
        assert sym in s["universe"]["equity"]
    for sym in ("LTC/USD", "BCH/USD"):
        assert sym in s["universe"]["crypto"]


def test_risk_never_above_one_pct_with_cap():
    rng = np.random.default_rng(7)
    for _ in range(200):
        price = float(rng.uniform(20, 700))
        stop = price * float(rng.uniform(0.80, 0.995))
        q = position_size(10_000, price, stop, 0.01, ETF)
        q = _limit(q, price, ETF)
        loss = q * (ETF.fill_price(price, "buy") - ETF.fill_price(stop, "sell"))
        assert loss <= 100 + 1e-9
        assert q * ETF.fill_price(price, "buy") <= 3333 + 1e-6


# ---------------------------------------------------------------- runner con datos sintéticos
def _synthetic_candidate():
    from tlab.backtest.runner import OOSGuardError  # noqa: F401

    data = {s: make_bars(1500, seed=i, start="2010-01-01") for i, s in
            enumerate(["SPY", "EFA", "IEF"])}  # fmt: skip
    data["GLD"] = make_bars(1200, seed=9, start="2011-03-01")  # entra más tarde
    sc = {
        "id": "donchian_etf",
        "status": "preregistrada",
        "universe": ["SPY", "EFA", "GLD"],
        "benchmark": "SPY",
        "benchmark_info": {"SPY": 0.6, "IEF": 0.4},
        "robust_keys": ["entry_n"],
        "start": "2011-06-01",
        "is_end": "2014-12-31",
        "end": "2015-06-30",
        "min_history_bars": 365,
        "risk_per_trade": 0.01,
        "risk_levels": [0.01, 0.0075, 0.005],
        "calibration_dd_limit": 0.10,
        "kill_switch_in_backtest": False,
        "subperiods": [["2011-06-01", "2012-12-31"], ["2013-01-01", "2015-06-30"]],
        "walkforward": {"first_test": "2013-01-01", "test_months": 12, "n_windows": 2,
                        "min_valid_windows": 1},
        "params": {"entry_n": 20, "exit_n": 10, "atr_mult": 2.0, "atr_n": 20},
    }  # fmt: skip
    return data, sc


def test_runner_candidate_is_wf_robust(tmp_path, settings):
    from tlab.backtest.runner import run_backtest

    data, sc = _synthetic_candidate()
    kw = dict(data=data, reports_dir=tmp_path / "reports", registry=tmp_path / "reg.md",
              settings=settings, strat_cfg=sc)  # fmt: skip
    p = run_backtest("donchian_etf", "is", **kw)
    txt = p.read_text()
    for sec in (
        "Calibración del riesgo en IS",
        "Kill switch (P1)",
        "Sin las 5 mejores",
        "Sin el mejor activo",
        "Subperiodos",
        "Por activo",
        "Benchmark informativo",
        "Kill switch **desactivado**",
        "GLD entra al universo el",
    ):
        assert sec in txt, sec
    eq = pd.read_csv(p.parent / "equity.csv", index_col=0, parse_dates=True)
    assert eq.index.max() <= pd.Timestamp("2014-12-31", tz="UTC")
    tr = pd.read_csv(p.parent / "trades.csv", parse_dates=["entry_date"])
    gld = tr[tr["symbol"] == "GLD"]
    if len(gld):
        assert gld["entry_date"].min() > data["GLD"].index[364]
    reg = (tmp_path / "reg.md").read_text()
    assert reg.count("calibración de riesgo") == 2  # 0,75 % y 0,5 % (1 % es la principal)
    assert "risk_per_trade=0.01" in reg and "sin kill switch" in reg
    p = run_backtest("donchian_etf", "wf", **kw)
    txt = p.read_text()
    assert "Walk-forward IS" in txt and "2014-01-01 → 2014-12-31" in txt
    assert "2015-" not in txt.split("Walk-forward IS")[1]
    p = run_backtest("donchian_etf", "robust", **kw)
    assert "Criterio 6" in p.read_text()
    assert reg.count("|") < (tmp_path / "reg.md").read_text().count("|")


def test_runner_entry_delay_option(tmp_path, settings):
    from tlab.backtest.runner import run_backtest

    data, sc = _synthetic_candidate()
    kw = dict(data=data, reports_dir=tmp_path / "reports", registry=tmp_path / "reg.md",
              settings=settings, strat_cfg=sc)  # fmt: skip
    base = run_backtest("donchian_etf", "is", **kw)
    late = run_backtest("donchian_etf", "is", entry_delay=1, **kw)
    assert "_delay1_" in late.parent.name and late.parent != base.parent
    assert "retraso 1 vela" in (tmp_path / "reg.md").read_text()
    t0 = pd.read_csv(base.parent / "trades.csv")
    t1 = pd.read_csv(late.parent / "trades.csv")
    if len(t0) and len(t1):  # con retraso, la primera entrada no puede ser anterior
        assert t1["entry_date"].min() > t0["entry_date"].min()


@pytest.mark.parametrize("mode", ["oos", "full"])
def test_runner_candidate_oos_and_full_are_locked(tmp_path, settings, mode):
    from tlab.backtest.runner import OOSGuardError, run_backtest

    data, sc = _synthetic_candidate()
    with pytest.raises(OOSGuardError):
        run_backtest("donchian_etf", mode, data=data, reports_dir=tmp_path / "r",
                     registry=tmp_path / "reg.md", settings=settings, strat_cfg=sc)  # fmt: skip
    assert not (tmp_path / "reg.md").exists()


def test_mix_benchmark_monthly_rebalance(settings):
    from tlab.backtest.costs import cost_models
    from tlab.backtest.runner import mix_benchmark_equity

    data = {"BTC/USD": make_bars(400, seed=3, freq="D", start="2021-01-01")}
    a, b = data["BTC/USD"].index[0], data["BTC/USD"].index[-1]
    eq = mix_benchmark_equity(data, {"BTC/USD": 0.5}, cost_models(settings), a, b, 10_000)
    bh = data["BTC/USD"]["close"]
    # Con 50 % en caja, la volatilidad diaria es ~la mitad que la de BTC.
    ratio = eq.pct_change().std() / bh.pct_change().std()
    assert 0.35 < ratio < 0.65
    from tlab.backtest.allocation_sim import simulate_weights
    from tlab.strategies.allocation import monthly_closes

    m = monthly_closes(pd.DataFrame({"BTC/USD": bh}))
    w = pd.DataFrame({"BTC/USD": 0.5}, index=m.index)
    _, tr = simulate_weights(data, w, cost_models(settings), 10_000, always_rebalance=True)
    assert len(tr) >= len(m) - 2  # rebalancea casi todos los meses
    _, tr0 = simulate_weights(data, w, cost_models(settings), 10_000)
    assert len(tr0) == 1  # sin el flag, pesos constantes = una sola compra


def test_targets_follow_candidate_toml(settings):
    """Las herramientas de robustez (azar, rejilla, Monte Carlo) usan el mismo periodo,
    entrada por activo, riesgo y tope que el runner."""
    from tlab.backtest.targets import build_target

    data, sc = _synthetic_candidate()
    t = build_target("donchian_etf", data=data, settings=settings, strat_cfg=sc, kill_switch=False)
    a, b = t.window("is")
    assert a == pd.Timestamp("2011-06-01", tz="UTC") and b == pd.Timestamp("2014-12-31", tz="UTC")
    assert t.cfg.max_position_fraction == pytest.approx(0.3333)
    assert t.entry_from["GLD"] == data["GLD"].index[364]
    assert t.sliced_bars("is")["GLD"].index[0] == data["GLD"].index[364]
    out = t.run(sc["params"], "is")
    assert out.equity.index[0] >= a and out.equity.index[-1] <= b
