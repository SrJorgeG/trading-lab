"""Guardia: el código que hable con el broker se niega a arrancar si no es PAPER."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

PAPER_URL = "https://paper-api.alpaca.markets"
LIVE_HOSTS = ("api.alpaca.markets",)


class LiveTradingRefused(RuntimeError):
    """Se ha detectado configuración de dinero real."""


def assert_paper_only(
    env: Mapping[str, str] | None = None,
    base_url: str | None = None,
    paper: bool = True,
    kill_switch_file: Path | None = None,
) -> None:
    """Lanza LiveTradingRefused si ALPACA_PAPER_TRADE != 'true', si la URL no es la de paper
    o si paper=False. (El KILL_SWITCH se comprueba aparte en el ejecutor.)"""
    env = os.environ if env is None else env
    if env.get("ALPACA_PAPER_TRADE") != "true":
        raise LiveTradingRefused("ALPACA_PAPER_TRADE debe ser exactamente 'true'")
    for url in (base_url, env.get("ALPACA_BASE_URL"), env.get("APCA_API_BASE_URL")):
        if url and url.rstrip("/").removesuffix("/v2") != PAPER_URL:
            raise LiveTradingRefused(f"URL de broker no permitida (solo {PAPER_URL})")
    if paper is not True:
        raise LiveTradingRefused("TradingClient con paper=False no permitido")
