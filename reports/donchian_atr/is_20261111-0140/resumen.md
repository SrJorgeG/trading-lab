# donchian_atr — modo is (baseline)
Generado: 2026-11-11 01:40 (hora de Madrid)

## Métricas: estrategia vs benchmark
| Métrica | Estrategia | Benchmark |
|---|---|---|
| CAGR | 4.24 % | 12.93 % |
| Rentabilidad total | 38.24 % | 158.11 % |
| Volatilidad anual | 6.44 % | 18.64 % |
| Sharpe | 0.68 | 0.75 |
| Sortino | 0.97 | 1.04 |
| Máx. drawdown | -11.73 % | -33.72 % |
| Máx. días bajo el agua | 2373 | 548 |
| Calmar | 0.36 | 0.38 |
| Nº operaciones | 20 | — |
| Win rate | 65.00 % | — |
| Expectancy ($) | 191.20 | — |
| Expectancy (R) | 1.68 | — |
| Profit factor | 10.22 | — |
| Exposición media | 7.64 % | — |
| Duración media (días) | 34.6 | — |

## Datos
- BTC/USD: 2014-09-17 → 2026-11-09 (4437 velas)
- QQQ: 2003-01-02 → 2026-11-10 (6003 velas)
- SPY: 2003-01-02 → 2026-11-10 (6003 velas)
- Fuente: yfinance (ajuste: auto_adjust)
- Periodo simulado: 2015-09-17 → 2023-07-06 (modo is)

## Costes
- equity: slippage 5.0 pb/lado, comisión 0.000 %/lado + 0.0 $/acc.
- crypto: slippage 10.0 pb/lado, comisión 0.250 %/lado + 0.0 $/acc.
- Escenario: base

## Parámetros
```
entry_n = 20
exit_n = 10
atr_mult = 2.0
atr_n = 20
```

## Variantes probadas
Ejecuciones registradas para esta estrategia: 1

**KILL SWITCH** activado el 2017-01-06 (sin entradas posteriores).
