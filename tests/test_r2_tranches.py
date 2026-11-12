"""R2-5: tramos, candado de un solo uso, coste por fecha, rejilla explícita y registro (T1–T21,
G1–G6, CF1–CF4, y los tests de E21: árbol sucio y estrategias rechazadas)."""

from __future__ import annotations

import copy
import csv
from pathlib import Path

import pandas as pd
import pytest
from conftest import flat_bars, make_bars, manual_signals

from tlab.backtest.costs import CostModel, CostSchedule
from tlab.backtest.guards import (
    LOG_COLUMNS,
    OOSGuardError,
    migrate_oos_log,
    require_clean_tree,
)
from tlab.backtest.portfolio_sim import SimConfig, simulate
from tlab.backtest.robustness import param_grid
from tlab.backtest.runner import run_backtest
from tlab.backtest.tranches import (
    TrancheGuardError,
    assert_is_allowed,
    check_tranche_guard,
    load_tranche,
    tranche_costs,
    tranche_hash,
)
from tlab.backtest.walkforward import pick_best
from tlab.config import load_strategy_config

REPO = Path(__file__).resolve().parents[1]


def clean_probe():
    """Sonda de git falsa: árbol limpio y un hash de HEAD reconocible."""
    return [], "c0ffee" * 6 + "abcd"


def dirty_probe():
    return [" M src/tlab/risk.py"], "abc"


def ts(d: str) -> pd.Timestamp:
    return pd.Timestamp(d, tz="UTC")


def guard(
    log, tranche, *, costs="base", delay=0, kind="candidata", frozen=True, confirm=True,
    h="h1", strategy="s",
):  # fmt: skip
    check_tranche_guard(log, strategy, tranche, h, costs, delay, kind, frozen, confirm, "rep")


def read_rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture
def log(tmp_path):
    return tmp_path / "oos_log.csv"


# ---------------------------------------------------------------- guarda (T1–T12)
def test_t1_sin_confirmacion(log):
    with pytest.raises(TrancheGuardError, match="confirm-tranche"):
        guard(log, "replica", confirm=False)


def test_t2_sin_congelar(log):
    with pytest.raises(TrancheGuardError, match="congelaci"):
        guard(log, "replica", frozen=False)


def test_t3_t4_fila_y_no_repetir(log):
    guard(log, "replica")
    rows = read_rows(log)
    assert len(rows) == 1
    r = rows[0]
    key = (r["tranche"], r["costs"], r["entry_delay"], r["kind"])
    assert key == ("replica", "base", "0", "candidata")
    with pytest.raises(TrancheGuardError, match="Ya ejecutado"):
        guard(log, "replica")


def test_t5_t6_orden(log):
    with pytest.raises(TrancheGuardError, match="Orden"):
        guard(log, "holdout_old")
    guard(log, "replica")
    with pytest.raises(TrancheGuardError, match="Orden"):
        guard(log, "holdout_new")  # saltándose holdout_old


def test_t7_cadena_completa(log):
    for t in ("replica", "holdout_old", "holdout_new", "full"):
        guard(log, t)
    assert len(read_rows(log)) == 4


def test_t8_otro_hash(log):
    guard(log, "replica")
    with pytest.raises(TrancheGuardError, match="otros parámetros"):
        guard(log, "replica", h="h2")


def test_t9_estres_exige_base(log):
    guard(log, "replica")
    with pytest.raises(TrancheGuardError, match="base"):
        guard(log, "holdout_old", costs="stress")
    guard(log, "holdout_old")
    guard(log, "holdout_old", costs="stress")
    with pytest.raises(TrancheGuardError, match="Ya ejecutado"):
        guard(log, "holdout_old", costs="stress")
    guard(log, "holdout_old", delay=1)


def test_t10_combinacion_no_anunciada(log):
    guard(log, "replica")
    with pytest.raises(TrancheGuardError, match="no anunciada"):
        guard(log, "replica", costs="stress", delay=1)


