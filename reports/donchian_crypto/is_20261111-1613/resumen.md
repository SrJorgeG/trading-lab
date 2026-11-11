# donchian_crypto — modo is (preregistrada)
Generado: 2026-11-11 16:13 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 26.84 % | 87.07 % |
| Rentabilidad total | 530.75 % | 12687.68 % |
| Volatilidad anual | 26.55 % | 72.66 % |
| Sharpe | 1.03 | 1.23 |
| Sortino | 1.50 | 1.82 |
| Máx. drawdown | -32.62 % | -83.40 % |
| Máx. días bajo el agua | 779 | 1079 |
| Calmar | 0.82 | 1.04 |
| Nº operaciones | 66 | — |
| Win rate | 37.88 % | — |
| Expectancy ($) | 804.17 | — |
| Expectancy (R) | 3.62 | — |
| Profit factor | 4.87 | — |
| Exposición media | 16.79 % | — |
| Duración media (días) | 38.4 | — |

## Datos
- BCH/USD: 2017-11-09 → 2026-10-31 (3279 velas)
- BTC/USD: 2014-09-17 → 2026-10-31 (4428 velas)
- ETH/USD: 2017-11-09 → 2026-10-31 (3279 velas)
- LTC/USD: 2014-09-17 → 2026-10-31 (4428 velas)
- BCH/USD entra al universo el 2018-11-08 (≥ 365 velas)
- BTC/USD entra al universo el 2015-09-16 (≥ 365 velas)
- ETH/USD entra al universo el 2018-11-08 (≥ 365 velas)
- LTC/USD entra al universo el 2015-09-16 (≥ 365 velas)
- Fuente: yfinance (ajuste: auto_adjust)
- Periodo simulado: 2015-10-01 → 2023-06-30 (modo is)

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

## Benchmark informativo (BTC/USD 50 % / caja 50 %, rebalanceo mensual, con costes)
CAGR 46.59 %, Sharpe 1.22, DD -57.3 %

## Calibración del riesgo en IS (P1, hipotesis.md §3)
| riesgo por operación | DD máx. IS | episodios kill switch | CAGR | Sharpe |
|---|---|---|---|---|
| 1.00 % | -32.6 % | 22 | 26.84 % | 1.03 |
| 0.75 % | -28.3 % | 17 | 20.66 % | 0.98 |
| 0.50 % | -22.6 % | 8 | 14.20 % | 0.92 |

**Ninguno** cumple DD ≤ 10 %: según P1 la candidata muere en IS.

## Kill switch (P1): episodios con reinicio del máximo
Episodios de caída > 10 %: **22**; primero (regla literal) el 2015-11-11

## Dependencia de pocas operaciones / un activo
- P&L total: 53075.39 $
- Sin las 5 mejores operaciones (criterio 9): 7195.34 $
- Sin el mejor activo (BTC/USD) (criterio 13): 30636.56 $

## Subperiodos (operaciones por fecha de entrada, criterio 11)
| subperiodo pre-registrado | tramo cubierto aquí | trades | expectancy R |
|---|---|---|---|
| 2015-10-01 → 2019-06-30 | 2015-10-01 → 2019-06-30 | 26 | 4.689 |
| 2019-07-01 → 2023-02-28 | 2019-07-01 → 2023-02-28 | 35 | 2.974 |
| 2023-03-01 → 2026-10-31 | 2023-03-01 → 2023-06-30 | 5 | 2.547 |

## Por activo (criterio 11: ≥ 2 activos con ≥ 10 operaciones y expectancy > 0)
| activo | trades | expectancy R | P&L $ |
|---|---|---|---|
| BCH/USD | 9 | 1.551 | 6208.28 |
| BTC/USD | 25 | 4.212 | 22438.84 |
| ETH/USD | 13 | 3.783 | 13625.46 |
| LTC/USD | 19 | 3.701 | 10802.82 |

Exposición media: 16.8 %
