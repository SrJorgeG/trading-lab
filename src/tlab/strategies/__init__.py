"""Estrategias: funciones PURAS (sin E/S, sin red, sin aleatoriedad)."""

import pandas as pd

from tlab.strategies import allocation, demo_sma, donchian_atr, rsi2_etf, tsmom_etf
from tlab.strategies.base import PanelSignalFn, as_panel

SIGNAL_STRATEGIES = {
    "demo_sma": demo_sma.generate_signals,
    "donchian_atr": donchian_atr.generate_signals,
    # Candidatas pre-registradas (docs/hipotesis.md). H1 y H4 reutilizan el módulo Donchian.
    "donchian_crypto": donchian_atr.generate_signals,
    "donchian_etf": donchian_atr.generate_signals,
    "tsmom_etf": tsmom_etf.generate_signals,
    "rsi2_etf": rsi2_etf.generate_signals,
}
# Ronda 2: estrategias que miran varios activos a la vez (ranking de panel). Se registran en
# `strategies/sector_rank.py` (R2-7) para no crear importaciones circulares.
PANEL_STRATEGIES: dict[str, PanelSignalFn] = {}
# Ids pre-registradas: sus fechas OOS están protegidas (ver backtest/runner.py).
CANDIDATES = ("donchian_crypto", "tsmom_etf", "rsi2_etf", "donchian_etf")
# Ronda 2 (H6 `tom_etf` aparcada, E15: no se registra).
CANDIDATES_R2 = ("sector_mom", "sector_lowvol")
# Estrategias que necesitan un calendario inyectado (solo H6; vacío mientras esté aparcada).
NEEDS_SESSIONS: tuple[str, ...] = ()
ALLOCATION_STRATEGIES = {
    "buy_hold": allocation.buy_hold,
    "faber_sma10m": allocation.faber_sma,
    "tsmom_12m": allocation.tsmom,
    "dual_momentum": allocation.dual_momentum,
}


def is_signal_strategy(strategy: str) -> bool:
    """True si la estrategia se simula con señales (por activo o de panel)."""
    return strategy in SIGNAL_STRATEGIES or strategy in PANEL_STRATEGIES


def resolve_signal_fn(strategy: str, sessions: pd.DatetimeIndex | None = None) -> PanelSignalFn:
    """Función de panel para cualquier estrategia por señales. Las de PANEL_STRATEGIES se
    devuelven tal cual; las de SIGNAL_STRATEGIES, envueltas con `as_panel`. Si la estrategia
    está en NEEDS_SESSIONS, exige `sessions` (ValueError si falta) y lo añade a una COPIA de
    `params` en cada llamada: el `params` del llamador (hash, registro) nunca lo contiene."""
    if strategy in PANEL_STRATEGIES:
        return PANEL_STRATEGIES[strategy]
    if strategy not in SIGNAL_STRATEGIES:
        raise KeyError(f"estrategia por señales desconocida: {strategy}")
    extra = None
    if strategy in NEEDS_SESSIONS:
        if sessions is None:
            raise ValueError(f"{strategy} necesita `sessions` (calendario inyectado).")
        extra = {"sessions": sessions}
    return as_panel(SIGNAL_STRATEGIES[strategy], extra)
