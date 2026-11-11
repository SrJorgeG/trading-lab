"""Estrategias: funciones PURAS (sin E/S, sin red, sin aleatoriedad)."""

from tlab.strategies import allocation, demo_sma, donchian_atr, rsi2_etf, tsmom_etf

SIGNAL_STRATEGIES = {
    "demo_sma": demo_sma.generate_signals,
    "donchian_atr": donchian_atr.generate_signals,
    # Candidatas pre-registradas (docs/hipotesis.md). H1 y H4 reutilizan el módulo Donchian.
    "donchian_crypto": donchian_atr.generate_signals,
    "donchian_etf": donchian_atr.generate_signals,
    "tsmom_etf": tsmom_etf.generate_signals,
    "rsi2_etf": rsi2_etf.generate_signals,
}
# Ids pre-registradas: sus fechas OOS están protegidas (ver backtest/runner.py).
CANDIDATES = ("donchian_crypto", "tsmom_etf", "rsi2_etf", "donchian_etf")
ALLOCATION_STRATEGIES = {
    "buy_hold": allocation.buy_hold,
    "faber_sma10m": allocation.faber_sma,
    "tsmom_12m": allocation.tsmom,
    "dual_momentum": allocation.dual_momentum,
}
