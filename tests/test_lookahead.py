"""Anti look-ahead para TODAS las estrategias (señales y asignación)."""

import numpy as np
import pandas as pd
import pytest
from conftest import make_bars

from tlab.strategies import ALLOCATION_STRATEGIES, SIGNAL_STRATEGIES

SIG_PARAMS = {"demo_sma": {"fast": 10, "slow": 30}, "donchian_atr": {}}
CUTS = [150, 300, 451, 599]


def _closes(n=900):
    syms = ["SPY", "EFA", "IEF", "BIL"]
    return pd.DataFrame({s: make_bars(n, seed=i)["close"] for i, s in enumerate(syms)})


@pytest.mark.parametrize("sid", sorted(SIGNAL_STRATEGIES))
def test_no_lookahead_truncation(sid):
    b = make_bars(600, seed=3)
    full = SIGNAL_STRATEGIES[sid](b, SIG_PARAMS[sid])
    for t in CUTS:
        part = SIGNAL_STRATEGIES[sid](b.iloc[:t], SIG_PARAMS[sid])
        pd.testing.assert_frame_equal(part, full.iloc[:t])


@pytest.mark.parametrize("sid", sorted(SIGNAL_STRATEGIES))
def test_no_lookahead_poison(sid):
    b = make_bars(600, seed=4)
    full = SIGNAL_STRATEGIES[sid](b, SIG_PARAMS[sid])
    for t in CUTS[:-1]:
        for poison in ("x10", "nan"):
            p = b.copy()
            if poison == "x10":
                p.iloc[t:] = p.iloc[t:] * 10
            else:
                p.iloc[t:] = np.nan
            got = SIGNAL_STRATEGIES[sid](p, SIG_PARAMS[sid])
            pd.testing.assert_frame_equal(got.iloc[:t], full.iloc[:t])


def _completed_months(w: pd.DataFrame, cut_ts) -> pd.DataFrame:
    # Solo meses ya cerrados antes del mes de la vela de corte.
    m0 = pd.Timestamp(cut_ts).to_period("M")
    return w[w.index.tz_localize(None).to_period("M") < m0]


@pytest.mark.parametrize("sid", sorted(ALLOCATION_STRATEGIES))
def test_no_lookahead_truncation_allocation(sid):
    c = _closes()
    full = ALLOCATION_STRATEGIES[sid](c, {})
    for t in (300, 500, 777):
        part = ALLOCATION_STRATEGIES[sid](c.iloc[:t], {})
        a = _completed_months(part, c.index[t - 1])
        pd.testing.assert_frame_equal(a, full.loc[a.index])


@pytest.mark.parametrize("sid", sorted(ALLOCATION_STRATEGIES))
def test_no_lookahead_poison_allocation(sid):
    c = _closes()
    full = ALLOCATION_STRATEGIES[sid](c, {})
    t = 500
    p = c.copy()
    p.iloc[t:] = p.iloc[t:] * 10
    got = ALLOCATION_STRATEGIES[sid](p, {})
    a = _completed_months(full, c.index[t - 1])
    pd.testing.assert_frame_equal(got.loc[a.index], a)
