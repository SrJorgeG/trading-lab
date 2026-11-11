"""Simulador de asignación por pesos (BASELINES mensuales y buy & hold).

NO aplica las reglas de 1 % de riesgo / stop (estas estrategias no tienen stop por operación):
sirve como referencia. Pesos decididos con datos <= fin de mes se ejecutan a la apertura de la
primera vela del mes siguiente, con costes; solo se opera cuando cambia el peso objetivo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tlab.backtest.costs import CostModel
from tlab.config import asset_class_of


def simulate_weights(
    bars: dict[str, pd.DataFrame],
    weights: pd.DataFrame,
    costs: dict[str, CostModel],
    initial_equity: float = 10_000.0,
    start=None,
    fractional: bool = True,
) -> tuple[pd.Series, pd.DataFrame]:
    """Devuelve (equity diaria, operaciones). `weights` indexado por la vela de decisión."""
    syms = list(weights.columns)
    opens = pd.DataFrame({s: bars[s]["open"] for s in syms})
    closes = pd.DataFrame({s: bars[s]["close"] for s in syms})
    idx = closes.index
    if start is not None:
        idx = idx[idx >= pd.Timestamp(start, tz="UTC")]
    closes_ff = closes.ffill()
    # Señal en la vela de decisión d -> ejecución en la siguiente vela del calendario.
    pos_in_cal = {d: i for i, d in enumerate(closes.index)}
    exec_map = {}
    for d in weights.index:
        i = pos_in_cal.get(d)
        if i is not None and i + 1 < len(closes.index):
            exec_map[closes.index[i + 1]] = weights.loc[d]
    cash, qty = initial_equity, dict.fromkeys(syms, 0.0)
    cur_w = None
    eq, trades = [], []
    for t in idx:
        if t in exec_map:
            w = exec_map[t].fillna(0.0)
            if cur_w is None or not np.allclose(w.values, cur_w.values):
                px_o = opens.loc[t]
                if px_o[w[w > 0].index].isna().any():
                    pass  # algún activo sin vela hoy: se espera al siguiente rebalanceo
                else:
                    val = cash + sum(
                        qty[s] * (px_o[s] if pd.notna(px_o[s]) else closes_ff.loc[t, s])
                        for s in syms
                        if qty[s]
                    )
                    # Ventas primero, luego compras.
                    for side in ("sell", "buy"):
                        for s in syms:
                            if pd.isna(px_o[s]):
                                continue
                            cm = costs[asset_class_of(s)]
                            target = w[s] * val / px_o[s]
                            if not fractional:
                                target = np.floor(target)
                            d_q = target - qty[s]
                            if (side == "sell" and d_q < -1e-12) or (side == "buy" and d_q > 1e-12):
                                fill = cm.fill_price(px_o[s], side)
                                if side == "buy":
                                    # que la caja alcance incluyendo costes
                                    d_q = min(
                                        d_q,
                                        cash / (fill * (1 + cm.fee_rate) + cm.commission_per_share),
                                    )
                                comm = cm.commission(d_q, fill)
                                cash -= d_q * fill + comm
                                qty[s] += d_q
                                trades.append(
                                    {
                                        "date": t,
                                        "symbol": s,
                                        "side": side,
                                        "qty": d_q,
                                        "price": fill,
                                        "commission": comm,
                                    }
                                )
                    cur_w = w
        eq.append(cash + sum(qty[s] * closes_ff.loc[t, s] for s in syms if qty[s]))
    return pd.Series(eq, index=idx, name="equity"), pd.DataFrame(trades)
