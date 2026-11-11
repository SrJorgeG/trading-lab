# donchian_etf — modo full (preregistrada)
Generado: 2026-11-11 16:36 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 3.59 % | 10.64 % |
| Rentabilidad total | 97.74 % | 605.62 % |
| Volatilidad anual | 5.36 % | 19.68 % |
| Sharpe | 0.69 | 0.61 |
| Sortino | 0.94 | 0.87 |
| Máx. drawdown | -9.43 % | -55.19 % |
| Máx. días bajo el agua | 1520 | 1772 |
| Calmar | 0.38 | 0.19 |
| Nº operaciones | 253 | — |
| Win rate | 39.92 % | — |
| Expectancy ($) | 38.63 | — |
| Expectancy (R) | 0.68 | — |
| Profit factor | 1.99 | — |
| Exposición media | 42.27 % | — |
| Duración media (días) | 54.1 | — |

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
- Periodo simulado: 2007-07-01 → 2026-10-30 (modo full)

## Costes
- equity: slippage 5.0 pb/lado, comisión 0.000 %/lado + 0.0 $/acc.
- crypto: slippage 20.0 pb/lado, comisión 0.250 %/lado + 0.0 $/acc.
- Escenario: base
- Riesgo por operación: 0.50 %; tope por posición: 33.33 % del equity

## Parámetros
```
entry_n = 55
exit_n = 20
atr_mult = 2.0
atr_n = 20
```

## Variantes probadas
Ejecuciones registradas para esta estrategia: 37

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.04 %, Sharpe 0.76, DD -32.5 %

## Kill switch (P1): episodios con reinicio del máximo
Episodios de caída > 10 %: **0**

## Dependencia de pocas operaciones / un activo
- P&L total: 9774.02 $
- Sin las 5 mejores operaciones (criterio 9): 4581.52 $
- Sin el mejor activo (DBC) (criterio 13): 6130.42 $

## Subperiodos (operaciones por fecha de entrada, criterio 11)
| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |
|---|---|---|---|
| 2007-07-01 → 2013-12-31 | 2007-07-01 → 2013-12-31 | 74 | 0.992 |
| 2014-01-01 → 2020-06-30 | 2014-01-01 → 2020-06-30 | 88 | 0.600 |
| 2020-07-01 → 2026-10-31 | 2020-07-01 → 2026-10-30 | 91 | 0.508 |

## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)
| activo | trades | expectancy R | P&L $ |
|---|---|---|---|
| DBC | 26 | 1.964 | 3643.60 |
| EEM | 33 | 0.276 | 659.10 |
| EFA | 43 | 0.336 | 347.03 |
| GLD | 32 | 1.010 | 2010.37 |
| IEF | 36 | 0.960 | 1182.72 |
| SPY | 47 | 0.408 | 1299.69 |
| VNQ | 36 | 0.327 | 631.51 |

Exposición media: 42.3 %
