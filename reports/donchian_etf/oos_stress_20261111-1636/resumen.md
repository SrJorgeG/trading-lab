# donchian_etf — modo oos (preregistrada)
Generado: 2026-11-11 16:36 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 3.08 % | 14.64 % |
| Rentabilidad total | 19.31 % | 121.43 % |
| Volatilidad anual | 5.59 % | 16.58 % |
| Sharpe | 0.57 | 0.91 |
| Sortino | 0.78 | 1.32 |
| Máx. drawdown | -7.17 % | -24.50 % |
| Máx. días bajo el agua | 1139 | 708 |
| Calmar | 0.43 | 0.60 |
| Nº operaciones | 89 | — |
| Win rate | 35.96 % | — |
| Expectancy ($) | 21.69 | — |
| Expectancy (R) | 0.42 | — |
| Profit factor | 1.70 | — |
| Exposición media | 39.41 % | — |
| Duración media (días) | 46.1 | — |

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
- Periodo simulado: 2021-01-01 → 2026-10-30 (modo oos)

## Costes
- equity: slippage 10.0 pb/lado, comisión 0.000 %/lado + 0.0 $/acc.
- crypto: slippage 40.0 pb/lado, comisión 0.500 %/lado + 0.0 $/acc.
- Escenario: stress
- Riesgo por operación: 0.50 %; tope por posición: 33.33 % del equity

## Parámetros
```
entry_n = 55
exit_n = 20
atr_mult = 2.0
atr_n = 20
```

## Variantes probadas
Ejecuciones registradas para esta estrategia: 35

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 7.98 %, Sharpe 0.78, DD -21.2 %

## Kill switch (P1): episodios con reinicio del máximo
Episodios de caída > 10 %: **0**

## Dependencia de pocas operaciones / un activo
- P&L total: 1930.64 $
- Sin las 5 mejores operaciones (criterio 9): -689.05 $
- Sin el mejor activo (DBC) (criterio 13): 457.00 $

## Subperiodos (operaciones por fecha de entrada, criterio 11)
| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |
|---|---|---|---|
| 2020-07-01 → 2026-10-31 | 2021-01-01 → 2026-10-30 | 89 | 0.415 |

## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)
| activo | trades | expectancy R | P&L $ |
|---|---|---|---|
| DBC | 11 | 2.491 | 1473.65 |
| EEM | 9 | 0.315 | 134.79 |
| EFA | 16 | 0.121 | 75.65 |
| GLD | 13 | 0.559 | 351.57 |
| IEF | 10 | -0.679 | -241.07 |
| SPY | 18 | 0.368 | 283.85 |
| VNQ | 12 | -0.194 | -147.80 |

Exposición media: 39.4 %
