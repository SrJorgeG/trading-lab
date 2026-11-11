"""Ejecución, stops, costes, sizing, límites y kill switch del simulador."""

import numpy as np
import pandas as pd
import pytest
from conftest import flat_bars, make_bars, manual_signals

from tlab.backtest.costs import CostModel
from tlab.backtest.portfolio_sim import SimConfig, simulate
from tlab.risk import check_kill_switch, position_size, risk_per_unit

EQ = CostModel(slippage_bps=5)


def cfg(**kw):
    base = {"costs": {"equity": EQ, "crypto": CostModel(slippage_bps=10, fee_rate=0.0025)}}
    base.update(kw)
    return SimConfig(**base)


def test_execution_next_open():
    b = flat_bars([(100, 101, 99, 100)] * 3 + [(105, 106, 104, 105)] + [(105, 106, 104, 105)] * 3)
    s = manual_signals(b.index, entries=[2], exits=[4], stop=50.0)
    r = simulate({"SPY": b}, {"SPY": s}, cfg(risk_per_trade=0.5))
    tr = r.trades.iloc[0]
    assert tr.entry_date == b.index[3]
    assert tr.entry_price == pytest.approx(105 * 1.0005)
    assert tr.exit_date == b.index[5]
    assert tr.exit_price == pytest.approx(105 * 0.9995)


def test_stop_intrabar_and_gap():
    # Intrabar: entra en vela 1 a 100, en vela 2 low=94 <= stop 95 -> sale a 95.
    b = flat_bars([(100, 101, 99, 100), (100, 101, 99, 100), (99, 100, 94, 97), (97, 98, 96, 97)])
    s = manual_signals(b.index, entries=[0], stop=95.0)
    tr = simulate({"SPY": b}, {"SPY": s}, cfg()).trades.iloc[0]
    assert tr.exit_reason == "stop" and tr.exit_price == pytest.approx(95 * 0.9995)
    # Gap: la vela 2 abre a 90 (< stop 95) -> sale a la apertura (90).
    b2 = flat_bars([(100, 101, 99, 100), (100, 101, 99, 100), (90, 92, 88, 91), (91, 92, 90, 91)])
    tr2 = simulate({"SPY": b2}, {"SPY": s}, cfg()).trades.iloc[0]
    assert tr2.exit_reason == "stop_gap" and tr2.exit_price == pytest.approx(90 * 0.9995)
    # Stop y objetivo en la misma vela -> gana el stop.
    b3 = flat_bars(
        [(100, 101, 99, 100), (100, 101, 99, 100), (100, 120, 94, 100), (100, 101, 99, 100)]
    )
    s3 = s.copy()
    s3["target_price"] = 115.0
    tr3 = simulate({"SPY": b3}, {"SPY": s3}, cfg()).trades.iloc[0]
    assert tr3.exit_reason == "stop"
    # Solo objetivo -> sale al objetivo.
    b4 = flat_bars([(100, 101, 99, 100), (100, 101, 99, 100), (100, 120, 99, 100)])
    tr4 = simulate({"SPY": b4}, {"SPY": s3}, cfg()).trades.iloc[0]
    assert tr4.exit_reason == "target" and tr4.exit_price == pytest.approx(115 * 0.9995)


def test_costs_applied_both_sides(settings):
    b = flat_bars([(100, 101, 99, 100)] * 2 + [(110, 111, 109, 110)] * 3)
    s = manual_signals(b.index, entries=[0], exits=[2], stop=40.0)
    c0 = SimConfig(costs={"equity": CostModel(), "crypto": CostModel()}, risk_per_trade=0.01)
    c1 = cfg(risk_per_trade=0.01)
    c2 = cfg(risk_per_trade=0.01, costs={"equity": EQ.scaled(2), "crypto": CostModel()})
    t0, t1, t2 = (simulate({"SPY": b}, {"SPY": s}, c).trades.iloc[0] for c in (c0, c1, c2))
    assert t0.qty == t1.qty == t2.qty == 1
    # A mano: entrada a 100 (apertura vela 1), salida a 110 (apertura vela 3).
    assert t0.pnl_usd == pytest.approx(10.0)
    cost1 = 100 * 0.0005 + 110 * 0.0005
    assert t0.pnl_usd - t1.pnl_usd == pytest.approx(cost1)
    assert t0.pnl_usd - t2.pnl_usd == pytest.approx(2 * cost1)
    # Cripto con comisión porcentual, en ambos lados.
    cc = CostModel(slippage_bps=10, fee_rate=0.0025)
    e, x = 100 * 1.001, 110 * 0.999
    assert cc.commission(1, e) + cc.commission(1, x) == pytest.approx((e + x) * 0.0025)


