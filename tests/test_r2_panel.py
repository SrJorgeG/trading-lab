"""R2-7 y R2-14: señales de panel (sector_mom / sector_lowvol), casos S1–S9 y S13 a mano,
contrato de panel, ausencia de look-ahead y coincidencia de los TOML con el pre-registro."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from conftest import make_bars

from tlab.backtest.costs import CostModel
from tlab.backtest.portfolio_sim import SimConfig, simulate
from tlab.config import load_strategy_config
from tlab.strategies import CANDIDATES_R2, PANEL_STRATEGIES, as_panel, tsmom_etf
from tlab.strategies.sector_rank import (
    generate_signals_panel,
    review_days_union,
)

DATES = pd.DatetimeIndex(["2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02"], tz="UTC")
D0201 = pd.Timestamp("2024-02-01", tz="UTC")
P = {"rank_by": "mom", "lookback": 2, "top_n": 2, "keep_n": 3, "atr_mult": 3, "atr_n": 1}
BASE = {
    "A": [100, 101, 110, 111],
    "B": [100, 100, 105, 106],
    "C": [100, 100, 102, 103],
    "D": [100, 99, 97, 96],
}


def make_panel(closes, dates=DATES, overrides=None):
    """open = cierre anterior; high/low = máx./mín. de (open, close); override por (símbolo, i)."""
    overrides = overrides or {}
    out = {}
    for s, cl in closes.items():
        rows = []
        for i, c in enumerate(cl):
            o = cl[i - 1] if i else c
            rows.append(overrides.get((s, i), (o, max(o, c), min(o, c), c)))
        df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=dates[: len(cl)])
        df["volume"] = 1000.0
        out[s] = df
    return out


A_SPECIAL = {("A", 2): (101, 111, 101, 110)}


def s1(closes=None, overrides=None, params=None):
    c = {**BASE, **(closes or {})}
    ov = {**A_SPECIAL, **(overrides or {})}
    return generate_signals_panel(make_panel(c, overrides=ov), {**P, **(params or {})})


def row(out, s):
    return out[s].loc[D0201]


def flags(out, s):
    r = row(out, s)
    return bool(r["entry"]), bool(r["exit"])


def test_s1_h5():
    out = s1()
    assert flags(out, "A") == (True, False) and row(out, "A")["stop_price"] == 80
    assert flags(out, "B") == (True, False) and row(out, "B")["stop_price"] == 90
    assert flags(out, "C") == (False, False) and row(out, "C")["stop_price"] == 96
    assert flags(out, "D") == (False, True) and row(out, "D")["stop_price"] == 91
    for s, rk in zip("ABCD", [0.10, 0.05, 0.02, -0.03], strict=True):
        assert row(out, s)["rank"] == pytest.approx(rk, abs=1e-9)
    # el resto de días, todo False
    for s in "ABCD":
        o = out[s].drop(index=D0201)
        assert not o["entry"].any() and not o["exit"].any()


def test_s2_c_cierra_a_99():
    out = s1(closes={"C": [100, 100, 99, 103]})
    assert flags(out, "A") == (True, False) and flags(out, "B") == (True, False)
    assert flags(out, "C") == (False, True) and flags(out, "D") == (False, True)
    assert row(out, "C")["stop_price"] == 96 and row(out, "C")["rank"] == pytest.approx(-0.01)


def test_s3_h7_lowvol():
    out = s1(params={"rank_by": "lowvol"})
    assert flags(out, "A") == (False, False)
    assert flags(out, "B") == (True, False) and flags(out, "C") == (True, False)
    assert flags(out, "D") == (False, True)  # D no es apto aunque tenga la menor volatilidad
    for s, rk in zip("ABCD", [-0.05332, -0.03450, -0.01400, -0.00732], strict=True):
        assert row(out, s)["rank"] == pytest.approx(rk, abs=1e-5)


def test_s3_keep_n_2():
    out = s1(params={"rank_by": "lowvol", "keep_n": 2})
    assert flags(out, "A") == (False, True)
    assert flags(out, "B") == (True, False) and flags(out, "C") == (True, False)
    assert flags(out, "D") == (False, True)


def test_s4_causal_con_velas_hasta_el_0201():
    full = s1()
    cut = {s: df.iloc[:3] for s, df in make_panel({**BASE}, overrides=A_SPECIAL).items()}
    part = generate_signals_panel(cut, P)
    for s in "ABCD":
        pd.testing.assert_frame_equal(part[s], full[s].iloc[:3])


def test_s5_empate_alfabetico():
    ov = {("B", 2): (100, 110, 100, 110)}
    out1 = s1(closes={"B": [100, 100, 110, 106]}, overrides=ov, params={"top_n": 1})
    assert flags(out1, "A") == (True, False) and flags(out1, "B") == (False, False)
    assert row(out1, "B")["stop_price"] == 80 and row(out1, "B")["rank"] == pytest.approx(0.10)
    assert flags(out1, "C") == (False, False) and flags(out1, "D") == (False, True)
    out2 = s1(closes={"B": [100, 100, 110, 106]}, overrides=ov, params={"top_n": 2})
    assert flags(out2, "A") == (True, False) and flags(out2, "B") == (True, False)
    assert flags(out2, "C") == (False, False)


def test_s6_menos_aptos_que_huecos():
    c = {"B": [100, 100, 99, 106], "C": [100, 100, 98, 103], "D": [100, 99, 97, 96]}
    out = s1(closes=c)
    assert flags(out, "A") == (True, False)
    for s in "BCD":
        assert flags(out, s) == (False, True)
    out2 = s1(closes={**c, "A": [100, 101, 99, 111]}, overrides={("A", 2): (101, 101, 99, 99)})
    for s in "ABCD":
        assert flags(out2, s) == (False, True)
    assert row(out2, "A")["stop_price"] == 93


def test_s7_historia_insuficiente():
    pan = make_panel(BASE, overrides=A_SPECIAL)
    e = pd.DataFrame(
        {"open": [50, 50.0], "high": [50, 100.0], "low": [50, 50.0], "close": [50, 100.0]},
        index=DATES[1:3],
    )
    e["volume"] = 1000.0
    pan["E"] = e
    out = generate_signals_panel(pan, P)
    ref = s1()
    for s in "ABCD":
        pd.testing.assert_frame_equal(out[s], ref[s])
    assert flags(out, "E") == (False, True) and np.isnan(row(out, "E")["rank"])


def test_s8_sin_fuga_entre_simbolos():
    pan = make_panel(BASE, overrides=A_SPECIAL)
    ref = generate_signals_panel(pan, P)
    poisoned = {s: df.copy() for s, df in pan.items()}
    poisoned["B"].loc[poisoned["B"].index > D0201, ["open", "high", "low", "close"]] *= 10
    got = generate_signals_panel(poisoned, P)
    for s in "ABCD":
        pd.testing.assert_frame_equal(got[s].loc[:D0201], ref[s].loc[:D0201])
    # Cortar solo A después del 02-01: las filas ≤ 02-01 de todos no cambian.
    cut = {s: df.copy() for s, df in pan.items()}
    cut["A"] = cut["A"].loc[:D0201]
    got2 = generate_signals_panel(cut, P)
    for s in "BCD":
        pd.testing.assert_frame_equal(got2[s].loc[:D0201], ref[s].loc[:D0201])


def test_s9_sin_vela_el_dia_de_revision():
    pan = make_panel(BASE, overrides=A_SPECIAL)
    pan["C"] = pan["C"].drop(index=D0201)
    out = generate_signals_panel(pan, P)
    assert len(out["C"]) == 3 and not out["C"]["entry"].any() and not out["C"]["exit"].any()
    assert flags(out, "A") == (True, False) and flags(out, "B") == (True, False)
    assert flags(out, "D") == (False, True)


def test_s13_de_punta_a_punta():
    dates = pd.DatetimeIndex(
        ["2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02", "2024-02-05"], tz="UTC"
    )
    c = {
        "A": [100, 101, 110, 111, 112],
        "B": [100, 100, 105, 106, 107],
        "C": [100, 100, 102, 103, 104],
        "D": [100, 99, 97, 96, 95],
    }
    pan = make_panel(c, dates=dates, overrides=A_SPECIAL)
    sig = generate_signals_panel(pan, P)
    cfg = SimConfig(
        costs={"equity": CostModel(slippage_bps=5), "crypto": CostModel()},
        initial_equity=10_000.0,
        risk_per_trade=0.01,
        max_position_fraction=0.3333,
        kill_switch_drawdown=None,
    )
    r = simulate(pan, sig, cfg)
    t = r.trades.set_index("symbol")
    assert set(t.index) == {"A", "B"}
    assert t.loc["A", "qty"] == 3 and t.loc["B", "qty"] == 6
    assert t.loc["A", "entry_price"] == pytest.approx(110.055)
    assert t.loc["B", "entry_price"] == pytest.approx(105.0525)
    assert t.loc["A", "risk_usd"] == pytest.approx(90.285) and t.loc["B", "risk_usd"] == (
        pytest.approx(90.585)
    )
    assert (t["exit_reason"] == "end_of_data").all()
    assert t.loc["A", "exit_price"] == pytest.approx(111.944)
    assert t.loc["B", "exit_price"] == pytest.approx(106.9465)
    assert t.loc["A", "pnl_usd"] == pytest.approx(5.667, abs=0.001)
    assert t.loc["B", "pnl_usd"] == pytest.approx(11.364, abs=0.001)
    assert t.loc["A", "pnl_r"] == pytest.approx(0.063, abs=0.001)
    assert t.loc["B", "pnl_r"] == pytest.approx(0.125, abs=0.001)
    assert r.equity.round(3).tolist() == [10000, 10000, 10000, 10008.52, 10017.031]
    assert r.n_open.tolist() == [0, 0, 0, 2, 2]


# ---------------------------------------------------------------- contrato y look-ahead
SYMS = ["S0", "S1", "S2", "S3", "S4"]
PP = {"rank_by": "mom", "lookback": 126, "top_n": 3, "keep_n": 5, "atr_mult": 3.0, "atr_n": 20}


def _five(n=600):
    return {s: make_bars(n, seed=i) for i, s in enumerate(SYMS)}


@pytest.mark.parametrize("sid", sorted(PANEL_STRATEGIES))
@pytest.mark.parametrize("rank_by", ["mom", "lowvol"])
def test_contrato_3_y_4(sid, rank_by):
    bars = _five()
    out = PANEL_STRATEGIES[sid](bars, {**PP, "rank_by": rank_by})
    assert set(out) == set(bars)
    for s in bars:
        assert out[s].index.equals(bars[s].index)
        assert not (out[s]["entry"] & out[s]["exit"]).any()
        assert out[s]["entry"].dtype == bool and out[s]["exit"].dtype == bool
    assert any(o["entry"].any() for o in out.values())


@pytest.mark.parametrize("sid", sorted(PANEL_STRATEGIES))
def test_pura_no_modifica_entradas(sid):
    bars = _five(300)
    copia = {s: df.copy() for s, df in bars.items()}
    p = dict(PP)
    PANEL_STRATEGIES[sid](bars, p)
    assert p == PP
    for s in bars:
        pd.testing.assert_frame_equal(bars[s], copia[s])


@pytest.mark.parametrize("rank_by", ["mom", "lowvol"])
@pytest.mark.parametrize("t", [150, 300, 451, 599])
def test_truncar_todos(rank_by, t):
    bars = _five()
    pr = {**PP, "rank_by": rank_by}
    full = generate_signals_panel(bars, pr)
    part = generate_signals_panel({s: df.iloc[:t] for s, df in bars.items()}, pr)
    for s in SYMS:
        pd.testing.assert_frame_equal(part[s], full[s].iloc[:t])


@pytest.mark.parametrize("rank_by", ["mom", "lowvol"])
@pytest.mark.parametrize("t", [150, 300, 451])
def test_truncar_uno_y_envenenar_uno(rank_by, t):
    bars = _five()
    pr = {**PP, "rank_by": rank_by}
    full = generate_signals_panel(bars, pr)
    cut_date = bars["S2"].index[t - 1]
    cut = {**bars, "S2": bars["S2"].iloc[:t]}
    got = generate_signals_panel(cut, pr)
    for s in SYMS:
        pd.testing.assert_frame_equal(got[s].loc[:cut_date], full[s].loc[:cut_date])
    for poison in ("x10", "nan"):
        p = bars["S1"].copy()
        p.iloc[t:] = p.iloc[t:] * 10 if poison == "x10" else np.nan
        got = generate_signals_panel({**bars, "S1": p}, pr)
        for s in SYMS:
            pd.testing.assert_frame_equal(got[s].iloc[:t], full[s].iloc[:t])


def test_as_panel_de_tsmom():
    bars = _five(300)
    p = {"lookback": 126, "atr_mult": 4.0, "atr_n": 20}
    got = as_panel(tsmom_etf.generate_signals)(bars, p)
    for s in SYMS:
        pd.testing.assert_frame_equal(got[s], tsmom_etf.generate_signals(bars[s], p))


# ---------------------------------------------------------------- casos límite
def test_un_solo_simbolo():
    out = generate_signals_panel({"A": make_bars(300)}, PP)
    assert set(out) == {"A"} and len(out["A"]) == 300


def test_sin_historia_todo_false_y_sin_excepcion():
    bars = {s: make_bars(40, seed=i) for i, s in enumerate(["A", "B"])}
    out = generate_signals_panel(bars, PP)  # lookback 126 > 40 velas: nadie es apto
    for s in bars:
        assert not out[s]["entry"].any()


def test_bars_vacio_y_sin_tz():
    with pytest.raises(ValueError):
        generate_signals_panel({}, PP)
    b = make_bars(300)
    b.index = b.index.tz_localize(None)
    with pytest.raises(ValueError):
        generate_signals_panel({"A": b}, PP)


@pytest.mark.parametrize(
    "bad", [{"top_n": 0}, {"keep_n": 2, "top_n": 3}, {"lookback": 0}, {"rank_by": "otro"}]
)
def test_parametros_invalidos(bad):
    with pytest.raises(ValueError):
        generate_signals_panel(_five(300), {**PP, **bad})


def test_dias_de_revision_union():
    idx = pd.DatetimeIndex(["2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02"], tz="UTC")
    a = pd.DataFrame({"close": 1.0}, index=idx[:2])
    b = pd.DataFrame({"close": 1.0}, index=idx[1:])
    # La primera fecha de la unión (01-30) no cuenta; la primera de febrero es el 02-01.
    assert list(review_days_union({"A": a, "B": b})) == [D0201]


# ---------------------------------------------------------------- TOML
@pytest.mark.parametrize("sid", CANDIDATES_R2)
def test_toml_coincide_con_el_preregistro(sid):
    sc = load_strategy_config(sid)
    assert sc["id"] == sid and sc["status"] == "preregistrada" and sc["frozen"] is False
    assert sc["universe"] == ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
    assert sc["replica_universe"] == ["EWJ", "EWG", "EWU", "EWC", "EWQ", "EWI", "EWA", "EWL", "EWH"]
    assert sc["benchmark"] == "SPY" and sc["benchmark_info"] == {"SPY": 0.6, "IEF": 0.4}
    assert sc["fixed_income"] == "IEF" and sc["fixed_income_from"] == "2002-08-01"
    tr = sc["tranches"]
    assert (tr["is"]["start"], tr["is"]["end"]) == ("2007-07-01", "2020-12-31")
    assert (tr["replica"]["start"], tr["replica"]["end"]) == ("2000-07-01", "2026-10-31")
    assert (tr["holdout_old"]["start"], tr["holdout_old"]["end"]) == ("2000-07-01", "2007-06-30")
    assert (tr["holdout_new"]["start"], tr["holdout_new"]["end"]) == ("2021-01-01", "2026-10-31")
    assert (tr["full"]["start"], tr["full"]["end"]) == ("2000-07-01", "2026-10-31")
    assert [tr[k]["slippage_bps"] for k in ("is", "replica", "holdout_old", "holdout_new")] == [
        5,
        15,
        10,
        5,
    ]
    assert tr["full"]["slippage_schedule"] == [["2000-07-01", 10], ["2007-07-01", 5]]
    assert tr["replica"]["universe"] == "replica_universe"
    assert sc["params"] == {
        "rank_by": "mom" if sid == "sector_mom" else "lowvol",
        "lookback": 126,
        "top_n": 3,
        "keep_n": 5,
        "atr_mult": 3.0,
        "atr_n": 20,
    }
    assert sc["robust_grid"] == {
        "lookback": [95, 126, 158],
        "atr_mult": [2.25, 3.0, 3.75],
        "keep_n": [4, 5, 6],
    }
    assert sc["risk_levels"] == [0.01, 0.0075, 0.005] and sc["calibration_dd_limit"] == 0.12
    assert sc["subperiods"] == [
        ["2000-07-01", "2007-06-30"],
        ["2007-07-01", "2013-12-31"],
        ["2014-01-01", "2020-06-30"],
        ["2020-07-01", "2026-10-31"],
    ]
    assert sc["min_history_bars"] == 365 and sc["kill_switch_in_backtest"] is False
    n = 1
    for v in sc["robust_grid"].values():
        n *= len(v)
    assert n == 27 and n + len(sc["risk_levels"]) - 1 <= 30