def test_t11_monos(log):
    with pytest.raises(TrancheGuardError):
        guard(log, "replica", kind="monos_rank")
    guard(log, "replica")
    guard(log, "replica", kind="monos_rank")
    with pytest.raises(TrancheGuardError, match="Ya ejecutado"):
        guard(log, "replica", kind="monos_rank")


def test_t12_combo(log):
    for t in ("replica", "is"):
        with pytest.raises(TrancheGuardError):
            guard(log, t, kind="combo", strategy="a+b")
    for t in ("holdout_old", "holdout_new", "full"):
        guard(log, t, kind="combo", strategy="a+b")


def test_tramo_no_guardado(log):
    with pytest.raises(TrancheGuardError):
        guard(log, "is")


def test_t13_hash():
    p = {"a": 1, "b": 2}
    assert tranche_hash(p, 0.01) != tranche_hash(p, 0.005)
    assert tranche_hash(p, 0.01) == tranche_hash({"b": 2, "a": 1}, 0.01)


def test_t14_migracion(tmp_path):
    src = REPO / "reports" / "oos_log.csv"
    dst = tmp_path / "oos_log.csv"
    # Copia del log con la cabecera antigua (4 columnas) de la ronda 1.
    old_text = "date_madrid,strategy,params_hash,forced\n" + "\n".join(
        ["2026-11-11T16:36+01:00,donchian_etf,205cf5b9047f,False"] * 4
    )
    dst.write_text(old_text + "\n", encoding="utf-8")
    assert src.exists()  # el real existe; no se toca
    old_rows = read_rows(dst)
    migrate_oos_log(dst)
    rows = read_rows(dst)
    assert list(rows[0]) == LOG_COLUMNS and len(rows) == len(old_rows) == 4
    for new, old in zip(rows, old_rows, strict=True):
        assert all(new[k] == old[k] for k in old)
        assert all(new[k] == "" for k in LOG_COLUMNS if k not in old)
    before = dst.read_text(encoding="utf-8")
    migrate_oos_log(dst)
    assert dst.read_text(encoding="utf-8") == before


SC_MINI = {
    "id": "x", "start": "2018-06-01", "is_end": "2020-12-31", "end": "2022-06-30",
    "universe": ["A"], "replica_universe": ["R"],
    "tranches": {
        "is": {"start": "2018-06-01", "end": "2020-12-31", "slippage_bps": 5},
        "replica": {"start": "2019-01-01", "end": "2022-06-30", "universe": "replica_universe",
                    "slippage_bps": 15},
        "full": {"start": "2018-06-01", "end": "2022-06-30",
                 "slippage_schedule": [["2018-06-01", 10], ["2019-01-01", 5]]},
    },
}  # fmt: skip


def test_t15_assert_is_allowed():
    sc = {**SC_MINI, "frozen": True}
    a, b = ts("2018-06-01"), ts("2020-12-31")
    with pytest.raises(TrancheGuardError):
        assert_is_allowed(sc, a, b)
    sc = {**SC_MINI, "frozen": False}
    with pytest.raises(TrancheGuardError):
        assert_is_allowed(sc, a, ts("2021-01-04"))
    assert_is_allowed(sc, a, b)


def _tr(**over):
    sc = copy.deepcopy(SC_MINI)
    for k, v in over.items():
        name, key = k.split("__")
        if v is None:
            sc["tranches"][name].pop(key, None)
        else:
            sc["tranches"][name][key] = v
    return sc


@pytest.mark.parametrize(
    "sc, name",
    [
        (SC_MINI, "no_existe"),
        (_tr(replica__start="2023-01-01"), "replica"),  # start > end
        (_tr(replica__slippage_bps=None), "replica"),  # sin coste
        (_tr(replica__slippage_schedule=[["2019-01-01", 5]]), "replica"),  # los dos
        (_tr(full__slippage_schedule=[["2019-01-01", 5], ["2018-06-01", 10]]), "full"),
        (_tr(full__slippage_schedule=[["2018-09-01", 10]]), "full"),  # empieza tarde
        (_tr(is__end="2020-12-30"), "is"),
        (_tr(replica__end="2022-07-01"), "replica"),
    ],
)
def test_t16_load_tranche_errores(sc, name):
    with pytest.raises(ValueError):
        load_tranche(sc, name)


