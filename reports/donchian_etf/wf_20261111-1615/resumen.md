# donchian_etf — modo wf (preregistrada)
Generado: 2026-11-11 16:18 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 3.55 % | 9.08 % |
| Rentabilidad total | 60.17 % | 223.35 % |
| Volatilidad anual | 5.20 % | 20.87 % |
| Sharpe | 0.70 | 0.52 |
| Sortino | 0.96 | 0.73 |
| Máx. drawdown | -9.43 % | -55.19 % |
| Máx. días bajo el agua | 1520 | 1772 |
| Calmar | 0.38 | 0.16 |
| Nº operaciones | 167 | — |
| Win rate | 42.51 % | — |
| Expectancy ($) | 36.03 | — |
| Expectancy (R) | 0.77 | — |
| Profit factor | 2.11 | — |
| Exposición media | 42.92 % | — |
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
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo wf)

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
Ejecuciones registradas para esta estrategia: 4

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Walk-forward IS (hipotesis.md §3: entrenamiento creciente, ventanas fijas)
| entrenamiento | prueba | parámetros elegidos | Sharpe entreno | trades | neto $ |
|---|---|---|---|---|---|
| 2007-07-01 → 2012-12-31 | 2013-01-01 → 2013-12-31 | entry_n=69, exit_n=20, atr_mult=2.5 | 1.06 | 15 | 117.79 |
| 2007-07-01 → 2013-12-31 | 2014-01-01 → 2014-12-31 | entry_n=69, exit_n=20, atr_mult=2.5 | 0.95 | 14 | 37.88 |
| 2007-07-01 → 2014-12-31 | 2015-01-01 → 2015-12-31 | entry_n=55, exit_n=20, atr_mult=1.5 | 0.84 | 16 | -625.92 |
| 2007-07-01 → 2015-12-31 | 2016-01-01 → 2016-12-31 | entry_n=55, exit_n=20, atr_mult=1.5 | 0.69 | 14 | 463.95 |
| 2007-07-01 → 2016-12-31 | 2017-01-01 → 2017-12-31 | entry_n=55, exit_n=20, atr_mult=1.5 | 0.71 | 20 | 865.43 |
| 2007-07-01 → 2017-12-31 | 2018-01-01 → 2018-12-31 | entry_n=55, exit_n=20, atr_mult=2.5 | 0.81 | 12 | 68.93 |
| 2007-07-01 → 2018-12-31 | 2019-01-01 → 2019-12-31 | entry_n=69, exit_n=20, atr_mult=2.5 | 0.74 | 13 | 986.93 |
| 2007-07-01 → 2019-12-31 | 2020-01-01 → 2020-12-31 | entry_n=69, exit_n=20, atr_mult=2.5 | 0.85 | 15 | 199.11 |

Ventanas válidas (con operaciones): 8/8 (mínimo 5). Positivas: 7/8 (88 %). Criterio 5 (≥ 60 %): sí.
