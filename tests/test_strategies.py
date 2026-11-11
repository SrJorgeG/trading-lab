"""Casos a mano de las estrategias implementadas (baselines y demo).

Cuando exista docs/hipotesis.md §6, añadir aquí test_strategy_<id>_cases por candidata.
"""

import numpy as np
import pandas as pd
import pytest
from conftest import flat_bars

from tlab.strategies.allocation import dual_momentum, faber_sma, monthly_closes, tsmom
from tlab.strategies.demo_sma import generate_signals as demo
from tlab.strategies.donchian_atr import generate_signals as donchian


def test_strategy_donchian_atr_cases():
    # 25 velas planas (H=101, L=99) y luego ruptura con cierre 105.
    rows = [(100, 101, 99, 100)] * 25 + [(100, 106, 100, 105)] + [(105, 106, 104, 105)] * 3
    rows += [(100, 100, 95, 96)]  # cierre 96 < mínimo de 10 velas previas (99) -> salida
    b = flat_bars(rows)
    s = donchian(b, {"entry_n": 20, "exit_n": 10, "atr_mult": 2.0, "atr_n": 20})
    assert not s["entry"].iloc[:25].any()
    assert s["entry"].iloc[25]
    atr = s["stop_price"].iloc[25]
    assert atr < 105 and np.isfinite(atr)
    # Las velas 26-28 tienen high 106 = máximo previo -> close 105 no supera 106 -> sin entrada.
    assert not s["entry"].iloc[26:29].any()
    assert s["exit"].iloc[29]


def test_strategy_demo_sma_cases():
    up = [(p, p + 1, p - 1, p) for p in np.linspace(100, 130, 40)]
    down = [(p, p + 1, p - 1, p) for p in np.linspace(130, 90, 40)]
    b = flat_bars(up + down)
    s = demo(b, {"fast": 5, "slow": 20})
    assert s["entry"].sum() >= 1 and s["exit"].sum() >= 1
    assert s.index[s["entry"]].min() < s.index[s["exit"]].min()


def _monthly(values, cols):
    idx = pd.date_range("2018-01-31", periods=len(values), freq="ME", tz="UTC")
    return pd.DataFrame(values, index=idx, columns=cols, dtype=float)


def test_strategy_faber_cases():
    c = _monthly([[100]] * 10 + [[110], [90]], ["SPY"])
    w = faber_sma(c, {"months": 10})
    assert w["SPY"].iloc[9] == 0  # cierre = media -> no estrictamente por encima
    assert w["SPY"].iloc[10] == 1.0  # 110 > media(100×9,110)=101
    assert w["SPY"].iloc[11] == 0.0  # 90 < media


def test_strategy_tsmom_cases():
    c = _monthly([[100]] + [[100]] * 11 + [[120], [80]], ["SPY"])
    w = tsmom(c, {"months": 12})
    assert w["SPY"].iloc[11] == 0
    assert w["SPY"].iloc[12] == 1.0 and w["SPY"].iloc[13] == 0.0


@pytest.mark.parametrize(
    "spy,efa,bil,expect",
    [
        (130, 120, 101, "SPY"),
        (110, 125, 101, "EFA"),
        (99, 98, 101, "IEF"),
        (101.5, 101, 102, "IEF"),
    ],
)
def test_strategy_dual_momentum_cases(spy, efa, bil, expect):
    vals = [[100, 100, 100, 100]] * 12 + [[spy, efa, 100, bil]]
    c = _monthly(vals, ["SPY", "EFA", "IEF", "BIL"])
    w = dual_momentum(c, {})
    assert w.iloc[-1][expect] == 1.0 and w.iloc[-1].sum() == 1.0


def test_monthly_closes_uses_last_bar_of_month():
    idx = pd.to_datetime(
        ["2020-01-30", "2020-01-31", "2020-02-27", "2020-02-28", "2020-03-02"]
    ).tz_localize("UTC")
    c = pd.DataFrame({"SPY": [1, 2, 3, 4, 5.0]}, index=idx)
    m = monthly_closes(c)
    assert list(m["SPY"]) == [2, 4, 5]


def test_tsmom_skip_default_and_validation():
    import pandas as pd
    import pytest
    from conftest import make_bars

    from tlab.strategies.allocation import monthly_closes, tsmom

    c = pd.DataFrame({"SPY": make_bars(800, seed=9)["close"]})
    base = tsmom(c, {"months": 12})
    assert base.equals(tsmom(c, {"months": 12, "skip": 0}))
    m = monthly_closes(c)
    r = m.shift(1) / m.shift(12) - 1
    exp = (r > 0).astype(float).where(r.notna(), 0.0)
    pd.testing.assert_frame_equal(tsmom(c, {"months": 12, "skip": 1}), exp)
    with pytest.raises(ValueError):
        tsmom(c, {"months": 3, "skip": 3})
