"""R2-14 (S10–S12): comportamiento del simulador con señales de panel. Casos a mano."""

from __future__ import annotations

import pytest
from conftest import flat_bars, manual_signals

from tlab.backtest.costs import CostModel
from tlab.backtest.portfolio_sim import SimConfig, simulate

FLAT = [(100, 101, 99, 100)] * 10


def cfg():
    return SimConfig(
        costs={"equity": CostModel(slippage_bps=5), "crypto": CostModel()},
        initial_equity=10_000.0,
        risk_per_trade=0.01,
        max_position_fraction=0.3333,
        kill_switch_drawdown=None,
    )


def world(w_drop=None):
    bars = {s: flat_bars(FLAT) for s in "XYZW"}
    if w_drop is not None:
        bars["W"] = bars["W"].drop(index=bars["W"].index[w_drop])
    return bars


def sigs(bars, entries, exits=None, stop=90.0):
    exits = exits or {}
    return {
        s: manual_signals(df.index, entries=entries.get(s, ()), exits=exits.get(s, ()), stop=stop)
        for s, df in bars.items()
    }


def test_s10_puesto_4_o_5_conserva_el_hueco_y_no_hay_cola():
    bars = world()
    sg = sigs(bars, {"X": [0], "Y": [0], "Z": [0], "W": [5]})  # X: sin entry ni exit el día 5
    r = simulate(bars, sg, cfg())
    assert len(r.trades) == 3 and set(r.trades.symbol) == {"X", "Y", "Z"}
    assert (r.trades.exit_reason == "end_of_data").all()
    assert (r.trades.qty == 9).all()
    assert r.trades.entry_price.to_numpy() == pytest.approx(100.05)
    assert (r.n_open.iloc[1:9] == 3).all()


def test_s10_variante_w_sin_vela_el_dia_6():
    bars = world(w_drop=6)
    sg = sigs(bars, {"X": [0], "Y": [0], "Z": [0], "W": [5]})
    r = simulate(bars, sg, cfg())
    assert set(r.trades.symbol) == {"X", "Y", "Z"}  # la pendiente de W tampoco entra el día 7


def test_s11_rotacion_en_la_misma_apertura():
    bars = world()
    sg = sigs(bars, {"X": [0], "Y": [0], "Z": [0], "W": [5]}, exits={"Z": [5]})
    r = simulate(bars, sg, cfg())
    t = r.trades.set_index("symbol")
    idx = bars["X"].index
    assert t.loc["Z", "exit_date"] == idx[6] and t.loc["Z", "exit_price"] == pytest.approx(99.95)
    assert t.loc["W", "entry_date"] == idx[6] and t.loc["W", "entry_price"] == pytest.approx(100.05)
    assert r.n_open.iloc[5] == 3 and r.n_open.iloc[6] == 3
    assert (r.exposure <= 1.0 + 1e-12).all()
    assert ((r.equity * (1 - r.exposure)) >= -1e-9).all()
    # Caja tras la apertura: 10000 − 3·900,45 + 899,55 − 900,45 = 7297,75; 27 acciones a 100.
    assert r.equity.iloc[6] == pytest.approx(7297.75 + 27 * 100)


def test_s12_senal_repetida_no_cambia_cantidad_ni_stop():
    bars = {"X": flat_bars(FLAT)}
    bars["X"].iloc[7] = [100, 101, 94, 100, 1000.0]  # low 94: saltaría un stop en 95, no en 90
    s = manual_signals(bars["X"].index, entries=[0, 5], stop=90.0)
    s.iloc[5, s.columns.get_loc("stop_price")] = 95.0
    r = simulate(bars, {"X": s}, cfg())
    assert len(r.trades) == 1
    tr = r.trades.iloc[0]
    assert tr.exit_reason == "end_of_data"
    assert tr.qty == 9 and tr.stop_initial == 90.0
