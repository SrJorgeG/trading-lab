# Baselines de referencia — 2026-11-11 01:41 (hora de Madrid)

> **Esto NO son las hipótesis pre-registradas.** Son estrategias clásicas con parámetros de
> manual, corridas una sola vez con el motor de `prep/motor-backtest` para tener una vara de
> medir y para comprobar que el motor da números razonables. No se ha optimizado nada.
> Fable: no las uses para elegir parámetros en el paso 1 (sería mirar resultados antes de
> pre-registrar). Las cifras salen de `scripts/run_baselines.py`; CSV: `reports/baselines/20261111-0141/resumen.csv`.

## Resultados (costes base; última columna = costes × 2)

| Baseline | Periodo | CAGR | Máx. DD | Sharpe | Nº ops | Exposición | Expect. R | CAGR / Sharpe costes×2 |
|---|---|---|---|---|---|---|---|---|
| Buy & hold SPY | 2005-01-03 → 2026-11-10 | 10.7 % | -55.2 % | 0.63 | 1 | — | — | 10.7 % / 0.63 |
| Buy & hold BTC | 2015-01-01 → 2026-11-09 | 58.7 % | -83.4 % | 1.03 | 1 | — | — | 58.7 % / 1.03 |
| Faber SMA 10 meses (SPY) | 2005-01-03 → 2026-11-10 | 7.8 % | -25.9 % | 0.66 | 33 | — | — | 7.7 % / 0.66 |
| TSMOM 12m (SPY) | 2005-01-03 → 2026-11-10 | 9.4 % | -33.7 % | 0.68 | 15 | — | — | 9.4 % / 0.68 |
| TSMOM 12m 1/N (SPY, EFA, EEM, TLT, GLD) | 2005-01-03 → 2026-11-10 | 6.3 % | -15.8 % | 0.70 | 391 | — | — | 6.2 % / 0.69 |
| Dual momentum (SPY/EFA → IEF; filtro BIL) | 2005-01-03 → 2026-11-10 | 8.1 % | -33.7 % | 0.57 | 75 | — | — | 7.9 % / 0.56 |
| Donchian 20/10, stop 2×ATR (SPY, QQQ, BTC) — reglas duras completas | 2005-01-03 → 2026-11-10 | 0.7 % | -10.1 % | 0.21 | 103 | 13.7 % | 0.15 | 0.5 % / 0.16 |
| Donchian 20/10 — igual pero SIN kill switch (informativo) | 2005-01-03 → 2026-11-10 | 9.7 % | -12.2 % | 1.10 | 272 | 40.4 % | 0.84 | 8.1 % / 1.01 |

- Capital virtual 10.000 $. Costes base: ETFs 5 pb/lado de slippage, 0 comisión; cripto 0,25 %
  comisión + 10 pb slippage por lado. Estrés = × 2.
- Sharpe con tipo libre de riesgo 0; anualizado con 252 (solo ETFs) o 365 (BTC y la cartera
  Donchian, que mezcla calendarios: los fines de semana la parte ETF no se mueve).
- "Nº ops" en las estrategias mensuales = nº de órdenes (compras + ventas), no operaciones
  cerradas. En Donchian = operaciones cerradas (las abiertas al final se cierran a mercado).

## Detalle Donchian (variante sin kill switch, costes base)
| activo | operaciones | win rate | expectancy R | P&L $ |
|---|---|---|---|---|
| BTC/USD | 67 | 46 % | 2.273 | 43193 |
| QQQ | 102 | 47 % | 0.401 | 11654 |
| SPY | 103 | 50 % | 0.355 | 10053 |

Motivos de salida (sin kill switch): {'signal': 197, 'stop': 72, 'stop_gap': 3}. Kill switch con reglas completas: 2015-09-13.

## Advertencias (léelas antes de creerte nada)
1. **Fuente: yfinance** (sin claves de Alpaca todavía). Precios ajustados por splits y dividendos
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
- SPY: 2003-01-02 → 2026-11-10 (6003 velas)
- QQQ: 2003-01-02 → 2026-11-10 (6003 velas)
- EFA: 2003-01-02 → 2026-11-10 (6003 velas)
- EEM: 2003-04-14 → 2026-11-10 (5933 velas)
- TLT: 2003-01-02 → 2026-11-10 (6003 velas)
- IEF: 2003-01-02 → 2026-11-10 (6003 velas)
- GLD: 2004-11-18 → 2026-11-10 (5529 velas)
- BIL: 2007-05-30 → 2026-11-10 (4895 velas)
- BTC/USD: 2014-09-17 → 2026-11-09 (4437 velas)
