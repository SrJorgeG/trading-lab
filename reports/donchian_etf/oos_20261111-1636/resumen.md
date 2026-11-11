# donchian_etf — modo oos (preregistrada)
Generado: 2026-11-11 16:36 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 3.45 % | 14.65 % |
| Rentabilidad total | 21.82 % | 121.54 % |
| Volatilidad anual | 5.73 % | 16.58 % |
| Sharpe | 0.62 | 0.91 |
| Sortino | 0.85 | 1.32 |
| Máx. drawdown | -7.04 % | -24.50 % |
| Máx. días bajo el agua | 1139 | 708 |
| Calmar | 0.49 | 0.60 |
| Nº operaciones | 89 | — |
| Win rate | 35.96 % | — |
| Expectancy ($) | 24.52 | — |
| Expectancy (R) | 0.49 | — |
| Profit factor | 1.80 | — |
| Exposición media | 40.31 % | — |
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
Ejecuciones registradas para esta estrategia: 34

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.00 %, Sharpe 0.78, DD -21.2 %

## Kill switch (P1): episodios con reinicio del máximo
Episodios de caída > 10 %: **0**

## Dependencia de pocas operaciones / un activo
- P&L total: 2182.07 $
- Sin las 5 mejores operaciones (criterio 9): -560.20 $
- Sin el mejor activo (DBC) (criterio 13): 591.90 $

## Subperiodos (operaciones por fecha de entrada, criterio 11)
| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |
|---|---|---|---|
| 2020-07-01 → 2026-10-31 | 2021-01-01 → 2026-10-30 | 89 | 0.486 |

## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)
| activo | trades | expectancy R | P&L $ |
|---|---|---|---|
| DBC | 11 | 2.669 | 1590.17 |
| EEM | 9 | 0.369 | 157.41 |
| EFA | 16 | 0.183 | 115.26 |
| GLD | 13 | 0.659 | 361.33 |
| IEF | 10 | -0.656 | -216.37 |
| SPY | 18 | 0.425 | 307.92 |
| VNQ | 12 | -0.171 | -133.65 |

Exposición media: 40.3 %
