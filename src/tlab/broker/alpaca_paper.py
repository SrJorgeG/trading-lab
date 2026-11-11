"""Cliente de trading PAPER. Aún sin órdenes: lo completa el paso 5."""

from __future__ import annotations

import os

from tlab.broker.guard import assert_paper_only


def make_trading_client(paper: bool = True):
    """Crea TradingClient SOLO en paper (pasa siempre por la guardia)."""
    from dotenv import load_dotenv

    load_dotenv()
    assert_paper_only(paper=paper)
    from alpaca.trading.client import TradingClient

    return TradingClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"], paper=True)
