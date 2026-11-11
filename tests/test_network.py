"""Opcionales: descargan datos reales (uv run pytest -m network)."""

import pytest

from tlab.data.yf_source import YFinanceSource


@pytest.mark.network
@pytest.mark.parametrize("sym,ac", [("SPY", "equity"), ("BTC/USD", "crypto")])
def test_yfinance_download_5_days(sym, ac):
    import pandas as pd

    end = pd.Timestamp.now(tz="UTC").normalize()
    df = YFinanceSource().fetch(sym, "1Day", end - pd.Timedelta(days=10), end, ac)
    assert len(df) >= 3 and df.index.tz is not None