def test_load_tranche_ok_y_costes():
    full = load_tranche(SC_MINI, "full")
    assert full.slippage_bps is None and len(full.schedule) == 2
    assert load_tranche(SC_MINI, "replica").universe == ["R"]
    settings = {
        "costs": {
            "equity": {"commission_per_share": 0.0, "slippage_bps": 5},
            "crypto": {"fee_rate": 0.0025, "slippage_bps": 20},
            "stress": {"multiplier": 2.0},
        }
    }
    rep = load_tranche(SC_MINI, "replica")
    c, sch = tranche_costs(settings, rep)
    assert c["equity"].slippage_bps == 15 and sch is None
    c2, _ = tranche_costs(settings, rep, "stress")
    assert c2["equity"].slippage_bps == 30
    c3, sch3 = tranche_costs(settings, full)
    assert c3["equity"].slippage_bps == 10 and sch3.steps[1][1]["equity"].slippage_bps == 5
    _, sch4 = tranche_costs(settings, full, "stress")
    assert sch4.steps[1][1]["equity"].slippage_bps == 10


# ---------------------------------------------------------------- rejilla (G1–G6)
def test_g1_g2_g5_rejilla():
    assert [p["lookback"] for p in param_grid({"lookback": 126}, ["lookback"])] == [94, 126, 158]
    ex = {"lookback": [95, 126, 158]}
    got = param_grid({"lookback": 126}, ["lookback"], explicit=ex)
    assert [p["lookback"] for p in got] == [95, 126, 158]
    with pytest.raises(ValueError):
        param_grid({"lookback": 126}, ["lookback"], explicit={"lookback": [95, 158]})


@pytest.mark.parametrize("sid", ["sector_mom", "sector_lowvol"])
def test_g3_toml(sid):
    sc = load_strategy_config(sid)
    g = param_grid(sc["params"], sc["robust_keys"], explicit=sc["robust_grid"])
    assert len(g) == 27 and len(g) + len(sc["risk_levels"]) - 1 <= 30
    assert sorted({p["lookback"] for p in g}) == [95, 126, 158]


def test_g6_pick_best_empate_elige_por_defecto():
    sc = load_strategy_config("sector_mom")
    g = param_grid(sc["params"], sc["robust_keys"], explicit=sc["robust_grid"])
    best = pick_best([(p, 0.5) for p in g], sc["params"], sc["robust_keys"])
    assert best == sc["params"]


# ---------------------------------------------------------------- coste por fecha (CF1–CF4)
def _sched():
    return CostSchedule(
        (
            (ts("2000-07-01"), {"equity": CostModel(slippage_bps=10), "crypto": CostModel()}),
            (ts("2007-07-01"), {"equity": CostModel(slippage_bps=5), "crypto": CostModel()}),
        )
    )


def _cf_run(schedule):
    prices = [
        (100, 100, 100, 100),
        (100, 100, 100, 100),
        (100, 105, 100, 105),
        (110, 111, 109, 110),
        (110, 110, 110, 110),
    ]
    b = flat_bars(prices, start="2007-06-27")
    s = manual_signals(b.index, entries=[1], exits=[2], stop=94.0)
    cfg = SimConfig(
        costs=schedule.steps[0][1],
        cost_schedule=schedule,
        initial_equity=10_000.0,
        risk_per_trade=0.01,
        max_position_fraction=0.3333,
        kill_switch_drawdown=None,
    )
    return simulate({"SPY": b}, {"SPY": s}, cfg).trades.iloc[0]


def test_cf1_coste_por_fecha():
    t = _cf_run(_sched())
    assert str(t.entry_date.date()) == "2007-06-29" and str(t.exit_date.date()) == "2007-07-02"
    assert t.entry_price == pytest.approx(100.10) and t.qty == 16
    assert t.risk_usd == pytest.approx(99.104)
    assert t.exit_price == pytest.approx(109.945)
    assert t.pnl_usd == pytest.approx(157.52, abs=0.01)
    assert t.pnl_r == pytest.approx(1.589, abs=1e-3)


