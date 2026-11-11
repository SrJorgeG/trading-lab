# ¿Mejor que el azar? — tsmom_etf — contra el azar
Generado: 2026-11-11 16:34 (hora de Madrid)

> Se comparan los resultados de la estrategia con los de **1000 estrategias al azar** (semilla 42) que operan lo mismo, con las mismas reglas y costes, pero entrando en momentos aleatorios. Cifras de `scripts/random_benchmark.py`.

## Veredicto
**INDISTINGUIBLE DEL AZAR** en Sharpe: real 0.41, por encima del 40% de los monos, p-valor empírico = 0.597.

Umbrales (fijados antes de mirar): p < 0,05 → «ventaja probable»; 0,05 ≤ p < 0,10 → «indicio débil»; p ≥ 0,10 → «indistinguible del azar». p = (1 + nº de monos ≥ real) / (N + 1), una cola.

## Todas las métricas
| métrica | real | azar p5 | azar mediana | azar p95 | percentil real | p-valor | veredicto |
|---|---|---|---|---|---|---|---|
| Sharpe | 0.41 | 0.03 | 0.47 | 0.81 | 40% | 0.597 | indistinguible del azar |
| CAGR | 1.4% | 0.0% | 1.2% | 2.3% | 62% | 0.382 | indistinguible del azar |
| Máx. caída | -9.5% | -11.3% | -6.4% | -3.8% | 13% | 0.873 | indistinguible del azar |
| MAR (CAGR / caída) | 0.15 | 0.01 | 0.17 | 0.42 | 41% | 0.591 | indistinguible del azar |
| Expectancy (R) | 0.941 | 0.059 | 1.186 | 2.663 | 40% | 0.602 | indistinguible del azar |

En la caída máxima, «mejor» = caer menos (percentil alto = el real cayó menos que los monos).

## ¿Se parecen los monos a la estrategia real?
| qué | real | monos (media) | monos p5–p95 |
|---|---|---|---|
| Nº operaciones | 43.0 | 28.7 | 22.0 – 35.0 |
| Duración media (velas) | 216.3 | 213.8 | 125.1 – 323.6 |
| Exposición media | 34% | 23% | 13% – 34% |

Factor de duración calibrado: 2.34 (duración media de los pilotos: 112.5, 172.2, 223.9).

## Cómo se construyen los monos
- Mismo universo y mismo nº de operaciones por activo que la estrategia real en el periodo.
- Cada operación dura lo que dura una operación real (sorteada entre las duraciones reales que no acabaron en stop), alargada por un factor calibrado con monos piloto para que la duración media **después** de los stops se parezca a la real.
- Entradas colocadas al azar sin solaparse; stop = el `stop_price` que la estrategia daría ese día (cierre − k·ATR); mismo sizing al 1 %, máx. posiciones, costes y kill switch (si está activado) vía `portfolio_sim`.

## Avisos
- Ganarle al azar es condición **necesaria, no suficiente**: una estrategia puede batir a los monos y aun así no ganarle a comprar y mantener, o no sobrevivir al kill switch.
- El p-valor es para **una** métrica (Sharpe). Si miras cinco métricas, alguna saldrá 'significativa' por suerte; decide la métrica antes de mirar.
- Los monos hacen menos operaciones (29) que la real (43): algunas entradas al azar no se pueden abrir (gap por debajo del stop o sin hueco). Compáralo con cuidado.
- La exposición media de los monos (23%) difiere de la real (34%) en más de un 15 %: el CAGR no es del todo comparable; fíjate más en Sharpe y expectancy.
- Los monos usan las mismas duraciones (calibradas para que, tras los stops, la duración media se parezca a la real), el mismo stop que daría la estrategia ese día y el mismo sizing del 1 %. Solo cambia CUÁNDO entran.
- Comparación SIN kill switch (como en las baselines).
- Un p-valor in-sample no garantiza nada fuera de muestra (ni en paper).

## Datos y configuración
- Estrategia: `tsmom_etf`, universo SPY, EFA, EEM, IEF, GLD, DBC, VNQ, parámetros lookback=252, atr_mult=4.0, atr_n=20.
- Periodo: **in-sample** 2007-07-01 → 2020-12-31.
- Reglas: portfolio_sim con reglas duras: riesgo 0% por operación con stop, máx. 3 posiciones, exposición ≤ 100%, **SIN kill switch**.
- Costes (base): crypto: slippage 20 pb/lado, comisión 0.250 %/lado; equity: slippage 5 pb/lado, comisión 0.000 %/lado.
- Fuente de datos: yfinance (ajuste: auto_adjust).

## Archivos
- `azar.csv`: métricas de cada mono · `azar_resumen.csv`: la tabla de arriba.
- `curvas.csv.gz`: equity real y de los primeros monos (submuestreada).
- `azar.html`: interactivo (histograma, violines, espaguetis) · `azar.png`: preview.
