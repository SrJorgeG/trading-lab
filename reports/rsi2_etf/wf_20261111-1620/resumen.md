# rsi2_etf — modo wf (preregistrada)
Generado: 2026-11-11 16:23 (hora de Madrid)

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
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo wf)

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
Ejecuciones registradas para esta estrategia: 4

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Walk-forward IS (hipotesis.md §3: entrenamiento creciente, ventanas fijas)
| entrenamiento | prueba | parámetros elegidos | Sharpe entreno | trades | neto $ |
|---|---|---|---|---|---|
| 2007-07-01 → 2012-12-31 | 2013-01-01 → 2013-12-31 | rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.61 | 30 | 129.29 |
| 2007-07-01 → 2013-12-31 | 2014-01-01 → 2014-12-31 | rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.70 | 33 | -13.47 |
| 2007-07-01 → 2014-12-31 | 2015-01-01 → 2015-12-31 | rsi_entry=7.5, exit_sma_n=5, atr_mult=3.75 | 0.58 | 33 | -5.19 |
| 2007-07-01 → 2015-12-31 | 2016-01-01 → 2016-12-31 | rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.50 | 22 | 117.04 |
| 2007-07-01 → 2016-12-31 | 2017-01-01 → 2017-12-31 | rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.51 | 33 | 303.72 |
| 2007-07-01 → 2017-12-31 | 2018-01-01 → 2018-12-31 | rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.63 | 36 | -295.68 |
| 2007-07-01 → 2018-12-31 | 2019-01-01 → 2019-12-31 | rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.38 | 28 | -96.54 |
| 2007-07-01 → 2019-12-31 | 2020-01-01 → 2020-12-31 | rsi_entry=7.5, exit_sma_n=6, atr_mult=3.75 | 0.31 | 21 | 182.41 |

Ventanas válidas (con operaciones): 8/8 (mínimo 5). Positivas: 4/8 (50 %). Criterio 5 (≥ 60 %): no.