def test_cf2_estres_x2():
    t = _cf_run(_sched().scaled(2))
    assert t.entry_price == pytest.approx(100.20) and t.qty == 15
    assert t.exit_price == pytest.approx(109.89)
    assert t.pnl_usd == pytest.approx(145.35, abs=0.01)


def test_cf4_at():
    s = _sched()
    with pytest.raises(ValueError):
        s.at(ts("2000-06-30"))
    assert s.at(ts("2007-06-30"))["equity"].slippage_bps == 10
    assert s.at(ts("2007-07-01"))["equity"].slippage_bps == 5


# ---------------------------------------------------------------- run_backtest ronda 2 (T17–T21)
def mini_sc(**over):
    sc = {
        "id": "sector_mom", "kind": "panel", "status": "preregistrada", "frozen": False,
        "universe": ["AAA", "BBB", "CCC"], "replica_universe": ["RRR", "SSS", "TTT"],
        "benchmark": "AAA", "benchmark_info": {}, "robust_keys": ["lookback"],
        "robust_grid": {"lookback": [15, 20, 25]},
        "start": "2018-06-01", "is_end": "2020-12-31", "end": "2022-06-30",
        "min_history_bars": 365, "require_full_universe": True,
        "risk_per_trade": 0.01, "risk_levels": [0.01, 0.0075, 0.005],
        "calibration_dd_limit": 0.12, "kill_switch_in_backtest": False,
        "subperiods": [["2018-06-01", "2020-12-31"], ["2021-01-01", "2022-06-30"]],
        "walkforward": {"first_test": "2020-01-01", "test_months": 6, "n_windows": 2,
                        "min_valid_windows": 1},
        "tranches": {
            "is": {"start": "2018-06-01", "end": "2020-12-31", "universe": "universe",
                   "slippage_bps": 5},
            "replica": {"start": "2018-06-01", "end": "2022-06-30",
                        "universe": "replica_universe", "slippage_bps": 15},
            "holdout_old": {"start": "2018-06-01", "end": "2019-12-31", "universe": "universe",
                            "slippage_bps": 10},
            "holdout_new": {"start": "2021-01-01", "end": "2022-06-30", "universe": "universe",
                            "slippage_bps": 5},
            "full": {"start": "2018-06-01", "end": "2022-06-30", "universe": "universe",
                     "slippage_schedule": [["2018-06-01", 10], ["2019-01-01", 5]]},
        },
        "params": {"rank_by": "mom", "lookback": 20, "top_n": 2, "keep_n": 3, "atr_mult": 3.0,
                   "atr_n": 10},
    }  # fmt: skip
    sc.update(over)
    return sc


def mini_data(short=None):
    names = ["AAA", "BBB", "CCC", "RRR", "SSS", "TTT"]
    d = {s: make_bars(1500, seed=i, start="2017-01-02") for i, s in enumerate(names)}
    if short:
        d[short] = make_bars(300, seed=9, start="2018-03-01")
    return d


def run(tmp_path, settings, mode, sc=None, data=None, probe=clean_probe, **kw):
    return run_backtest(
        "sector_mom", mode, data=data or mini_data(), reports_dir=tmp_path / "reports",
        registry=tmp_path / "reg.md", settings=settings, strat_cfg=sc or mini_sc(),
        git_probe=probe, **kw,
    )  # fmt: skip


def test_t17_is_no_pasa_de_is_end(tmp_path, settings):
    p = run(tmp_path, settings, "is")
    eq = pd.read_csv(p.parent / "equity.csv", index_col=0, parse_dates=True)
    assert eq.index[-1] <= ts("2020-12-31")
    assert "Tramo **is**" in p.read_text(encoding="utf-8")
    assert not (tmp_path / "reports" / "oos_log.csv").exists()  # el IS no gasta tramos


