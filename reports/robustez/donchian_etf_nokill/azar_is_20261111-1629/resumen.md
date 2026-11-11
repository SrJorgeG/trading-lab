# ¿Mejor que el azar? — donchian_etf — contra el azar
Generado: 2026-11-11 16:29 (hora de Madrid)

> Se comparan los resultados de la estrategia con los de **1000 estrategias al azar** (semilla 42) que operan lo mismo, con las mismas reglas y costes, pero entrando en momentos aleatorios. Cifras de `scripts/random_benchmark.py`.

## Veredicto
**VENTAJA PROBABLE** en Sharpe: real 0.70, por encima del 95% de los monos, p-valor empírico = 0.047.

Umbrales (fijados antes de mirar): p < 0,05 → «ventaja probable»; 0,05 ≤ p < 0,10 → «indicio débil»; p ≥ 0,10 → «indistinguible del azar». p = (1 + nº de monos ≥ real) / (N + 1), una cola.

## Todas las métricas
| métrica | real | azar p5 | azar mediana | azar p95 | percentil real | p-valor | veredicto |
|---|---|---|---|---|---|---|---|
| Sharpe | 0.70 | 0.06 | 0.35 | 0.69 | 95% | 0.047 | ventaja probable |
| CAGR | 3.6% | 0.1% | 1.3% | 2.7% | 99% | 0.008 | ventaja probable |
| Máx. caída | -9.4% | -15.2% | -9.4% | -6.7% | 49% | 0.508 | indistinguible del azar |
| MAR (CAGR / caída) | 0.38 | 0.01 | 0.14 | 0.36 | 95% | 0.047 | ventaja probable |
| Expectancy (R) | 0.767 | 0.064 | 0.323 | 0.684 | 98% | 0.016 | ventaja probable |

En la caída máxima, «mejor» = caer menos (percentil alto = el real cayó menos que los monos).

## ¿Se parecen los monos a la estrategia real?
| qué | real | monos (media) | monos p5–p95 |
|---|---|---|---|
| Nº operaciones | 167.0 | 141.8 | 134.0 – 150.0 |
| Duración media (velas) | 39.5 | 38.9 | 33.4 – 44.9 |
| Exposición media | 43% | 32% | 28% – 36% |

Factor de duración calibrado: 1.46 (duración media de los pilotos: 29.6, 35.9, 38.3).

## Cómo se construyen los monos
- Mismo universo y mismo nº de operaciones por activo que la estrategia real en el periodo.
- Cada operación dura lo que dura una operación real (sorteada entre las duraciones reales que no acabaron en stop), alargada por un factor calibrado con monos piloto para que la duración media **después** de los stops se parezca a la real.
- Entradas colocadas al azar sin solaparse; stop = el `stop_price` que la estrategia daría ese día (cierre − k·ATR); mismo sizing al 1 %, máx. posiciones, costes y kill switch (si está activado) vía `portfolio_sim`.

## Avisos
- Ganarle al azar es condición **necesaria, no suficiente**: una estrategia puede batir a los monos y aun así no ganarle a comprar y mantener, o no sobrevivir al kill switch.
- El p-valor es para **una** métrica (Sharpe). Si miras cinco métricas, alguna saldrá 'significativa' por suerte; decide la métrica antes de mirar.
- Los monos hacen menos operaciones (142) que la real (167): algunas entradas al azar no se pueden abrir (gap por debajo del stop o sin hueco). Compáralo con cuidado.
- La exposición media de los monos (32%) difiere de la real (43%) en más de un 15 %: el CAGR no es del todo comparable; fíjate más en Sharpe y expectancy.
- Los monos usan las mismas duraciones (calibradas para que, tras los stops, la duración media se parezca a la real), el mismo stop que daría la estrategia ese día y el mismo sizing del 1 %. Solo cambia CUÁNDO entran.
- Comparación SIN kill switch (como en las baselines).
- Un p-valor in-sample no garantiza nada fuera de muestra (ni en paper).

## Datos y configuración
- Estrategia: `donchian_etf`, universo SPY, EFA, EEM, IEF, GLD, DBC, VNQ, parámetros entry_n=55, exit_n=20, atr_mult=2.0, atr_n=20.
- Periodo: **in-sample** 2007-07-01 → 2020-12-31.
- Reglas: portfolio_sim con reglas duras: riesgo 0% por operación con stop, máx. 3 posiciones, exposición ≤ 100%, **SIN kill switch**.
- Costes (base): crypto: slippage 20 pb/lado, comisión 0.250 %/lado; equity: slippage 5 pb/lado, comisión 0.000 %/lado.
- Fuente de datos: yfinance (ajuste: auto_adjust).

## Archivos
- `azar.csv`: métricas de cada mono · `azar_resumen.csv`: la tabla de arriba.
- `curvas.csv.gz`: equity real y de los primeros monos (submuestreada).
- `azar.html`: interactivo (histograma, violines, espaguetis) · `azar.png`: preview.