@pytest.mark.parametrize("seed", range(20))
def test_position_size_risk_cap(seed):
    rng = np.random.default_rng(seed)
    eq = float(rng.uniform(1_000, 100_000))
    entry = float(rng.uniform(5, 600))
    stop = entry * float(rng.uniform(0.80, 0.999))
    for cm, ac in ((EQ, "equity"), (CostModel(slippage_bps=10, fee_rate=0.0025), "crypto")):
        q = position_size(eq, entry, stop, 0.01, cm, ac)
        assert q >= 0
        assert q * risk_per_unit(entry, stop, cm) <= 0.01 * eq + 1e-9
        if ac == "equity":
            assert q == int(q)
            assert (q + 1) * risk_per_unit(entry, stop, cm) > 0.01 * eq  # redondeo abajo
    assert position_size(1000, 500, 100, 0.01, EQ) == 0  # 1 acción ya arriesga > 10 $
    assert position_size(1000, 100, 101, 0.01, EQ) == 0  # stop por encima: no hay operación
    # Cantidad 0 -> no hay operación en el simulador.
    b = flat_bars([(500, 501, 499, 500)] * 4)
    s = manual_signals(b.index, entries=[0], stop=100.0)
    r = simulate({"SPY": b}, {"SPY": s}, cfg(initial_equity=1000))
    assert r.trades.empty and (r.n_open == 0).all()


def test_max_positions():
    syms = [f"S{i:02d}" for i in range(10)]
    bars = {s: make_bars(300, seed=i, vol=0.002) for i, s in enumerate(syms)}
    sigs = {}
    for s, b in bars.items():
        sg = manual_signals(
            b.index, entries=list(range(0, 300, 7)), stop=b["close"] * 0.9, rank=1.0
        )
        sigs[s] = sg
    r = simulate(bars, sigs, cfg(kill_switch_drawdown=None))
    assert r.n_open.max() <= 3
    first = r.trades.sort_values(["entry_date", "symbol"]).head(3)
    assert list(first.symbol) == ["S00", "S01", "S02"]  # empate -> orden alfabético
    r2 = simulate(bars, sigs, cfg(kill_switch_drawdown=None))
    pd.testing.assert_frame_equal(r.trades, r2.trades)  # determinista


def test_no_leverage():
    syms = ["A", "B", "C"]
    bars = {s: make_bars(400, seed=10 + i) for i, s in enumerate(syms)}
    # Stop muy cerca -> el sizing pediría mucho: la caja/exposición deben recortarlo.
    sigs = {
        s: manual_signals(
            b.index,
            entries=list(range(0, 400, 5)),
            exits=list(range(3, 400, 5)),
            stop=b["close"] * 0.999,
        )
        for s, b in bars.items()
    }
    r = simulate(bars, sigs, cfg(kill_switch_drawdown=None))
    assert len(r.trades) > 0
    assert (r.exposure <= 1.0 + 1e-9).all()
    assert (r.trades.qty > 0).all()


def test_kill_switch(tmp_path):
    prices = [(100, 101, 99, 100)] * 3 + [(100, 100, 85, 86)] + [(86, 87, 85, 86)] * 10
    a = flat_bars(prices)
    s = manual_signals(a.index, entries=[0, 5, 8], stop=10.0)
    r = simulate({"SPY": a}, {"SPY": s}, cfg(risk_per_trade=1.0))
    assert r.kill_switch_date == a.index[3]
    assert r.trades.iloc[0].exit_reason == "kill_switch"
    assert len(r.trades) == 1  # sin entradas posteriores
    assert (r.n_open.iloc[5:] == 0).all()
    assert check_kill_switch([100, 110, 105], 98.9, 0.10)
    assert not check_kill_switch(110.0, 99.0, 0.10)