def test_t18_replica_a_ciegas(tmp_path, settings):
    sc = mini_sc(frozen=True)
    p = run(tmp_path, settings, "replica", sc=sc, confirm_tranche=True)
    assert p.name == "criterio15.md" and (p.parent / "detalle").is_dir()
    assert "NO ABRIR" in (p.parent / "detalle" / "README.md").read_text(encoding="utf-8")
    txt = p.read_text(encoding="utf-8")
    assert "CAGR" not in txt and "Expectancy" in txt and "Sharpe" in txt
    last = (tmp_path / "reg.md").read_text(encoding="utf-8").strip().splitlines()[-1]
    assert "CAGR" not in last and "DD" not in last and "expectancy" in last and "n=" in last
    rows = read_rows(tmp_path / "reports" / "oos_log.csv")
    assert rows[-1]["tranche"] == "replica" and rows[-1]["commit"].startswith("c0ffee")
    with pytest.raises(TrancheGuardError, match="Ya ejecutado"):
        run(tmp_path, settings, "replica", sc=sc, confirm_tranche=True)


def test_escalera_completa_con_costes_por_fecha(tmp_path, settings):
    sc = mini_sc(frozen=True)
    for mode in ("replica", "holdout_old", "holdout_new", "full"):
        run(tmp_path, settings, mode, sc=sc, confirm_tranche=True)
    rows = read_rows(tmp_path / "reports" / "oos_log.csv")
    assert [r["tranche"] for r in rows] == ["replica", "holdout_old", "holdout_new", "full"]
    full = next((tmp_path / "reports" / "sector_mom").glob("full_*/resumen.md"))
    assert "Calendario de costes (E11)" in full.read_text(encoding="utf-8")


def test_t19_oos_no_existe_en_ronda2(tmp_path, settings):
    with pytest.raises(ValueError, match="oos"):
        run(tmp_path, settings, "oos", sc=mini_sc(frozen=True), confirm_oos=True)


def test_t20_universo_incompleto(tmp_path, settings):
    with pytest.raises(ValueError, match="CCC"):
        run(tmp_path, settings, "is", data=mini_data(short="CCC"))


def test_replica_exige_confirmacion_y_congelar(tmp_path, settings):
    with pytest.raises(TrancheGuardError):
        run(tmp_path, settings, "replica", sc=mini_sc(frozen=True))
    with pytest.raises(TrancheGuardError):
        run(tmp_path, settings, "replica", sc=mini_sc(frozen=False), confirm_tranche=True)


def test_congelada_no_hay_mas_is(tmp_path, settings):
    with pytest.raises(TrancheGuardError):
        run(tmp_path, settings, "is", sc=mini_sc(frozen=True))


# ---------------------------------------------------------------- E21: árbol sucio y rechazadas
def test_e21_arbol_sucio(tmp_path, settings):
    with pytest.raises(OOSGuardError, match="sin commitear"):
        run(tmp_path, settings, "is", probe=dirty_probe)
    with pytest.raises(OOSGuardError, match="sin commitear"):
        run(
            tmp_path, settings, "replica", sc=mini_sc(frozen=True), probe=dirty_probe,
            confirm_tranche=True,
        )  # fmt: skip
    assert require_clean_tree(clean_probe).startswith("c0ffee")


@pytest.mark.parametrize("sid", ["donchian_etf", "donchian_crypto"])
@pytest.mark.parametrize("mode", ["oos", "full"])
def test_e21_rechazadas_no_ejecutan_fuera_de_is(sid, mode, tmp_path, settings):
    with pytest.raises(OOSGuardError, match="rechazada"):
        run_backtest(
            sid, mode, reports_dir=tmp_path / "r", registry=tmp_path / "reg.md",
            settings=settings, confirm_oos=True,
        )  # fmt: skip
    assert not (tmp_path / "r").exists()


def test_e21_aparcada_valida(tmp_path, settings):
    sc = mini_sc(status="aparcada")
    with pytest.raises(OOSGuardError, match="aparcada"):
        run(tmp_path, settings, "holdout_old", sc=sc, confirm_tranche=True)
