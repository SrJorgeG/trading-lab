"""Contraste yfinance ↔ Alpaca: lógica de comparación (sin red) y salida sin claves."""

import numpy as np
import pandas as pd
from conftest import make_bars

from tlab.data.crosscheck import compare_returns, results_table


def test_identical_series_ok():
    b = make_bars(600, seed=1, start="2016-01-01")
    r, det = compare_returns("SPY", "equity", b, b * 1.37, "2016-01-01", "2026-10-31")
    assert r.verdict == "OK" and r.best_lag == 0 and r.max_abs_diff_bp < 1e-6
    assert "SPY" in results_table([r])


def test_shifted_calendar_flagged():
    b = make_bars(600, seed=2, freq="D", start="2021-01-01")
    alp = b.copy()
    alp.index = alp.index + pd.Timedelta(days=1)
    r, _ = compare_returns("BTC/USD", "crypto", b, alp, "2021-01-01", "2026-10-31")
    assert r.verdict == "REVISAR" and r.best_lag != 0


def test_noisy_crypto_within_tolerance_and_equity_outside():
    b = make_bars(800, seed=3, freq="D", start="2021-01-01", vol=0.04)
    rng = np.random.default_rng(0)
    alp = b.copy()
    alp["close"] = b["close"] * np.exp(rng.normal(0, 0.0015, len(b)))
    r, _ = compare_returns("ETH/USD", "crypto", b, alp, "2021-01-01", "2026-10-31")
    assert r.verdict == "OK"
    r2, _ = compare_returns("SPY", "equity", b, alp, "2021-01-01", "2026-10-31")
    assert r2.verdict == "REVISAR"


def test_missing_days_and_empty():
    b = make_bars(600, seed=4, start="2016-01-01")
    alp = b.iloc[::2]
    r, _ = compare_returns("IEF", "equity", b, alp, "2016-01-01", "2026-10-31")
    assert r.verdict == "REVISAR" and "faltan" in r.reasons
    empty = b.iloc[:0]
    r, _ = compare_returns("DBC", "equity", b, empty, "2016-01-01", "2026-10-31")
    assert r.verdict == "REVISAR"


def test_script_skips_without_keys(monkeypatch, capsys, tmp_path):
    import importlib.util
    from pathlib import Path

    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # sin .env aquí
    import tlab.data.alpaca_source as src

    monkeypatch.setattr(src, "has_keys", lambda: False)
    p = Path(__file__).resolve().parents[1] / "scripts" / "check_alpaca_vs_yf.py"
    spec = importlib.util.spec_from_file_location("chk", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main(["--out", str(tmp_path / "out")]) == 0
    assert "Sin claves de Alpaca" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()
    syms = mod.candidate_symbols()
    for s in ("SPY", "QQQ", "IWM", "DIA", "EFA", "EEM", "IEF", "GLD", "DBC", "VNQ",
              "BTC/USD", "ETH/USD", "LTC/USD", "BCH/USD"):  # fmt: skip
        assert s in syms
