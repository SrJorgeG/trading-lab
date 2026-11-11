# rsi2_etf — modo robust (preregistrada)
Generado: 2026-11-11 16:24 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 0.06 % | 9.08 % |
| Rentabilidad total | 0.81 % | 223.35 % |
| Volatilidad anual | 2.86 % | 20.87 % |
| Sharpe | 0.04 | 0.52 |
| Sortino | 0.05 | 0.73 |
| Máx. drawdown | -9.92 % | -55.19 % |
| Máx. días bajo el agua | 1058 | 1772 |
| Calmar | 0.01 | 0.16 |
| Nº operaciones | 490 | — |
| Win rate | 61.22 % | — |
| Expectancy ($) | 0.16 | — |
| Expectancy (R) | 0.01 | — |
| Profit factor | 1.02 | — |
| Exposición media | 6.30 % | — |
| Duración media (días) | 4.6 | — |

## Datos
- DIA: 2003-01-02 → 2026-10-30 (5996 velas)
- EEM: 2003-04-14 → 2026-10-30 (5926 velas)
- EFA: 2003-01-02 → 2026-10-30 (5996 velas)
- IEF: 2003-01-02 → 2026-10-30 (5996 velas)
- IWM: 2003-01-02 → 2026-10-30 (5996 velas)
- QQQ: 2003-01-02 → 2026-10-30 (5996 velas)
- SPY: 2003-01-02 → 2026-10-30 (5996 velas)
- DIA entra al universo el 2004-06-15 (≥ 365 velas)
- EEM entra al universo el 2004-09-23 (≥ 365 velas)
- EFA entra al universo el 2004-06-15 (≥ 365 velas)
- IWM entra al universo el 2004-06-15 (≥ 365 velas)
- QQQ entra al universo el 2004-06-15 (≥ 365 velas)
- SPY entra al universo el 2004-06-15 (≥ 365 velas)
- Fuente: yfinance (ajuste: auto_adjust)
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo robust)

## Costes
- equity: slippage 5.0 pb/lado, comisión 0.000 %/lado + 0.0 $/acc.
- crypto: slippage 20.0 pb/lado, comisión 0.250 %/lado + 0.0 $/acc.
- Escenario: base
- Riesgo por operación: 0.50 %; tope por posición: 33.33 % del equity

## Parámetros
```
rsi_n = 2
rsi_entry = 10.0
trend_n = 200
exit_sma_n = 5
atr_mult = 3.0
atr_n = 20
```

## Variantes probadas
Ejecuciones registradas para esta estrategia: 35

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Robustez (in-sample)
| prueba | Sharpe | expectancy R | trades |
|---|---|---|---|
| central | 0.04 | 0.008 | 490 |
| rsi_entry=7.5, exit_sma_n=4, atr_mult=2.25 | 0.17 | 0.037 | 427 |
| rsi_entry=7.5, exit_sma_n=4, atr_mult=3.0 | 0.17 | 0.031 | 407 |
| rsi_entry=7.5, exit_sma_n=4, atr_mult=3.75 | 0.25 | 0.037 | 392 |
| rsi_entry=7.5, exit_sma_n=5, atr_mult=2.25 | 0.19 | 0.042 | 421 |
| rsi_entry=7.5, exit_sma_n=5, atr_mult=3.0 | 0.19 | 0.037 | 399 |
| rsi_entry=7.5, exit_sma_n=5, atr_mult=3.75 | 0.30 | 0.046 | 385 |
| rsi_entry=7.5, exit_sma_n=6, atr_mult=2.25 | 0.25 | 0.059 | 416 |
| rsi_entry=7.5, exit_sma_n=6, atr_mult=3.0 | 0.26 | 0.051 | 392 |
| rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.34 | 0.055 | 377 |
| rsi_entry=10.0, exit_sma_n=4, atr_mult=2.25 | 0.07 | 0.010 | 540 |
| rsi_entry=10.0, exit_sma_n=4, atr_mult=3.0 | 0.04 | 0.008 | 504 |
| rsi_entry=10.0, exit_sma_n=4, atr_mult=3.75 | 0.11 | 0.013 | 487 |
| rsi_entry=10.0, exit_sma_n=5, atr_mult=2.25 | 0.06 | 0.009 | 527 |
| rsi_entry=10.0, exit_sma_n=5, atr_mult=3.75 | 0.11 | 0.015 | 473 |
| rsi_entry=10.0, exit_sma_n=6, atr_mult=2.25 | 0.15 | 0.029 | 521 |
| rsi_entry=10.0, exit_sma_n=6, atr_mult=3.0 | 0.13 | 0.024 | 483 |
| rsi_entry=10.0, exit_sma_n=6, atr_mult=3.75 | 0.18 | 0.026 | 466 |
| rsi_entry=12.5, exit_sma_n=4, atr_mult=2.25 | -0.00 | -0.004 | 670 |
| rsi_entry=12.5, exit_sma_n=4, atr_mult=3.0 | 0.06 | 0.011 | 626 |
| rsi_entry=12.5, exit_sma_n=4, atr_mult=3.75 | 0.13 | 0.012 | 604 |
| rsi_entry=12.5, exit_sma_n=5, atr_mult=2.25 | 0.01 | 0.000 | 653 |
| rsi_entry=12.5, exit_sma_n=5, atr_mult=3.0 | 0.09 | 0.016 | 607 |
| rsi_entry=12.5, exit_sma_n=5, atr_mult=3.75 | 0.15 | 0.016 | 584 |
| rsi_entry=12.5, exit_sma_n=6, atr_mult=2.25 | 0.11 | 0.017 | 643 |
| rsi_entry=12.5, exit_sma_n=6, atr_mult=3.0 | 0.19 | 0.032 | 594 |
| rsi_entry=12.5, exit_sma_n=6, atr_mult=3.75 | 0.24 | 0.028 | 570 |
| suelta trend_n=150 | 0.13 | 0.022 | 463 |
| suelta trend_n=250 | 0.05 | 0.010 | 508 |
| costes × 2 | -0.13 | -0.021 | 490 |
| retraso 1 vela | 0.02 | -0.004 | 540 |

Rejilla ±25 %: 24/26 vecinas (92 %) con expectancy > 0 y Sharpe ≥ 50 % del central (0.04). Criterio 6 (≥ 70 %): sí.

P&L total sin las 5 mejores operaciones: -300.12 $
Monte Carlo (1000, semilla 42): DD p50 5.8 %, p95 8.7 %
