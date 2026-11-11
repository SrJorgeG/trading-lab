# donchian_etf — modo is (preregistrada)
Generado: 2026-11-11 16:13 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 5.26 % | 9.08 % |
| Rentabilidad total | 99.68 % | 223.35 % |
| Volatilidad anual | 8.21 % | 20.87 % |
| Sharpe | 0.67 | 0.52 |
| Sortino | 0.92 | 0.73 |
| Máx. drawdown | -12.68 % | -55.19 % |
| Máx. días bajo el agua | 1073 | 1772 |
| Calmar | 0.41 | 0.16 |
| Nº operaciones | 167 | — |
| Win rate | 42.51 % | — |
| Expectancy ($) | 59.69 | — |
| Expectancy (R) | 0.77 | — |
| Profit factor | 2.05 | — |
| Exposición media | 60.15 % | — |
| Duración media (días) | 57.3 | — |

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
entry_n = 55
exit_n = 20
atr_mult = 2.0
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
| 1.00 % | -12.7 % | 1 | 5.26 % | 0.67 |
| 0.75 % | -11.6 % | 1 | 4.63 % | 0.68 |
| 0.50 % | -9.4 % | 0 | 3.55 % | 0.70 |

Riesgo que seleccionaría P1 (mayor con DD ≤ 10 %): **0.50 %**

## Kill switch (P1): episodios con reinicio del máximo
Episodios de caída > 10 %: **1**; primero (regla literal) el 2015-10-16

## Dependencia de pocas operaciones / un activo
- P&L total: 9968.34 $
- Sin las 5 mejores operaciones (criterio 9): 5185.88 $
- Sin el mejor activo (GLD) (criterio 13): 7615.44 $

## Subperiodos (operaciones por fecha de entrada, criterio 11)
| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |
|---|---|---|---|
| 2007-07-01 → 2013-12-31 | 2007-07-01 → 2013-12-31 | 74 | 0.992 |
| 2014-01-01 → 2020-06-30 | 2014-01-01 → 2020-06-30 | 88 | 0.600 |
| 2020-07-01 → 2026-10-31 | 2020-07-01 → 2020-12-31 | 5 | 0.362 |

## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)
| activo | trades | expectancy R | P&L $ |
|---|---|---|---|
| DBC | 16 | 1.346 | 1906.55 |
| EEM | 25 | 0.232 | 975.81 |
| EFA | 28 | 0.374 | 157.23 |
| GLD | 19 | 1.250 | 2352.91 |
| IEF | 26 | 1.582 | 1738.35 |
| SPY | 29 | 0.397 | 1453.86 |
| VNQ | 24 | 0.576 | 1383.64 |

Exposición media: 60.2 %
