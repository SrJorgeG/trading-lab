"""Carga de configuración TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


# Techo de las reglas duras de CLAUDE.md (solo Jorge puede cambiarlas). Lo configurable puede
# ser MÁS estricto, nunca más laxo.
HARD_LIMITS = {
    "kill_switch_drawdown": 0.15,
    "risk_per_trade": 0.01,
    "max_positions": 3,
    "max_gross_exposure": 1.0,
}


class HardRuleError(ValueError):
    """Un valor de configuración supera el techo de una regla dura."""


def validate_settings(s: dict) -> dict:
    """Lanza HardRuleError si algún valor de [risk] supera el techo de las reglas duras
    (o es <= 0). Devuelve `s` sin cambios."""
    risk = s.get("risk", {})
    for key, ceiling in HARD_LIMITS.items():
        if key not in risk:
            continue
        v = risk[key]
        if v <= 0:
            raise HardRuleError(f"[risk] {key} = {v}: debe ser > 0.")
        if v > ceiling + 1e-12:
            raise HardRuleError(
                f"[risk] {key} = {v} supera el techo de la regla dura ({ceiling}). "
                "Solo Jorge puede cambiarlo, con una enmienda fechada en CLAUDE.md."
            )
    return s


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Lee config/settings.toml y valida el techo de las reglas duras."""
    p = path or CONFIG_DIR / "settings.toml"
    with open(p, "rb") as f:
        return validate_settings(tomllib.load(f))


def load_strategy_config(strategy_id: str, path: Path | None = None) -> dict[str, Any]:
    """Lee config/strategies/<id>.toml."""
    p = path or CONFIG_DIR / "strategies" / f"{strategy_id}.toml"
    with open(p, "rb") as f:
        return tomllib.load(f)


def asset_class_of(symbol: str) -> str:
    """'crypto' si el símbolo es tipo BTC/USD o BTC-USD; si no, 'equity'."""
    s = symbol.upper()
    return "crypto" if ("/" in s or s.endswith("-USD")) else "equity"
