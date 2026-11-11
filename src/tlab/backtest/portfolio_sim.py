"""Simulador de cartera vela a vela (motor de REFERENCIA para el veredicto).

Orden de eventos en cada vela t (fechas = unión de calendarios; un activo solo actúa en sus velas):
 1. Liquidación por kill switch pendiente (detectado al cierre de t-1) → todo a la apertura de t.
 2. Posiciones abiertas: salida por señal de t-1 → apertura de t (− slippage).
    Si no: apertura <= stop (gap) → sale a la apertura; low <= stop → sale al stop.
    Stop y objetivo en la misma vela → gana el stop.
 3. Entradas pendientes (señales de t-1), ordenadas por rank desc y símbolo asc (determinista):
    se omite si apertura <= stop; sizing con risk.position_size sobre el equity a la apertura;
    luego risk.apply_limits (máx. posiciones, exposición, caja). Tras entrar se comprueba el stop
    dentro de la misma vela (low <= stop).
 4. Valoración al cierre; kill switch si equity < pico × (1 − umbral) → liquidación en t+1 y
    bloqueo permanente de entradas.
 5. Señales de la vela t (calculadas con datos <= t) quedan pendientes para t+1.
Al final de los datos, lo abierto se cierra al último cierre (motivo `end_of_data`, con costes).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from tlab.backtest.costs import CostModel
from tlab.config import asset_class_of
from tlab.risk import apply_limits, check_kill_switch, position_size


@dataclass
class SimConfig:
    initial_equity: float = 10_000.0
    risk_per_trade: float = 0.01
    max_positions: int = 3
    max_gross_exposure: float = 1.0
    kill_switch_drawdown: float | None = 0.10
    allow_fractional: bool = False
    costs: dict[str, CostModel] = field(
        default_factory=lambda: {"equity": CostModel(), "crypto": CostModel()}
    )
    entry_delay: int = 0  # velas extra de retraso (prueba de robustez)


@dataclass
class SimResult:
    equity: pd.Series
    trades: pd.DataFrame
    exposure: pd.Series
    n_open: pd.Series
    kill_switch_date: pd.Timestamp | None


TRADE_COLS = [
    "symbol",
    "entry_date",
    "entry_price",
    "exit_date",
    "exit_price",
    "qty",
    "stop_initial",
    "risk_usd",
    "pnl_usd",
    "pnl_r",
    "costs_usd",
    "exit_reason",
]


def simulate(
    bars: dict[str, pd.DataFrame], signals: dict[str, pd.DataFrame], cfg: SimConfig
) -> SimResult:
    """Ejecuta la simulación. `signals[s]` debe tener el mismo índice que `bars[s]`."""
    symbols = sorted(bars)
    index = sorted(set().union(*[bars[s].index for s in symbols]))
    index = pd.DatetimeIndex(index)
    ac = {s: asset_class_of(s) for s in symbols}
    sig = {}
    for s in symbols:
        sg = signals[s].reindex(bars[s].index)
        if cfg.entry_delay:
            sg = sg.copy()
            sg[["entry", "stop_price", "rank"]] = sg[["entry", "stop_price", "rank"]].shift(
                cfg.entry_delay
            )
            sg["entry"] = sg["entry"].fillna(False).astype(bool)
        sig[s] = sg
    cash = cfg.initial_equity
    pos: dict[str, dict] = {}
    last_close: dict[str, float] = {}
    pending_entry: dict[str, tuple[float, float, float]] = {}  # s -> (stop, rank, obj.)
    pending_exit: set[str] = set()
    trades: list[dict] = []
    eq_hist, expo_hist, nopen_hist = [], [], []
    peak = cfg.initial_equity
    kill_pending, killed, kill_date = False, False, None

    def close_pos(s: str, t, ref_price: float, reason: str) -> None:
        nonlocal cash
        p = pos.pop(s)
        cm = cfg.costs[ac[s]]
        fill = cm.fill_price(ref_price, "sell")
        comm = cm.commission(p["qty"], fill)
        cash += p["qty"] * fill - comm
        pnl = p["qty"] * fill - comm - p["cost_basis"]
        costs = p["entry_costs"] + comm + p["qty"] * (ref_price - fill)
        trades.append(
            {
                "symbol": s,
                "entry_date": p["entry_date"],
                "entry_price": p["entry_fill"],
                "exit_date": t,
                "exit_price": fill,
                "qty": p["qty"],
                "stop_initial": p["stop"],
                "risk_usd": p["risk_usd"],
                "pnl_usd": pnl,
                "pnl_r": pnl / p["risk_usd"] if p["risk_usd"] > 0 else np.nan,
                "costs_usd": costs,
                "exit_reason": reason,
            }
        )

    for t in index:
        active = [s for s in symbols if t in bars[s].index]
        bar = {s: bars[s].loc[t] for s in active}
        # 1. kill switch pendiente
        if kill_pending:
            for s in list(pos):
                if s in bar:
                    close_pos(s, t, bar[s]["open"], "kill_switch")
            if not pos:
                kill_pending = False
        # 2. salidas
        for s in sorted(pos):
            if s not in bar:
                continue
            b, p = bar[s], pos[s]
            if s in pending_exit:
                close_pos(s, t, b["open"], "signal")
            elif b["open"] <= p["stop"]:
                close_pos(s, t, b["open"], "stop_gap")
            elif b["low"] <= p["stop"]:
                close_pos(s, t, p["stop"], "stop")
            elif p.get("target") and b["high"] >= p["target"]:
                close_pos(s, t, p["target"], "target")
        pending_exit -= set(bar)  # solo se consumen las de activos con vela hoy
        # 3. entradas
        if not killed and pending_entry:
            mtm = cash + sum(
                p["qty"] * (bar[s]["open"] if s in bar else last_close[s]) for s, p in pos.items()
            )
            cands = sorted(
                [(s, *pending_entry[s]) for s in pending_entry if s in bar],
                key=lambda x: (-(x[2] if np.isfinite(x[2]) else -np.inf), x[0]),
            )
            for s, stop, _rank, target in cands:
                if s in pos:
                    continue
                o = bar[s]["open"]
                if not (np.isfinite(stop) and o > stop):
                    continue
                cm = cfg.costs[ac[s]]
                qty = position_size(
                    mtm, o, stop, cfg.risk_per_trade, cm, ac[s], cfg.allow_fractional
                )
                gross = sum(
                    p["qty"] * (bar[x]["open"] if x in bar else last_close[x])
                    for x, p in pos.items()
                )
                qty = apply_limits(
                    qty,
                    o,
                    cm,
                    cash,
                    mtm,
                    gross,
                    len(pos),
                    cfg.max_positions,
                    cfg.max_gross_exposure,
                    ac[s],
                    cfg.allow_fractional,
                )
                if qty <= 0:
                    continue
                fill = cm.fill_price(o, "buy")
                comm = cm.commission(qty, fill)
                cash -= qty * fill + comm
                risk_usd = (
                    qty * (fill - cm.fill_price(stop, "sell"))
                    + comm
                    + cm.commission(qty, cm.fill_price(stop, "sell"))
                )
                pos[s] = {
                    "qty": qty,
                    "entry_date": t,
                    "entry_fill": fill,
                    "stop": stop,
                    "cost_basis": qty * fill + comm,
                    "risk_usd": risk_usd,
                    "entry_costs": comm + qty * (fill - o),
                    "target": target if np.isfinite(target) else None,
                }
                if bar[s]["low"] <= stop:  # stop tocado en la misma vela de entrada
                    close_pos(s, t, stop, "stop")
                elif pos[s]["target"] and bar[s]["high"] >= pos[s]["target"]:
                    close_pos(s, t, pos[s]["target"], "target")
        for s in [x for x in pending_entry if x in bar]:
            del pending_entry[s]
        # 4. valoración
        for s in active:
            last_close[s] = float(bar[s]["close"])
        gross = sum(p["qty"] * last_close[s] for s, p in pos.items())
        eq = cash + gross
        eq_hist.append(eq)
        expo_hist.append(gross / eq if eq > 0 else 0.0)
        nopen_hist.append(len(pos))
        peak = max(peak, eq)
        if (
            cfg.kill_switch_drawdown is not None
            and not killed
            and check_kill_switch(peak, eq, cfg.kill_switch_drawdown)
        ):
            killed, kill_pending, kill_date = True, bool(pos), t
        # 5. señales de t
        for s in active:
            row = sig[s].loc[t]
            if s in pos and bool(row["exit"]):
                pending_exit.add(s)
            elif s not in pos and not killed and bool(row["entry"]):
                rk = row["rank"] if "rank" in row and pd.notna(row["rank"]) else -np.inf
                tg = row["target_price"] if "target_price" in row else np.nan
                pending_entry[s] = (
                    float(row["stop_price"]),
                    float(rk),
                    float(tg) if pd.notna(tg) else np.nan,
                )

    # Fin de datos: las posiciones abiertas se cierran (contables) al último cierre.
    if len(index):
        t_end = index[-1]
        for s in sorted(pos):
            close_pos(s, t_end, last_close[s], "end_of_data")
        if eq_hist:
            eq_hist[-1] = cash
    return SimResult(
        equity=pd.Series(eq_hist, index=index, name="equity"),
        trades=pd.DataFrame(trades, columns=TRADE_COLS),
        exposure=pd.Series(expo_hist, index=index, name="exposure"),
        n_open=pd.Series(nopen_hist, index=index, name="n_open"),
        kill_switch_date=kill_date,
    )
