# tsmom_etf — modo wf (preregistrada)
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
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo wf)

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
Ejecuciones registradas para esta estrategia: 4

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Walk-forward IS (hipotesis.md §3: entrenamiento creciente, ventanas fijas)
| entrenamiento | prueba | parámetros elegidos | Sharpe entreno | trades | neto $ |
|---|---|---|---|---|---|
| 2007-07-01 → 2012-12-31 | 2013-01-01 → 2013-12-31 | lookback=189, atr_mult=3.0 | 0.52 | 4 | 993.47 |
| 2007-07-01 → 2013-12-31 | 2014-01-01 → 2014-12-31 | lookback=189, atr_mult=3.0 | 0.62 | 6 | 473.68 |
| 2007-07-01 → 2014-12-31 | 2015-01-01 → 2015-12-31 | lookback=189, atr_mult=3.0 | 0.68 | 12 | -523.70 |
| 2007-07-01 → 2015-12-31 | 2016-01-01 → 2016-12-31 | lookback=189, atr_mult=3.0 | 0.54 | 5 | 58.69 |
| 2007-07-01 → 2016-12-31 | 2017-01-01 → 2017-12-31 | lookback=189, atr_mult=3.0 | 0.52 | 4 | 1125.63 |
| 2007-07-01 → 2017-12-31 | 2018-01-01 → 2018-12-31 | lookback=189, atr_mult=3.0 | 0.71 | 10 | -167.30 |
| 2007-07-01 → 2018-12-31 | 2019-01-01 → 2019-12-31 | lookback=189, atr_mult=3.0 | 0.54 | 4 | 862.98 |
| 2007-07-01 → 2019-12-31 | 2020-01-01 → 2020-12-31 | lookback=189, atr_mult=3.0 | 0.64 | 9 | -110.69 |

Ventanas válidas (con operaciones): 8/8 (mínimo 5). Positivas: 5/8 (62 %). Criterio 5 (≥ 60 %): sí.
