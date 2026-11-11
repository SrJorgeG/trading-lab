"""BASELINES de referencia (NO son las hipótesis pre-registradas del paso 1).

Ejecuta con costes base (y repite con costes × 2) y escribe docs/baselines.md y
reports/baselines/<fecha>/resumen.csv. No optimiza nada: parámetros clásicos fijos.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from tlab import metrics  # noqa: E402
from tlab.backtest.allocation_sim import simulate_weights  # noqa: E402
from tlab.backtest.costs import cost_models  # noqa: E402
from tlab.backtest.portfolio_sim import SimConfig, simulate  # noqa: E402
from tlab.config import ROOT, load_settings  # noqa: E402
from tlab.data.loader import load_bars, pick_source  # noqa: E402
from tlab.report import MADRID, now_madrid  # noqa: E402
from tlab.strategies import allocation  # noqa: E402
from tlab.strategies.donchian_atr import generate_signals as donchian  # noqa: E402

EQ_START = "2005-01-01"
BTC_START = "2015-01-01"


def alloc_run(name, data, syms, fn, params, costs, start, ppy, init):
    closes = pd.DataFrame({s: data[s]["close"] for s in syms}).dropna(how="all")
    bars = {s: data[s].reindex(closes.index) for s in syms}
    w = fn(closes, params)
    eq, tr = simulate_weights(bars, w, costs, init, start=start)
    st = metrics.summary(eq, None, ppy)
    st["trades"] = len(tr)
    st["exposure"] = float("nan")
    return name, st, eq


def donchian_run(name, data, syms, cfg, start, params):
    a = pd.Timestamp(start, tz="UTC")
    bars = {s: data[s] for s in syms}
    sigs = {s: donchian(b, params) for s, b in bars.items()}
    bb = {s: b[b.index >= a] for s, b in bars.items()}
    ss = {s: sigs[s][sigs[s].index >= a] for s in syms}
    r = simulate(bb, ss, cfg)
    st = metrics.summary(r.equity, r.trades, 365, r.exposure)
    st["exposure"] = st.pop("avg_exposure")
    st["kill"] = str(r.kill_switch_date.date()) if r.kill_switch_date is not None else "—"
    return name, st, r


def fmt_row(name, st, st2):
    def p(x):
        return "—" if pd.isna(x) else f"{x * 100:.1f} %"

    def f(x):
        return "—" if pd.isna(x) else f"{x:.2f}"

    exp_r = st.get("expectancy_r", float("nan"))
    return (
        f"| {name} | {st['start']} → {st['end']} | {p(st['cagr'])} | {p(st['max_dd'])} | "
        f"{f(st['sharpe'])} | {st['trades']} | {p(st.get('exposure'))} | {f(exp_r)} | "
        f"{p(st2['cagr'])} / {f(st2['sharpe'])} |"
    )


def main() -> None:
    s = load_settings()
    src = pick_source(s["data"]["source"])
    syms = ["SPY", "QQQ", "EFA", "EEM", "TLT", "IEF", "GLD", "BIL", "BTC/USD"]
    data = load_bars(
        syms,
        "1Day",
        start=s["data"]["history_start"],
        source=src,
        cache_dir=ROOT / s["data"]["cache_dir"],
    )
    init = s["capital"]["virtual_equity_usd"]
    r = s["risk"]
    rows, csv_rows = [], []
    donch_detail = ""
    for _cm_name in ("base",):
        base, stress = cost_models(s, "base"), cost_models(s, "stress")
        results = {}
        for costs_label, costs in (("base", base), ("stress", stress)):
            out = []
            out.append(
                alloc_run(
                    "Buy & hold SPY",
                    data,
                    ["SPY"],
                    allocation.buy_hold,
                    {},
                    costs,
                    EQ_START,
                    252,
                    init,
                )
            )
            out.append(
                alloc_run(
                    "Buy & hold BTC",
                    data,
                    ["BTC/USD"],
                    allocation.buy_hold,
                    {},
                    costs,
                    BTC_START,
                    365,
                    init,
                )
            )
            out.append(
                alloc_run(
                    "Faber SMA 10 meses (SPY)",
                    data,
                    ["SPY"],
                    allocation.faber_sma,
                    {"months": 10},
                    costs,
                    EQ_START,
                    252,
                    init,
                )
            )
            out.append(
                alloc_run(
                    "TSMOM 12m (SPY)",
                    data,
                    ["SPY"],
                    allocation.tsmom,
                    {"months": 12},
                    costs,
                    EQ_START,
                    252,
                    init,
                )
            )
            out.append(
                alloc_run(
                    "TSMOM 12m 1/N (SPY, EFA, EEM, TLT, GLD)",
                    data,
                    ["SPY", "EFA", "EEM", "TLT", "GLD"],
                    allocation.tsmom,
                    {"months": 12},
                    costs,
                    EQ_START,
                    252,
                    init,
                )
            )
            out.append(
                alloc_run(
                    "Dual momentum (SPY/EFA → IEF; filtro BIL)",
                    data,
                    ["SPY", "EFA", "IEF", "BIL"],
                    allocation.dual_momentum,
                    {"months": 12, "risk": ["SPY", "EFA"], "safe": "IEF", "tbill": "BIL"},
                    costs,
                    EQ_START,
                    252,
                    init,
                )
            )
            cfg = SimConfig(
                initial_equity=init,
                risk_per_trade=r["risk_per_trade"],
                max_positions=r["max_positions"],
                max_gross_exposure=r["max_gross_exposure"],
                kill_switch_drawdown=r["kill_switch_drawdown"],
                costs=costs,
            )
            dp = {"entry_n": 20, "exit_n": 10, "atr_mult": 2.0, "atr_n": 20}
            dsyms = ["SPY", "QQQ", "BTC/USD"]
            n1, st1, res1 = donchian_run(
                "Donchian 20/10, stop 2×ATR (SPY, QQQ, BTC) — reglas duras completas",
                data,
                dsyms,
                cfg,
                EQ_START,
                dp,
            )
            n2, st2_, res2 = donchian_run(
                "Donchian 20/10 — igual pero SIN kill switch (informativo)",
                data,
                dsyms,
                replace(cfg, kill_switch_drawdown=None),
                EQ_START,
                dp,
            )
            out += [(n1, st1, res1), (n2, st2_, res2)]
            results[costs_label] = out
            if costs_label == "base":
                t = res2.trades
                lines = [
                    "| activo | operaciones | win rate | expectancy R | P&L $ |",
                    "|---|---|---|---|---|",
                ]
                for sym, g in t.groupby("symbol"):
                    lines.append(
                        f"| {sym} | {len(g)} | {(g.pnl_usd > 0).mean() * 100:.0f} % | "
                        f"{g.pnl_r.mean():.3f} | {g.pnl_usd.sum():.0f} |"
                    )
                reasons = t.exit_reason.value_counts().to_dict()
                donch_detail = (
                    "\n".join(lines) + f"\n\nMotivos de salida (sin kill switch): "
                    f"{reasons}. Kill switch con reglas completas: {st1['kill']}."
                )
        for (name, st, _), (_, st2, _) in zip(results["base"], results["stress"], strict=True):
            rows.append(fmt_row(name, st, st2))
            csv_rows.append(
                {
                    "baseline": name,
                    **{k: v for k, v in st.items()},
                    "cagr_stress": st2["cagr"],
                    "sharpe_stress": st2["sharpe"],
                }
            )
    stamp = pd.Timestamp.now(tz=MADRID).strftime("%Y%m%d-%H%M")
    rep = ROOT / "reports" / "baselines" / stamp
    rep.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(csv_rows).to_csv(rep / "resumen.csv", index=False)
    data_lines = "\n".join(
        f"- {k}: {v.index[0].date()} → {v.index[-1].date()} ({len(v)} velas)"
        for k, v in data.items()
    )
    md = TEMPLATE.format(
        now=now_madrid(),
        src=src.name,
        rows="\n".join(rows),
        detail=donch_detail,
        data=data_lines,
        csv=str((rep / "resumen.csv").relative_to(ROOT)),
    )
    (ROOT / "docs" / "baselines.md").write_text(md, encoding="utf-8")
    print(md)


TEMPLATE = """# Baselines de referencia — {now}

