"""R2-10 / R2-17: métricas nuevas y criterios (casos ME1–ME16 de la especificación)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from tlab import metrics
from tlab.backtest.criteria import (
    checklist,
    criterion_16,
    criterion_17,
    monte_carlo_dd_grouped,
)


def test_me1_relacion():
    assert metrics.return_dd_ratio(0.06, -0.12) == pytest.approx(0.5)


def test_me2_me3_me5_me6_me7_criterio_17():
    assert criterion_17(0.06, -0.12, 50, 0.09, -0.55) is True  # 0,5 > 0,1636
    assert criterion_17(-0.01, -0.02, 50, 0.20, -0.10) is False  # E9 a
    assert criterion_17(0.01, -0.05, 10, -0.02, -0.40) is True  # E9 b
    assert criterion_17(0.05, -0.05, 0, 0.10, -0.50) is False  # sin operaciones
    assert criterion_17(0.06, -0.12, 50, 0.10, -0.20) is False  # 0,5 no es mayor que 0,5


def test_me4_caida_cero():
    assert math.isinf(metrics.return_dd_ratio(0.03, 0.0, 5))
    assert criterion_17(0.03, 0.0, 5, 0.10, -0.20) is True
    assert math.isnan(metrics.return_dd_ratio(0.03, 0.0, 0))  # sin operaciones


def test_me8_cagr_conjunto():
    assert metrics.joint_cagr(1.5, 7, 1.2, 5) == pytest.approx(0.0502017, abs=1e-7)


def test_me9_criterio_16():
    assert criterion_16(0.0501, 0.03, 0.02) is True
    assert criterion_16(0.0499, 0.03, 0.02) is False
    assert criterion_16(0.0300, 0.03, 0.0) is False
    assert criterion_16(0.0301, 0.03, 0.0) is True


def test_me10_peor_ano():
    idx = pd.to_datetime(
        ["2020-12-31", "2021-06-30", "2021-12-31", "2022-12-30", "2023-12-29"], utc=True
    )
    eq = pd.Series([100, 120, 110, 99, 108.9], index=idx)
    year, ret = metrics.worst_calendar_year(eq)
    assert year == 2022 and ret == pytest.approx(-0.10)


def test_me11_rachas():
    pnl = [10, -20, -30, 5, -5, -5, -5]
    d = pd.date_range("2024-01-01", periods=7, tz="UTC")
    t = pd.DataFrame({"pnl_usd": pnl, "exit_date": d, "entry_date": d, "symbol": "A"})
    r = metrics.losing_streaks(t.sample(frac=1, random_state=1))  # se ordena solo
    assert r == {"longest_n": 3, "longest_usd": -15.0, "deepest_usd": -50.0}
    cero = t.assign(pnl_usd=[-1, -1, 0, -1, -1, -1, 1])  # pnl == 0 corta la racha
    assert metrics.losing_streaks(cero)["longest_n"] == 3
    assert metrics.losing_streaks(t.iloc[:0])["longest_n"] == 0


def test_me12_me13_efectivo_como_caja():
    idx = pd.date_range("2024-01-01", periods=3, tz="UTC")
    eq = pd.Series([10000, 10100, 9898.0], index=idx)
    cash = pd.Series([10000, 10002, 10004.0004], index=idx)
    adj = metrics.cash_adjusted_equity(eq, pd.Series([0.5, 0.0, 1.0], index=idx), cash)
    assert adj.to_numpy() == pytest.approx([10000, 10101.0, 9901.0002])
    full = metrics.cash_adjusted_equity(eq, pd.Series(1.0, index=idx), cash)
    assert full.to_numpy() == pytest.approx(eq.to_numpy())
    flat = pd.Series(10000.0, index=idx)
    out = metrics.cash_adjusted_equity(flat, pd.Series(0.0, index=idx), cash)
    assert out.to_numpy() == pytest.approx(cash.to_numpy())


def test_me14_monte_carlo_agrupado():
    d1, d2 = pd.Timestamp("2024-01-31", tz="UTC"), pd.Timestamp("2024-02-29", tz="UTC")
    t = pd.DataFrame({"entry_date": [d1] * 3 + [d2] * 3, "pnl_usd": [-100.0] * 3 + [50.0] * 3})
    dd = monte_carlo_dd_grouped(t, 10_000.0, n=200, seed=42)
    assert set(np.round(dd, 6)) <= {0.03, 0.029557}
    assert np.array_equal(dd, monte_carlo_dd_grouped(t, 10_000.0, n=200, seed=42))


def test_me15_16d():
    def f(s, ief, cash):
        rows = checklist("full", cagr_16d=s, ief_cagr_16d=ief, cash_cagr_16d=cash)
        return [r for r in rows if r[0].startswith("16d")][0][2]

    assert f(0.06, 0.05, 0.03) is True
    assert f(0.049, 0.04, 0.03) is False  # falla caja + 2
    assert f(0.06, 0.07, 0.03) is False  # falla IEF


def test_me16_16a_no_calculable():
    rows = checklist("holdout_new", g_old=None)
    assert [r for r in rows if r[0].startswith("16a")][0][2] is None


def test_checklist_is_y_sin_apta():
    rows = checklist(
        "is", expectancy_usd=5.0, max_dd_calibrated=-0.11, sharpe=0.6, cagr=0.06, cash_cagr=0.03
    )
    assert [r[2] for r in rows] == [True, True, True, True]
    assert not any("apta" in r[0].lower() or "apta" in r[1].lower() for r in rows)
    # kill switch al 15 %: el hold-out exige 0 episodios
    assert checklist("holdout_old", kill_switch_episodes=1)[0][2] is False


# ---------------------------------------------------------------- secciones por tramo (R2-10.3)
def _cash_rate():
    idx = pd.date_range("2016-01-01", "2023-01-01", freq="D", tz="UTC")
    return pd.Series(0.03, index=idx)


def _run(tmp_path, settings, mode, **kw):
    from test_r2_tranches import clean_probe, mini_data, mini_sc

    from tlab.backtest.runner import run_backtest

    return run_backtest(
        "sector_mom", mode, data=mini_data(), reports_dir=tmp_path / "reports",
        registry=tmp_path / "reg.md", settings=settings, strat_cfg=mini_sc(frozen=mode != "is"),
        git_probe=clean_probe, cash_rate=_cash_rate(), **kw,
    )  # fmt: skip


def test_secciones_is_y_tramos(tmp_path, settings):
    txt = _run(tmp_path, settings, "is").read_text(encoding="utf-8")
    for s in ("Ronda 2: benchmarks", "Caja (letras", "Peor año natural", "Peor racha",
              "kill switch al 15 %", "Casillas de este tramo", "16-IS", "17-IS"):  # fmt: skip
        assert s in txt
    assert "apta" not in txt.lower().replace("aptos", "")
    r = _run(tmp_path, settings, "replica", confirm_tranche=True)
    assert "CAGR" not in r.read_text(encoding="utf-8")
    _run(tmp_path, settings, "holdout_old", confirm_tranche=True)
    new = _run(tmp_path, settings, "holdout_new", confirm_tranche=True).read_text(encoding="utf-8")
    assert "16a" in new and "16b" in new and "| 12 kill switch" in new
