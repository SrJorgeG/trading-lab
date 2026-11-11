# donchian_etf — modo robust (preregistrada)
Generado: 2026-11-11 16:19 (hora de Madrid)

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
- Periodo simulado: 2007-07-01 → 2020-12-31 (modo robust)

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
Ejecuciones registradas para esta estrategia: 33

Kill switch **desactivado** en esta simulación (P1 de hipotesis.md): las métricas se miden sin él y los episodios se cuentan aparte.

## Benchmark informativo (SPY 60 % / IEF 40 %, rebalanceo mensual, con costes)
CAGR 8.14 %, Sharpe 0.75, DD -32.5 %

## Robustez (in-sample)
| prueba | Sharpe | expectancy R | trades |
|---|---|---|---|
| central | 0.70 | 0.767 | 167 |
| entry_n=41, exit_n=15, atr_mult=1.5 | 0.33 | 0.326 | 247 |
| entry_n=41, exit_n=15, atr_mult=2.0 | 0.42 | 0.328 | 221 |
| entry_n=41, exit_n=15, atr_mult=2.5 | 0.45 | 0.308 | 209 |
| entry_n=41, exit_n=20, atr_mult=1.5 | 0.62 | 0.720 | 197 |
| entry_n=41, exit_n=20, atr_mult=2.0 | 0.70 | 0.683 | 175 |
| entry_n=41, exit_n=20, atr_mult=2.5 | 0.72 | 0.612 | 166 |
| entry_n=41, exit_n=25, atr_mult=1.5 | 0.64 | 0.942 | 176 |
| entry_n=41, exit_n=25, atr_mult=2.0 | 0.77 | 0.935 | 154 |
| entry_n=41, exit_n=25, atr_mult=2.5 | 0.78 | 0.784 | 146 |
| entry_n=55, exit_n=15, atr_mult=1.5 | 0.41 | 0.376 | 228 |
| entry_n=55, exit_n=15, atr_mult=2.0 | 0.38 | 0.290 | 212 |
| entry_n=55, exit_n=15, atr_mult=2.5 | 0.47 | 0.331 | 195 |
| entry_n=55, exit_n=20, atr_mult=1.5 | 0.72 | 0.865 | 179 |
| entry_n=55, exit_n=20, atr_mult=2.5 | 0.80 | 0.766 | 152 |
| entry_n=55, exit_n=25, atr_mult=1.5 | 0.72 | 1.058 | 160 |
| entry_n=55, exit_n=25, atr_mult=2.0 | 0.74 | 1.010 | 147 |
| entry_n=55, exit_n=25, atr_mult=2.5 | 0.80 | 0.883 | 137 |
| entry_n=69, exit_n=15, atr_mult=1.5 | 0.29 | 0.238 | 220 |
| entry_n=69, exit_n=15, atr_mult=2.0 | 0.30 | 0.272 | 204 |
| entry_n=69, exit_n=15, atr_mult=2.5 | 0.43 | 0.318 | 187 |
| entry_n=69, exit_n=20, atr_mult=1.5 | 0.64 | 0.807 | 171 |
| entry_n=69, exit_n=20, atr_mult=2.0 | 0.65 | 0.761 | 158 |
| entry_n=69, exit_n=20, atr_mult=2.5 | 0.81 | 0.806 | 142 |
| entry_n=69, exit_n=25, atr_mult=1.5 | 0.68 | 1.041 | 153 |
| entry_n=69, exit_n=25, atr_mult=2.0 | 0.70 | 0.963 | 139 |
| entry_n=69, exit_n=25, atr_mult=2.5 | 0.77 | 0.854 | 130 |
| costes × 2 | 0.65 | 0.660 | 167 |
| retraso 1 vela | 0.64 | 0.609 | 166 |

Rejilla ±25 %: 23/26 vecinas (88 %) con expectancy > 0 y Sharpe ≥ 50 % del central (0.70). Criterio 6 (≥ 70 %): sí.

P&L total sin las 5 mejores operaciones: 2931.84 $
Monte Carlo (1000, semilla 42): DD p50 4.8 %, p95 7.6 %
