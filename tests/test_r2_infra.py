"""R2-6: señales de panel (infraestructura): as_panel, resolve_signal_fn e integración en runner."""

from __future__ import annotations

import pandas as pd
import pytest
from conftest import make_bars

import tlab.strategies as strategies
from tlab.backtest.portfolio_sim import simulate
from tlab.backtest.runner import make_cfg, run_backtest
from tlab.strategies import resolve_signal_fn, tsmom_etf
from tlab.strategies.base import as_panel


def _bars(n=5):
    return {
        s: make_bars(600, seed=i) for i, s in enumerate(["SPY", "EFA", "IEF", "GLD", "DBC"][:n])
    }


def test_as_panel_equivale_a_llamar_simbolo_a_simbolo():
    bars = _bars()
    p = {"lookback": 126, "atr_mult": 4.0, "atr_n": 20}
    got = as_panel(tsmom_etf.generate_signals)(bars, p)
    assert set(got) == set(bars)
    for s, df in bars.items():
        pd.testing.assert_frame_equal(got[s], tsmom_etf.generate_signals(df, p))


def test_resolve_por_activo_y_desconocida():
    fn = resolve_signal_fn("tsmom_etf")
    out = fn(_bars(2), {"lookback": 126, "atr_mult": 4.0, "atr_n": 20})
    assert set(out) == {"SPY", "EFA"}
    with pytest.raises(KeyError):
        resolve_signal_fn("no_existe")


def test_resolve_panel_se_devuelve_tal_cual(monkeypatch):
    def fake(bars, params):
        return {s: tsmom_etf.generate_signals(df, params) for s, df in bars.items()}

    monkeypatch.setitem(strategies.PANEL_STRATEGIES, "fake_panel", fake)
    assert resolve_signal_fn("fake_panel") is fake
    assert strategies.is_signal_strategy("fake_panel")


def test_sessions_se_inyecta_en_copia(monkeypatch):
    seen = {}

    def needs(df, params):
        seen["p"] = params
        return tsmom_etf.generate_signals(df, {"lookback": 5, "atr_mult": 2.0, "atr_n": 2})

    monkeypatch.setitem(strategies.SIGNAL_STRATEGIES, "needs_s", needs)
    monkeypatch.setattr(strategies, "NEEDS_SESSIONS", ("needs_s",))
    with pytest.raises(ValueError):
        resolve_signal_fn("needs_s")
    idx = pd.DatetimeIndex(["2024-01-02"], tz="UTC")
    mine = {"x": 1}
    resolve_signal_fn("needs_s", idx)({"A": make_bars(30)}, mine)
    assert "sessions" in seen["p"] and "sessions" not in mine


def test_runner_donchian_etf_igual_que_simbolo_a_simbolo(tmp_path, settings):
    """El cambio a panel no altera las operaciones de la ronda 1 (aceptación de R2-6)."""
    from test_candidates import _synthetic_candidate

    data, sc = _synthetic_candidate()
    out = run_backtest(
        "donchian_etf",
        "is",
        data=data,
        reports_dir=tmp_path / "reports",
        registry=tmp_path / "reg.md",
        settings=settings,
        strat_cfg=sc,
    )
    got = pd.read_csv(out.parent / "trades.csv")
    assert len(got) > 0
    # Referencia: el camino antiguo (una llamada por activo) sobre las mismas velas.
    from tlab.backtest.costs import cost_models
    from tlab.backtest.runner import asset_entry_dates
    from tlab.strategies.donchian_atr import generate_signals

    bars = {k: data[k] for k in sc["universe"]}
    cfg = make_cfg(settings, sc, cost_models(settings, "base"))
    ef = asset_entry_dates(bars, 365)
    a, b = pd.Timestamp(sc["start"], tz="UTC"), pd.Timestamp(sc["is_end"], tz="UTC")
    bb = {s: df[(df.index >= max(a, ef[s])) & (df.index <= b)] for s, df in bars.items()}
    ss = {s: generate_signals(bars[s], sc["params"]).loc[bb[s].index[0] : b] for s in bb}
    ref = simulate(bb, ss, cfg).trades
    assert len(ref) == len(got)
    assert list(ref["symbol"]) == list(got["symbol"])
    assert ref["pnl_usd"].to_numpy() == pytest.approx(got["pnl_usd"].to_numpy())
