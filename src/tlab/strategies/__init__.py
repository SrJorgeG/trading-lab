"""Estrategias: funciones PURAS (sin E/S, sin red, sin aleatoriedad)."""

from tlab.strategies import allocation, demo_sma, donchian_atr

SIGNAL_STRATEGIES = {
    "demo_sma": demo_sma.generate_signals,
    "donchian_atr": donchian_atr.generate_signals,
}
ALLOCATION_STRATEGIES = {
    "buy_hold": allocation.buy_hold,
    "faber_sma10m": allocation.faber_sma,
    "tsmom_12m": allocation.tsmom,
    "dual_momentum": allocation.dual_momentum,
}
