"""Monte Carlo: reproducibilidad, invariantes, formas y un caso sintético del kill switch."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.backtest.montecarlo import (
    MCConfig,
    block_bootstrap_returns,
    luck_comment,
    run_montecarlo,
    stats_table,
    write_outputs,
)


def _equity_from_pnls(pnls, start="2020-01-01", initial=10_000.0, freq="B"):
    idx = pd.date_range(start, periods=len(pnls) + 1, freq=freq, tz="UTC")
    eq = pd.Series(np.concatenate([[initial], initial + np.cumsum(pnls)]), index=idx)
    trades = pd.DataFrame(
        {
            "pnl_usd": pnls,
            "pnl_r": np.array(pnls) / (0.01 * initial),
            "entry_date": idx[:-1],
            "exit_date": idx[1:],
        }
    )
    return eq, trades


def test_reproducible_with_seed():
    eq, tr = _equity_from_pnls([100, -50, 80, -20, 40, -10, 30])
    cfg = MCConfig(n=200, seed=42, method="bootstrap")
    a = run_montecarlo(eq, tr, cfg)
    b = run_montecarlo(eq, tr, cfg)
    np.testing.assert_array_equal(a.final_equity, b.final_equity)
    np.testing.assert_array_equal(a.max_dd, b.max_dd)
    np.testing.assert_array_equal(a.sample_paths, b.sample_paths)
    c = run_montecarlo(eq, tr, MCConfig(n=200, seed=7, method="bootstrap"))
    assert not np.array_equal(a.final_equity, c.final_equity)


def test_shuffle_preserves_final_equity_additive():
    pnls = [200.0, -80.0, 50.0, -10.0, 120.0, -40.0]
    eq, tr = _equity_from_pnls(pnls, initial=10_000.0)
    res = run_montecarlo(eq, tr, MCConfig(n=500, seed=42, method="shuffle", sizing="additive"))
    expected = 10_000.0 + sum(pnls)
    np.testing.assert_allclose(res.final_equity, expected)
    np.testing.assert_allclose(res.real["final_equity"], expected)
    # El CAGR, al anualizarse con el mismo periodo, también es idéntico.
    assert np.unique(np.round(res.cagr, 12)).size == 1


def test_shuffle_preserves_final_equity_compound():
    pnls = [200.0, -80.0, 50.0, -10.0, 120.0]
    eq, tr = _equity_from_pnls(pnls, initial=10_000.0)
    res = run_montecarlo(eq, tr, MCConfig(n=300, seed=1, method="shuffle", sizing="compound"))
    factors = 1.0 + 0.01 * tr["pnl_r"].to_numpy()
    expected = 10_000.0 * np.prod(factors)
    np.testing.assert_allclose(res.final_equity, expected, rtol=1e-12)


def test_bootstrap_shapes_and_variance():
    pnls = [100.0, -40.0, 70.0, -20.0, 50.0, -15.0, 30.0]
    eq, tr = _equity_from_pnls(pnls, initial=10_000.0)
    res = run_montecarlo(eq, tr, MCConfig(n=2000, seed=42, method="bootstrap"))
    assert res.final_equity.shape == (2000,)
    assert res.max_dd.shape == (2000,)
    assert res.cagr.shape == (2000,)
    assert res.bands.shape[0] == len(pnls) + 1
    assert res.sample_paths.shape[1] == len(pnls) + 1
    # Con reemplazo el equity final ya no es constante.
    assert res.final_equity.std() > 0
    expected_mean = 10_000.0 + len(pnls) * np.mean(pnls)
    assert res.final_equity.mean() == pytest.approx(expected_mean, rel=0.05)


def test_percentiles_monotonic():
    rng = np.random.default_rng(0)
    pnls = rng.normal(20, 80, 25)
    eq, tr = _equity_from_pnls(pnls)
    for method in ("shuffle", "bootstrap"):
        res = run_montecarlo(eq, tr, MCConfig(n=400, seed=0, method=method))
        b = res.bands
        assert (b["p5"] <= b["p25"] + 1e-9).all()
        assert (b["p25"] <= b["p50"] + 1e-9).all()
        assert (b["p50"] <= b["p75"] + 1e-9).all()
        assert (b["p75"] <= b["p95"] + 1e-9).all()
        st = stats_table(res)
        for _, row in st[st["kind"].isin(["usd", "pct", "days"])].iterrows():
            qs = [row["p5"], row["p25"], row["p50"], row["p75"], row["p95"]]
            assert qs == sorted(qs)


def test_kill_switch_probability_synthetic():
    """Un único pérdida de -1.100 $ y tres ganancias de +500 $; capital 10.000 $.

    Posición de la pérdida (sizing aditivo, kill switch > 10 % desde el máximo):
    - 1.ª operación: 11,00 % → salta
    - 2.ª (después de +500): 10,48 % → salta
    - 3.ª (después de +1.000): 10,00 % exacto → NO salta (la regla es estrictamente mayor)
    - 4.ª (después de +1.500): 9,57 % → no salta
    Las 4 posiciones son igualmente probables al barajar, así que P = 1/2.
    """
    pnls = [500.0, 500.0, 500.0, -1100.0]
    eq, tr = _equity_from_pnls(pnls, initial=10_000.0)
    res = run_montecarlo(eq, tr, MCConfig(n=4000, seed=42, method="shuffle", kill_switch=0.10))
    assert res.p_kill == pytest.approx(0.5, abs=0.03)
    # El camino original termina +400 y la pérdida va al final: no salta.
    assert res.real["hit_kill"] is False


def test_block_bootstrap_length_and_first_block():
    rets = np.arange(20, dtype=float) / 100.0  # valores únicos, fáciles de reconocer
    n, block, seed = 50, 5, 123
    boot = block_bootstrap_returns(rets, n=n, block=block, seed=seed)
    assert boot.shape == (n, len(rets))
    # Cada bloque de `block` columnas (salvo el recorte final) es una ventana real.
    n_blocks = int(np.ceil(len(rets) / block))
    for i in range(n):
        for b in range(n_blocks):
            sl = boot[i, b * block : (b + 1) * block]
            if len(sl) < block:
                continue
            windows = range(0, len(rets) - block + 1)
            found = any(np.array_equal(sl, rets[s : s + block]) for s in windows)
            assert found, f"sim {i} bloque {b} no es una ventana real"
    # Misma semilla = misma matriz.
    boot2 = block_bootstrap_returns(rets, n=n, block=block, seed=seed)
    np.testing.assert_array_equal(boot, boot2)
    with pytest.raises(ValueError, match="no puede ser mayor"):
        block_bootstrap_returns(rets, n=2, block=50, seed=0)


def test_block_method_on_daily_equity():
    idx = pd.date_range("2018-01-01", periods=260, freq="B", tz="UTC")
    rng = np.random.default_rng(1)
    r = rng.normal(0.0004, 0.01, len(idx) - 1)
    eq = pd.Series(10_000 * np.cumprod(np.concatenate([[1.0], 1 + r])), index=idx)
    res = run_montecarlo(eq, None, MCConfig(n=300, seed=42, method="block", block_length=10))
    assert res.bands.shape[0] == len(eq)
    assert res.final_equity.std() > 0
    assert 0 <= res.p_kill <= 1
    # Bandas monótonas
    assert (res.bands["p5"] <= res.bands["p95"] + 1e-9).all()


def test_trade_methods_need_closed_trades():
    idx = pd.date_range("2020-01-01", periods=10, freq="B", tz="UTC")
    eq = pd.Series(np.linspace(100, 110, 10), index=idx)
    with pytest.raises(ValueError, match="operaciones cerradas"):
        run_montecarlo(eq, None, MCConfig(method="shuffle", n=10))


def test_write_outputs(tmp_path):
    eq, tr = _equity_from_pnls([100, -40, 60, -20, 30])
    cfg = MCConfig(n=80, seed=0, method="bootstrap")
    res = run_montecarlo(eq, tr, cfg)
    paths = write_outputs(res, tmp_path, "prueba", cfg, html=True, png=True)
    assert paths["md"].exists() and "Monte Carlo" in paths["md"].read_text(encoding="utf-8")
    assert paths["csv"].exists()
    assert paths["html"].exists() and paths["html"].stat().st_size > 1000
    assert paths["png"].exists() and paths["png"].stat().st_size > 1000
    text = luck_comment(res)
    assert isinstance(text, str) and len(text) > 20
