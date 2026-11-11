"""Métricas, walk-forward, OOS guard, caché, validación, guardia, informes, motores."""

import numpy as np
import pandas as pd
import pytest
from conftest import flat_bars, make_bars, manual_signals

from tlab import metrics
from tlab.backtest.costs import CostModel
from tlab.backtest.portfolio_sim import SimConfig, simulate
from tlab.backtest.runner import OOSGuardError, check_oos_guard, run_backtest
from tlab.backtest.walkforward import make_windows
from tlab.broker.guard import LiveTradingRefused, assert_paper_only
from tlab.data.loader import load_bars
from tlab.data.validate import validate_bars
from tlab.report import REQUIRED_SECTIONS


def test_metrics_known_values():
    idx = pd.date_range("2020-01-01", periods=5, freq="D", tz="UTC")
    eq = pd.Series([100, 110, 99, 121, 121.0], index=idx)
    assert metrics.max_drawdown(eq) == pytest.approx(-0.10)
    assert metrics.total_return(eq) == pytest.approx(0.21)
    r = np.array([0.10, -0.10, 121 / 99 - 1, 0.0])
    assert metrics.sharpe(eq, 252) == pytest.approx(r.mean() / r.std(ddof=1) * np.sqrt(252))
    idx2 = pd.to_datetime(["2020-01-01", "2022-01-01"]).tz_localize("UTC")
    eq2 = pd.Series([100.0, 121.0], index=idx2)
    yrs = (idx2[1] - idx2[0]).days / 365.25
    assert metrics.cagr(eq2) == pytest.approx(1.21 ** (1 / yrs) - 1)
    tr = pd.DataFrame(
        {
            "pnl_usd": [100, -50, 30, -20.0],
            "pnl_r": [2, -1, 0.6, -0.4],
            "entry_date": idx[:4],
            "exit_date": idx[1:],
        }
    )
    st = metrics.trade_stats(tr)
    assert st["expectancy_usd"] == pytest.approx(15.0)
    assert st["expectancy_r"] == pytest.approx(0.3)
    assert st["win_rate"] == pytest.approx(0.5)
    assert st["profit_factor"] == pytest.approx(130 / 70)


def test_engines_agree_single_asset():
    """Sin límites de cartera y stop lejano: mismo nº de operaciones y < 0,5 pp.

    Con stops cercanos los motores difieren (documentado en docs/PREP_NOTES.md):
    (1) vectorbt no aplica slippage a la salida por stop; portfolio_sim sí (más pesimista);
    (2) si en la misma vela hay salida por señal (a la apertura) y el low toca el stop,
    vectorbt da prioridad al stop; portfolio_sim sale antes, a la apertura (orden real).
    Por eso el caso con stops solo exige el mismo nº de operaciones.
    """
    from tlab.backtest.vbt_engine import run_single
    from tlab.strategies.demo_sma import generate_signals

    b = make_bars(1500, seed=7, vol=0.01)
    cm = CostModel(slippage_bps=5)
    cfg = SimConfig(
        risk_per_trade=1e9,
        max_positions=1,
        kill_switch_drawdown=None,
        allow_fractional=True,
        costs={"equity": cm, "crypto": cm},
    )
    for atr_mult, tol in ((50.0, 0.005), (3.0, None)):
        sig = generate_signals(b, {"fast": 10, "slow": 40, "atr_mult": atr_mult})
        sig["stop_price"] = sig["stop_price"].clip(lower=0.01)
        r = simulate({"SPY": b}, {"SPY": sig}, cfg)
        pf = run_single(b, sig, cm)
        assert len(r.trades) == int(pf.trades.count())
        if tol is not None:
            diff = abs(metrics.total_return(r.equity) - float(pf.total_return()))
            assert diff < tol, diff


def test_walkforward_windows():
    w = make_windows("2010-01-01", "2020-01-01", 5)
    assert len(w) == 5
    assert w[0].test_start == w[0].train_end
    for a, b in zip(w, w[1:], strict=False):
        assert b.test_start == a.test_end  # contiguas, sin solape
        assert a.train_start < a.train_end <= a.test_start
    assert w[-1].test_end == pd.Timestamp("2020-01-01")
    assert w[0].test_start == pd.Timestamp("2015-01-01") or w[0].test_start < pd.Timestamp(
        "2015-01-02"
    )


def test_oos_guard(tmp_path):
    log = tmp_path / "oos_log.csv"
    with pytest.raises(OOSGuardError):
        check_oos_guard(log, "x", {"a": 1}, confirm=False, force=False)
    check_oos_guard(log, "x", {"a": 1}, confirm=True, force=False)
    check_oos_guard(log, "x", {"a": 1}, confirm=True, force=False)  # mismos params: OK
    with pytest.raises(OOSGuardError):
        check_oos_guard(log, "x", {"a": 2}, confirm=True, force=False)
    check_oos_guard(log, "x", {"a": 2}, confirm=True, force=True)
    assert "True" in log.read_text()  # el --force queda anotado


class CountingSource:
    name, adjustment, feed = "fake", "all", "test"

    def __init__(self):
        self.calls = 0

    def fetch(self, symbol, timeframe, start, end, asset_class):
        self.calls += 1
        b = make_bars(3000, start="2010-01-01")
        return b[(b.index >= start) & (b.index <= end)]


