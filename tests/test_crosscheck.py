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


def test_attach_dividends_and_overlap():
    from tlab.data.crosscheck import attach_dividends, exdiv_overlap_stats

    idx = pd.date_range("2016-01-04", periods=5, freq="B", tz="UTC")
    det = pd.DataFrame(
        {
            "ret_yf": [0.01, 0.02, -0.01, 0.0, 0.01],
            "ret_alpaca": [0.01, 0.015, -0.01, 0.0, 0.01],
            "abs_diff": [0.0, 0.005, 0.0, 0.0, 0.0005],
        },
        index=idx,
    )
    # Fecha naive (como suelen venir los dividendos de yfinance) = el 2.º día.
    divs = pd.Series([0.42], index=pd.DatetimeIndex(["2016-01-05"]))
    out = attach_dividends(det, divs)
    day, prev = pd.Timestamp("2016-01-05"), pd.Timestamp("2016-01-04")
    assert out.index.tz is None
    assert bool(out.loc[day, "is_exdiv"]) is True
    assert out.loc[day, "div_amount"] == 0.42
    assert bool(out.loc[prev, "is_exdiv"]) is False
    assert out.loc[day, "abs_diff_bp"] == 50
    stats = exdiv_overlap_stats(out, tol=0.001)
    assert stats["n_over"] == 1 and stats["n_exdiv"] == 1
    assert stats["n_over_and_exdiv"] == 1
    assert stats["share_over_that_are_exdiv"] == 1.0
    assert stats["share_exdiv_that_are_over"] == 1.0
    empty = attach_dividends(det, pd.Series(dtype=float))
    assert not empty["is_exdiv"].any()


def test_alpaca_source_adjustment_cache_path(tmp_path):
    from tlab.data.alpaca_source import AlpacaSource
    from tlab.data.loader import cache_path

    a, b = AlpacaSource(), AlpacaSource(adjustment="split")
    assert a.adjustment == "all" and b.adjustment == "split"
    p1, p2 = cache_path(tmp_path, a, "SPY", "1Day"), cache_path(tmp_path, b, "SPY", "1Day")
    assert "all" in p1.name and "split" in p2.name and p1 != p2
    try:
        AlpacaSource(adjustment="nope")
        raise AssertionError("debería rechazar el ajuste")
    except ValueError:
        pass


def test_diag_script_skips_without_keys(monkeypatch, capsys, tmp_path):
    import importlib.util
    from pathlib import Path

    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    import tlab.data.alpaca_source as src

    monkeypatch.setattr(src, "has_keys", lambda: False)
    p = Path(__file__).resolve().parents[1] / "scripts" / "diag_alpaca_vs_yf.py"
    spec = importlib.util.spec_from_file_location("diag_alp", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main(["--out", str(tmp_path / "out")]) == 0
    assert "Sin claves de Alpaca" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_compare_returns_object_and_tz_aware_indexes():
    """Reproduce el crash del diagnóstico: un índice object/str y otro tz-aware."""
    b = make_bars(600, seed=1, start="2016-01-01")
    assert b.index.tz is not None
    left = b.copy()
    right = (b * 1.37).copy()
    right.index = pd.Index(right.index.strftime("%Y-%m-%d"))
    assert not isinstance(right.index, pd.DatetimeIndex)
    assert not hasattr(right.index, "tz") or right.index.tz is None
    r, det = compare_returns("SPY", "equity", left, right, "2016-01-01", "2026-10-31")
    assert r.verdict == "OK" and r.best_lag == 0 and r.max_abs_diff_bp < 1e-6
    assert isinstance(det.index, pd.DatetimeIndex) and det.index.tz is None
    # El otro sentido (object a la izquierda, tz-aware a la derecha) también.
    r2, det2 = compare_returns("SPY", "equity", right, left, "2016-01-01", "2026-10-31")
    assert r2.verdict == "OK" and r2.best_lag == 0 and det2.index.tz is None
