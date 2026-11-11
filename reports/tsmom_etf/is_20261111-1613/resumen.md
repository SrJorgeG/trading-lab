# tsmom_etf — modo is (preregistrada)
Generado: 2026-11-11 16:13 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 2.44 % | 9.08 % |
| Rentabilidad total | 38.43 % | 223.35 % |
| Volatilidad anual | 6.77 % | 20.87 % |
| Sharpe | 0.39 | 0.52 |
| Sortino | 0.52 | 0.73 |
| Máx. drawdown | -17.50 % | -55.19 % |
| Máx. días bajo el agua | 1156 | 1772 |
| Calmar | 0.14 | 0.16 |
| Nº operaciones | 43 | — |
| Win rate | 46.51 % | — |
| Expectancy ($) | 89.38 | — |
| Expectancy (R) | 0.94 | — |
| Profit factor | 2.55 | — |
| Exposición media | 60.84 % | — |
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
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo is)

## Costes
- equity: slippage 5.0 pb/lado, comisión 0.000 %/lado + 0.0 $/acc.
- crypto: slippage 20.0 pb/lado, comisión 0.250 %/lado + 0.0 $/acc.
- Escenario: base
- Riesgo por operación: 1.00 %; tope por posición: 33.33 % del equity

## Parámetros
```
lookback = 252
atr_mult = 4.0
atr_n = 20
```

## Variantes probadas
Ejecuciones registradas para esta estrategia: 3

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Calibración del riesgo en IS (P1, hipotesis.md §3)
| riesgo por operación | DD máx. IS | episodios kill switch | CAGR | Sharpe |
|---|---|---|---|---|
| 1.00 % | -17.5 % | 2 | 2.44 % | 0.39 |
| 0.75 % | -13.8 % | 1 | 1.99 % | 0.40 |
| 0.50 % | -9.5 % | 0 | 1.38 % | 0.41 |

Riesgo que seleccionaría P1 (mayor con DD ≤ 10 %): **0.50 %**

## Kill switch (P1): episodios con reinicio del máximo
Episodios de caída > 10 %: **2**; primero (regla literal) el 2008-10-13

## Dependencia de pocas operaciones / un activo
- P&L total: 3843.49 $
- Sin las 5 mejores operaciones (criterio 9): 61.49 $
- Sin el mejor activo (SPY) (criterio 13): 2336.67 $

## Subperiodos (operaciones por fecha de entrada, criterio 11)
| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |
|---|---|---|---|
| 2007-07-01 → 2013-12-31 | 2007-07-01 → 2013-12-31 | 26 | 0.884 |
| 2014-01-01 → 2020-06-30 | 2014-01-01 → 2020-06-30 | 17 | 1.030 |
| 2020-07-01 → 2026-10-31 | 2020-07-01 → 2020-12-31 | 0 | nan |

## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)
| activo | trades | expectancy R | P&L $ |
|---|---|---|---|
| DBC | 4 | -0.511 | -258.02 |
| EEM | 4 | 0.341 | 236.15 |
| EFA | 6 | -0.513 | -316.13 |
| GLD | 8 | 1.540 | 1197.58 |
| IEF | 5 | 3.209 | 1208.52 |
| SPY | 8 | 1.608 | 1506.82 |
| VNQ | 8 | 0.375 | 268.56 |

Exposición media: 60.8 %
