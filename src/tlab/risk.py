"""Sizing, límites y kill switch. Compartido por el backtest y el ejecutor diario."""

from __future__ import annotations

import math
from collections.abc import Iterable

from tlab.backtest.costs import CostModel

CRYPTO_QTY_STEP = 1e-6  # precisión de cantidad usada para cripto (conservadora)


def floor_qty(qty: float, asset_class: str, allow_fractional: bool) -> float:
    """Redondea SIEMPRE hacia abajo: enteros en ETFs, CRYPTO_QTY_STEP en cripto."""
    if qty <= 0:
        return 0.0
    if asset_class == "crypto" or allow_fractional:
        step = CRYPTO_QTY_STEP
        return math.floor(qty / step + 1e-9) * step
    return float(math.floor(qty + 1e-9))


def risk_per_unit(entry_price: float, stop_price: float, costs: CostModel) -> float:
    """Pérdida por unidad si salta el stop, con slippage y comisiones de entrada y salida.
    `entry_price` y `stop_price` son precios de referencia (sin slippage)."""
    e = costs.fill_price(entry_price, "buy")
    s = costs.fill_price(stop_price, "sell")
    return (e - s) + costs.commission(1, e) + costs.commission(1, s)


def position_size(
    equity: float,
    entry_price: float,
    stop_price: float,
    risk_pct: float,
    costs: CostModel,
    asset_class: str = "equity",
    allow_fractional: bool = False,
) -> float:
    """Cantidad tal que la pérdida al stop (con costes) <= risk_pct × equity. 0 = no operar."""
    if not (stop_price > 0 and entry_price > stop_price and equity > 0):
        return 0.0
    rpu = risk_per_unit(entry_price, stop_price, costs)
    if rpu <= 0:
        return 0.0
    return floor_qty(risk_pct * equity / rpu, asset_class, allow_fractional)


def apply_limits(
    qty: float,
    price: float,
    costs: CostModel,
    cash: float,
    equity: float,
    gross_exposure: float,
    n_open: int,
    max_positions: int,
    max_gross_exposure: float,
    asset_class: str = "equity",
    allow_fractional: bool = False,
    max_position_fraction: float | None = None,
) -> float:
    """Recorta la cantidad para respetar: máx. posiciones, exposición bruta <= límite × equity,
    caja disponible (incluida la comisión) y, si se indica, coste de la posición (con slippage y
    comisión de entrada) <= `max_position_fraction` × equity (tope equity/3 de hipotesis.md §2).
    Devuelve la cantidad final (puede ser 0)."""
    if n_open >= max_positions or qty <= 0:
        return 0.0
    fill = costs.fill_price(price, "buy")
    unit_cost = fill + costs.commission(1, fill)
    room = min(cash, max_gross_exposure * equity - gross_exposure)
    if max_position_fraction is not None:
        room = min(room, max_position_fraction * equity)
    if room <= 0:
        return 0.0
    qty = min(qty, room / unit_cost)
    return floor_qty(qty, asset_class, allow_fractional)


def check_kill_switch(
    equity_history_or_peak: float | Iterable[float], equity_now: float, threshold: float = 0.10
) -> bool:
    """True si el equity actual ha caído MÁS de `threshold` desde su máximo."""
    if isinstance(equity_history_or_peak, (int, float)):
        peak = float(equity_history_or_peak)
    else:
        peak = max(list(equity_history_or_peak) + [equity_now])
    peak = max(peak, equity_now)
    return equity_now < peak * (1 - threshold)
