# Verificación del contraste yfinance - Alpaca (Fable, fase A)
Generado por un script ad hoc sobre `data_cache/` (yfinance auto_adjust vs Alpaca SIP adjustment=all). No contiene resultados de estrategias.

## 1. Naturaleza de las discrepancias (rentabilidad diaria cierre a cierre, 2016-01 a 2026-10)

| ETF | corr | corr sin los 5 peores días | días >10 pb | de ellos en mar-2020 | de ellos que revierten al día siguiente | peor día (pb) | cierre yf/alp ese día vs mediana (pb) | deriva de niveles fin/inicio (pb) | mediana abs. dif. de gap de apertura (pb) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | 0.9961 | 0.9995 | 44 | 15 | 21 | 269 (2020-03-13) | -32 | 96 | 0.1 |
| DIA | 0.9983 | 0.9998 | 26 | 10 | 15 | 235 (2020-03-17) | 0 | 21 | 0.1 |
| IWM | 0.9992 | 0.9997 | 47 | 13 | 21 | 140 (2020-03-17) | -46 | 1 | 0.3 |
| EFA | 0.9987 | 0.9999 | 7 | 3 | 5 | -216 (2020-03-17) | 0 | 1 | 0.5 |
| EEM | 0.9996 | 0.9998 | 28 | 7 | 12 | 126 (2020-03-17) | 1 | -1 | 0.9 |
| GLD | 0.9958 | 1.0000 | 8 | 5 | 4 | -321 (2020-03-17) | -19 | 0 | 0.0 |
| VNQ | 0.9801 | 0.9997 | 16 | 6 | 8 | 957 (2020-03-17) | 0 | 3 | 0.4 |
| QQQ | 1.0000 | 1.0000 | 2 | 0 | 0 | -18 (2022-09-19) | -18 | -32 | 0.2 |
| IEF | 0.9999 | 0.9999 | 1 | 0 | 0 | 14 (2016-08-01) | -0 | 14 | 0.3 |
| DBC | 0.9994 | 0.9997 | 6 | 2 | 2 | -139 (2018-12-26) | -2 | -134 | 1.5 |

## 2. ¿Cambian las señales? (mismas funciones de estrategia sobre yfinance y Alpaca, ambas recortadas a 2016+; se compara 2017-07 a 2020-12, tramo IS, sin simular)

| estrategia | ETF | entradas yf | entradas Alpaca | coinciden mismo día | salidas yf | salidas Alp | coinciden |
|---|---|---|---|---|---|---|---|
| tsmom_etf | SPY | 38 | 38 | 38 | 4 | 4 | 4 |
| tsmom_etf | EFA | 26 | 26 | 26 | 16 | 16 | 16 |
| tsmom_etf | EEM | 25 | 25 | 25 | 17 | 17 | 17 |
| tsmom_etf | IEF | 26 | 26 | 26 | 16 | 16 | 16 |
| tsmom_etf | GLD | 27 | 27 | 27 | 15 | 15 | 15 |
| tsmom_etf | DBC | 18 | 18 | 18 | 24 | 24 | 24 |
| tsmom_etf | VNQ | 24 | 24 | 24 | 18 | 18 | 18 |
| rsi2_etf | SPY | 46 | 47 | 44 | 557 | 555 | 552 |
| rsi2_etf | QQQ | 46 | 46 | 46 | 550 | 549 | 549 |
| rsi2_etf | IWM | 41 | 39 | 39 | 505 | 500 | 500 |
| rsi2_etf | DIA | 49 | 50 | 49 | 527 | 524 | 522 |
| rsi2_etf | EFA | 40 | 39 | 39 | 511 | 509 | 507 |
| rsi2_etf | EEM | 44 | 46 | 43 | 493 | 490 | 489 |
| donchian_etf | SPY | 125 | 121 | 121 | 34 | 33 | 32 |
| donchian_etf | EFA | 81 | 78 | 78 | 39 | 38 | 38 |
| donchian_etf | EEM | 82 | 79 | 79 | 46 | 45 | 45 |
| donchian_etf | IEF | 55 | 53 | 53 | 59 | 59 | 59 |
| donchian_etf | GLD | 66 | 66 | 66 | 48 | 48 | 47 |
| donchian_etf | DBC | 70 | 66 | 66 | 56 | 52 | 52 |
| donchian_etf | VNQ | 52 | 52 | 52 | 49 | 48 | 48 |