> **Esto NO son las hipótesis pre-registradas.** Son estrategias clásicas con parámetros de
> manual, corridas una sola vez con el motor de `prep/motor-backtest` para tener una vara de
> medir y para comprobar que el motor da números razonables. No se ha optimizado nada.
> Fable: no las uses para elegir parámetros en el paso 1 (sería mirar resultados antes de
> pre-registrar). Las cifras salen de `scripts/run_baselines.py`; CSV: `{csv}`.

## Resultados (costes base; última columna = costes × 2)

| Baseline | Periodo | CAGR | Máx. DD | Sharpe | Nº ops | Exposición | Expect. R | \
CAGR / Sharpe costes×2 |
|---|---|---|---|---|---|---|---|---|
{rows}

- Capital virtual 10.000 $. Costes base: ETFs 5 pb/lado de slippage, 0 comisión; cripto 0,25 %
  comisión + 10 pb slippage por lado. Estrés = × 2.
- Sharpe con tipo libre de riesgo 0; anualizado con 252 (solo ETFs) o 365 (BTC y la cartera
  Donchian, que mezcla calendarios: los fines de semana la parte ETF no se mueve).
- "Nº ops" en las estrategias mensuales = nº de órdenes (compras + ventas), no operaciones
  cerradas. En Donchian = operaciones cerradas (las abiertas al final se cierran a mercado).

