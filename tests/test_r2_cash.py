"""R2-4: benchmark de caja (casos a mano CA1–CA7 de docs/especificaciones_ronda2.md)."""

from __future__ import annotations

import pandas as pd
import pytest

from tlab import metrics
from tlab.data.cash import cash_equity, discount_to_yield


def _bdays(a: str, b: str) -> pd.DatetimeIndex:
    return pd.date_range(a, b, freq="B", tz="UTC")


def _const(idx, v):
    return pd.Series(v, index=idx)


def test_ca1_descuento_a_rentabilidad():
    assert discount_to_yield(0.05) == pytest.approx(0.0513434, abs=1e-7)


def test_ca2_serie_constante_da_su_cagr():
    idx = _bdays("2020-01-01", "2025-01-01")
    eq = cash_equity(_const(idx, 0.05), idx, 10_000.0)
    assert metrics.cagr(eq) == pytest.approx(0.05, abs=1e-9)
    assert eq.iloc[-1] == pytest.approx(12_764.09, abs=0.01)


def test_ca3_con_conversion():
    idx = _bdays("2020-01-01", "2025-01-01")
    y = discount_to_yield(0.05)
    eq = cash_equity(_const(idx, y), idx, 10_000.0)
    assert metrics.cagr(eq) == pytest.approx(0.0513434, abs=1e-7)


def _ca4():
    idx = pd.DatetimeIndex(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-08"], tz="UTC")
    return idx, pd.Series([0.05, 0.05, 0.10, 0.10], index=idx)


def test_ca4_usa_el_tipo_de_la_sesion_anterior():
    idx, r = _ca4()
    eq = cash_equity(r, idx, 10_000.0)
    assert list(eq.round(4)) == [10000.0, 10001.3359, 10002.6720, 10013.1180]


def test_ca5_nan_se_arrastra():
    idx, r = _ca4()
    r.iloc[1] = float("nan")
    eq = cash_equity(r, idx, 10_000.0)
    assert list(eq.round(4)) == [10000.0, 10001.3359, 10002.6720, 10013.1180]


def test_ca6_sin_tipo_en_el_primer_dia():
    idx, r = _ca4()
    with pytest.raises(ValueError):
        cash_equity(r.iloc[1:], idx, 10_000.0)


def test_ca7_sin_mirar_al_futuro():
    idx = _bdays("2024-01-01", "2024-03-29")
    base = pd.Series(0.04, index=idx)
    t = idx[30]
    alt = base.copy()
    alt[alt.index > t] = 0.40
    a = cash_equity(base, idx, 10_000.0)
    b = cash_equity(alt, idx, 10_000.0)
    # Hasta t incluida y también t+1 (usa el tipo de t) no cambia nada.
    assert (a.iloc[:32] == b.iloc[:32]).all()
    assert a.iloc[33] != b.iloc[33]


def test_indice_vacio():
    idx = pd.DatetimeIndex([], tz="UTC")
    assert len(cash_equity(pd.Series(dtype=float), idx, 1.0)) == 0


@pytest.mark.network
def test_load_tbill_rate_network():
    from tlab.config import load_settings
    from tlab.data.cash import load_tbill_rate

    rate, info = load_tbill_rate(load_settings())
    assert rate.min() >= -0.01 and rate.max() <= 0.20
    assert info["max_gap_days"] <= 10
