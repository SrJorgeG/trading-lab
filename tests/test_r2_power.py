"""R2-19: el test de potencia sintético funciona y es reproducible (N pequeño, sin red)."""

from __future__ import annotations

import pandas as pd

from tlab.backtest.power_test import (
    BENCH,
    NAMES,
    pass_rates,
    run_power,
    synthetic_series,
)


def test_series_sinteticas_forma_y_semilla():
    a = synthetic_series(0.0004, 1, n_days=300)
    b = synthetic_series(0.0004, 1, n_days=300)
    assert set(a) == set(NAMES) | {BENCH}
    pd.testing.assert_frame_equal(a["S1"], b["S1"])
    assert not a["S1"].equals(synthetic_series(0.0004, 2, n_days=300)["S1"])


def test_run_power_reproducible(settings):
    kw = dict(n_monkeys=20, seed=42, n_days=900, n_jobs=1)
    d1 = run_power(0.0004, 1, settings, **kw)
    d2 = run_power(0.0004, 1, settings, **kw)
    pd.testing.assert_frame_equal(d1, d2)
    assert set(pass_rates(d1).index) == {"c0", "c3", "c16", "c17", "c14", "todos"}
