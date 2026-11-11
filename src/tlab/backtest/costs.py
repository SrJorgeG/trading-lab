"""Costes por lado: comisión + slippage (incluye spread), con multiplicador de estrés."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    slippage_bps: float = 0.0  # por lado, en contra
    fee_rate: float = 0.0  # % del nominal por lado (cripto)
    commission_per_share: float = 0.0

    def scaled(self, mult: float) -> CostModel:
        return CostModel(
            self.slippage_bps * mult, self.fee_rate * mult, self.commission_per_share * mult
        )

    @property
    def slip(self) -> float:
        return self.slippage_bps / 10_000

    def fill_price(self, price: float, side: str) -> float:
        """Precio con slippage en contra: compra más cara, venta más barata."""
        return price * (1 + self.slip) if side == "buy" else price * (1 - self.slip)

    def commission(self, qty: float, fill_price: float) -> float:
        return abs(qty) * self.commission_per_share + abs(qty) * fill_price * self.fee_rate


def cost_models(settings: dict, mode: str = "base") -> dict[str, CostModel]:
    """Modelos de coste por clase de activo; mode = base, stress o zero."""
    c = settings["costs"]
    eq = CostModel(
        slippage_bps=c["equity"]["slippage_bps"],
        commission_per_share=c["equity"]["commission_per_share"],
    )
    cr = CostModel(slippage_bps=c["crypto"]["slippage_bps"], fee_rate=c["crypto"]["fee_rate"])
    if mode == "zero":
        return {"equity": CostModel(), "crypto": CostModel()}
    mult = c["stress"]["multiplier"] if mode == "stress" else 1.0
    return {"equity": eq.scaled(mult), "crypto": cr.scaled(mult)}