## Detalle Donchian (variante sin kill switch, costes base)
{detail}

## Advertencias (léelas antes de creerte nada)
1. **Fuente: {src}** (sin claves de Alpaca todavía). Precios ajustados por splits y dividendos
   (`auto_adjust`), así que buy & hold y las mensuales incluyen dividendos reinvertidos de forma
   implícita. Faltan comprobar contra Alpaca (`adjustment="all"`) cuando haya claves.
2. **Las mensuales (Faber, TSMOM, dual momentum, buy & hold) NO cumplen las reglas duras**: no
   tienen stop por operación ni sizing al 1 %; van al 100 % del capital en uno o varios ETFs.
   Están simuladas con `allocation_sim` (pesos objetivo, ejecución a la apertura del primer día
   del mes siguiente, fracciones de participación, efectivo al 0 %). Para operarlas con las
   reglas del kit Fable tiene que decidir cómo encajarlas (ver `docs/PREP_NOTES.md`).
3. **Kill switch permanente**: con la regla literal (−10 % desde máximo → se para para siempre),
   un backtest de 20 años muere en el primer bache y el resto del periodo queda en efectivo.
   Por eso se muestra también la variante sin kill switch, solo como información.
4. Periodo con sesgo: 2005-2026 incluye un mercado alcista muy largo en EE. UU.; BTC solo desde
   2015 (yfinance empieza en sept. 2014). Una sola trayectoria histórica: no es una predicción.
5. El efectivo no rinde nada en las simulaciones (en dual momentum, BIL solo se usa como listón
   del filtro absoluto; antes de 2007-05, que no existe BIL, el listón es 0 %).
6. No se modelan: impuestos, dividendos en paper, subastas de apertura, liquidez/impacto,
   horarios de cripto vs ETF en el ejecutor real, ni el redondeo a acciones enteras en las
   mensuales (sí en Donchian).

## Datos usados
{data}
"""

if __name__ == "__main__":
    main()
