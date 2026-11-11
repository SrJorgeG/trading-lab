# tsmom_etf — modo robust (preregistrada)
Generado: 2026-11-11 16:20 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 1.38 % | 9.08 % |
| Rentabilidad total | 20.36 % | 223.35 % |
| Volatilidad anual | 3.50 % | 20.87 % |
| Sharpe | 0.41 | 0.52 |
| Sortino | 0.55 | 0.73 |
| Máx. drawdown | -9.48 % | -55.19 % |
| Máx. días bajo el agua | 1155 | 1772 |
| Calmar | 0.15 | 0.16 |
| Nº operaciones | 43 | — |
| Win rate | 46.51 % | — |
| Expectancy ($) | 47.34 | — |
| Expectancy (R) | 0.94 | — |
| Profit factor | 2.76 | — |
| Exposición media | 34.30 % | — |
| Duración media (días) | 313.5 | — |

## Datos
- DBC: 2006-02-06 → 2026-10-30 (5217 velas)
- EEM: 2003-04-14 → 2026-10-30 (5926 velas)
- EFA: 2003-01-02 → 2026-10-30 (5996 velas)
- GLD: 2004-11-18 → 2026-10-30 (5522 velas)
- IEF: 2003-01-02 → 2026-10-30 (5996 velas)
- SPY: 2003-01-02 → 2026-10-30 (5996 velas)
- VNQ: 2004-09-29 → 2026-10-30 (5558 velas)
- DBC entra al universo el 2007-07-19 (≥ 365 velas)
- EEM entra al universo el 2004-09-23 (≥ 365 velas)
- EFA entra al universo el 2004-06-15 (≥ 365 velas)
- GLD entra al universo el 2006-05-02 (≥ 365 velas)
- IEF entra al universo el 2004-06-15 (≥ 365 velas)
- SPY entra al universo el 2004-06-15 (≥ 365 velas)
- VNQ entra al universo el 2006-03-10 (≥ 365 velas)
- Fuente: yfinance (ajuste: auto_adjust)
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo robust)

## Costes
- equity: slippage 5.0 pb/lado, comisión 0.000 %/lado + 0.0 $/acc.
- crypto: slippage 20.0 pb/lado, comisión 0.250 %/lado + 0.0 $/acc.
- Escenario: base
- Riesgo por operación: 0.50 %; tope por posición: 33.33 % del equity

## Parámetros
```
lookback = 252
atr_mult = 4.0
atr_n = 20
```

## Variantes probadas
Ejecuciones registradas para esta estrategia: 15

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Robustez (in-sample)
| prueba | Sharpe | expectancy R | trades |
|---|---|---|---|
| central | 0.41 | 0.941 | 43 |
| lookback=189, atr_mult=3.0 | 0.70 | 2.451 | 45 |
| lookback=189, atr_mult=4.0 | 0.66 | 1.673 | 45 |
| lookback=189, atr_mult=5.0 | 0.63 | 1.250 | 43 |
| lookback=252, atr_mult=3.0 | 0.45 | 1.230 | 47 |
| lookback=252, atr_mult=5.0 | 0.37 | 0.765 | 40 |
| lookback=315, atr_mult=3.0 | 0.51 | 1.521 | 48 |
| lookback=315, atr_mult=4.0 | 0.50 | 1.223 | 42 |
| lookback=315, atr_mult=5.0 | 0.52 | 1.320 | 35 |
| costes × 2 | 0.40 | 0.892 | 43 |
| retraso 1 vela | 0.37 | 0.815 | 43 |

Rejilla ±25 %: 8/8 vecinas (100 %) con expectancy > 0 y Sharpe ≥ 50 % del central (0.41). Criterio 6 (≥ 70 %): sí.

P&L total sin las 5 mejores operaciones: 54.46 $
Monte Carlo (1000, semilla 42): DD p50 2.5 %, p95 4.1 %
