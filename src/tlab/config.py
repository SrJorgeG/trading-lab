"""Carga de configuración TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Lee config/settings.toml."""
    p = path or CONFIG_DIR / "settings.toml"
    with open(p, "rb") as f:
        return tomllib.load(f)


def load_strategy_config(strategy_id: str, path: Path | None = None) -> dict[str, Any]:
    """Lee config/strategies/<id>.toml."""
    p = path or CONFIG_DIR / "strategies" / f"{strategy_id}.toml"
    with open(p, "rb") as f:
        return tomllib.load(f)


def asset_class_of(symbol: str) -> str:
    """'crypto' si el símbolo es tipo BTC/USD o BTC-USD; si no, 'equity'."""
    s = symbol.upper()
    return "crypto" if ("/" in s or s.endswith("-USD")) else "equity"