def test_cache_no_network(tmp_path):
    src = CountingSource()
    a = load_bars(["SPY"], start="2012-01-01", end="2015-01-01", source=src, cache_dir=tmp_path)
    assert src.calls == 1
    b = load_bars(["SPY"], start="2012-01-01", end="2015-01-01", source=src, cache_dir=tmp_path)
    assert src.calls == 1  # segunda carga idéntica: cero red
    pd.testing.assert_frame_equal(a["SPY"], b["SPY"], check_freq=False)
    load_bars(["SPY"], start="2012-01-01", end="2016-01-01", source=src, cache_dir=tmp_path)
    assert src.calls == 2  # incremental: solo lo que falta
    c = load_bars(["SPY"], start="2013-01-01", end="2014-01-01", source=src, cache_dir=tmp_path)
    assert src.calls == 2 and c["SPY"].index.tz is not None


def test_validate_bars():
    b = flat_bars([(100, 101, 99, 100)] * 10)
    assert validate_bars(b) == []
    bad = b.copy()
    bad.iloc[2, bad.columns.get_loc("high")] = 90  # high < open
    bad.iloc[3, bad.columns.get_loc("low")] = 105  # low > close
    issues = " ".join(validate_bars(bad))
    assert "high" in issues and "low" in issues
    gap = b.drop(b.index[4:8])
    assert any("huecos" in i for i in validate_bars(gap))
    nan = b.copy()
    nan.iloc[1, 0] = np.nan
    assert any("NaN" in i for i in validate_bars(nan))
    crypto = make_bars(30, freq="D").drop(pd.Timestamp("2015-01-10", tz="UTC"))
    assert any("huecos" in i for i in validate_bars(crypto, "crypto"))


def test_guard_paper_only():
    ok = {"ALPACA_PAPER_TRADE": "true"}
    assert_paper_only(ok)
    assert_paper_only(ok, base_url="https://paper-api.alpaca.markets/v2")
    for env in ({"ALPACA_PAPER_TRADE": "false"}, {}, {"ALPACA_PAPER_TRADE": "True "}):
        with pytest.raises(LiveTradingRefused):
            assert_paper_only(env)
    with pytest.raises(LiveTradingRefused):
        assert_paper_only(ok, base_url="https://api.alpaca.markets")
    with pytest.raises(LiveTradingRefused):
        assert_paper_only({**ok, "APCA_API_BASE_URL": "https://api.alpaca.markets"})
    with pytest.raises(LiveTradingRefused):
        assert_paper_only(ok, paper=False)


def test_report_sections(tmp_path, settings):
    data = {
        "SPY": make_bars(900, seed=1),
        "QQQ": make_bars(900, seed=2),
        "IWM": make_bars(900, seed=5),
    }
    sc = {
        "id": "demo_sma",
        "status": "demo",
        "universe": ["SPY", "QQQ", "IWM"],
        "benchmark": "SPY",
        "params": {"fast": 10, "slow": 30, "atr_mult": 2.0, "atr_n": 14},
        "robust_keys": ["fast"],
    }
    p = run_backtest(
        "demo_sma",
        "full",
        data=data,
        reports_dir=tmp_path / "reports",
        registry=tmp_path / "reg.md",
        settings=settings,
        strat_cfg=sc,
    )
    txt = p.read_text()
    for sec in REQUIRED_SECTIONS:
        assert sec in txt
    assert "| Métrica | Estrategia | Benchmark |" in txt and "| Sharpe |" in txt
    assert (p.parent / "trades.csv").exists() and (p.parent / "equity.csv").exists()
    assert "demo_sma" in (tmp_path / "reg.md").read_text()
    for mode in ("is", "wf", "robust"):
        run_backtest(
            "demo_sma",
            mode,
            data=data,
            reports_dir=tmp_path / "reports",
            registry=tmp_path / "reg.md",
            settings=settings,
            strat_cfg=sc,
        )
    with pytest.raises(OOSGuardError):
        run_backtest(
            "demo_sma",
            "oos",
            data=data,
            reports_dir=tmp_path / "reports",
            registry=tmp_path / "reg.md",
            settings=settings,
            strat_cfg=sc,
        )


def test_simulator_mixed_calendars():
    """Acción (L-V) + cripto (7 días): las señales del viernes se ejecutan el lunes."""
    eq = make_bars(200, seed=1, freq="B", vol=0.002)
    cr = make_bars(280, seed=2, freq="D", vol=0.002)
    s_eq = manual_signals(eq.index, entries=[1], stop=eq["close"] * 0.5)  # 1 = viernes
    s_cr = manual_signals(cr.index, entries=[], stop=np.nan)
    cm = CostModel(slippage_bps=5)
    r = simulate(
        {"SPY": eq, "BTC/USD": cr},
        {"SPY": s_eq, "BTC/USD": s_cr},
        SimConfig(costs={"equity": cm, "crypto": cm}),
    )
    assert eq.index[1].day_of_week == 4
    assert r.trades.iloc[0].entry_date == eq.index[2]  # lunes
    assert r.n_open.max() == 1
