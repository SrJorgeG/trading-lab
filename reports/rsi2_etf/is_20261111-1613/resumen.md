# rsi2_etf — modo is (preregistrada)
Generado: 2026-11-11 16:13 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 0.22 % | 9.08 % |
| Rentabilidad total | 3.01 % | 223.35 % |
| Volatilidad anual | 5.06 % | 20.87 % |
| Sharpe | 0.07 | 0.52 |
| Sortino | 0.09 | 0.73 |
| Máx. drawdown | -16.42 % | -55.19 % |
| Máx. días bajo el agua | 1065 | 1772 |
| Calmar | 0.01 | 0.16 |
| Nº operaciones | 490 | — |
| Win rate | 61.22 % | — |
| Expectancy ($) | 0.62 | — |
| Expectancy (R) | 0.01 | — |
| Profit factor | 1.03 | — |
| Exposición media | 11.64 % | — |
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
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo is)

## Costes
- equity: slippage 5.0 pb/lado, comisión 0.000 %/lado + 0.0 $/acc.
- crypto: slippage 20.0 pb/lado, comisión 0.250 %/lado + 0.0 $/acc.
- Escenario: base
- Riesgo por operación: 1.00 %; tope por posición: 33.33 % del equity

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
Ejecuciones registradas para esta estrategia: 3

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Calibración del riesgo en IS (P1, hipotesis.md §3)
| riesgo por operación | DD máx. IS | episodios kill switch | CAGR | Sharpe |
|---|---|---|---|---|
| 1.00 % | -16.4 % | 1 | 0.22 % | 0.07 |
| 0.75 % | -13.5 % | 1 | 0.14 % | 0.06 |
| 0.50 % | -9.9 % | 0 | 0.06 % | 0.04 |

Riesgo que seleccionaría P1 (mayor con DD ≤ 10 %): **0.50 %**

## Kill switch (P1): episodios con reinicio del máximo
Episodios de caída > 10 %: **1**; primero (regla literal) el 2018-10-11

## Dependencia de pocas operaciones / un activo
- P&L total: 301.49 $
- Sin las 5 mejores operaciones (criterio 9): -437.08 $
- Sin el mejor activo (IWM) (criterio 13): -26.15 $

## Subperiodos (operaciones por fecha de entrada, criterio 11)
| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |
|---|---|---|---|
| 2007-07-01 → 2013-12-31 | 2007-07-01 → 2013-12-31 | 212 | 0.051 |
| 2014-01-01 → 2020-06-30 | 2014-01-01 → 2020-06-30 | 259 | -0.038 |
| 2020-07-01 → 2026-10-31 | 2020-07-01 → 2020-12-31 | 19 | 0.151 |

## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)
| activo | trades | expectancy R | P&L $ |
|---|---|---|---|
| DIA | 95 | 0.003 | -64.24 |
| EEM | 73 | 0.024 | 143.95 |
| EFA | 69 | -0.082 | -511.56 |
| IWM | 76 | 0.047 | 327.64 |
| QQQ | 94 | 0.025 | 198.85 |
| SPY | 83 | 0.018 | 206.86 |

Exposición media: 11.6 %
