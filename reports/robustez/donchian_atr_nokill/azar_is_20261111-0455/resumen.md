# ¿Mejor que el azar? — Donchian 20/10 (SPY, QQQ, BTC) sin kill switch
Generado: 2026-11-11 04:55 (hora de Madrid)

> Se comparan los resultados de la estrategia con los de **1000 estrategias al azar** (semilla 42) que operan lo mismo, con las mismas reglas y costes, pero entrando en momentos aleatorios. Cifras de `scripts/random_benchmark.py`.

## Veredicto
**VENTAJA PROBABLE** en Sharpe: real 1.60, por encima del 97% de los monos, p-valor empírico = 0.034.

Umbrales (fijados antes de mirar): p < 0,05 → «ventaja probable»; 0,05 ≤ p < 0,10 → «indicio débil»; p ≥ 0,10 → «indistinguible del azar». p = (1 + nº de monos ≥ real) / (N + 1), una cola.

## Todas las métricas
| métrica | real | azar p5 | azar mediana | azar p95 | percentil real | p-valor | veredicto |
|---|---|---|---|---|---|---|---|
| Sharpe | 1.60 | 0.77 | 1.18 | 1.57 | 97% | 0.034 | ventaja probable |
| CAGR | 22.5% | 6.6% | 12.1% | 19.2% | 99% | 0.015 | ventaja probable |
| Máx. caída | -12.2% | -21.6% | -15.4% | -11.3% | 89% | 0.115 | indistinguible del azar |
| MAR (CAGR / caída) | 1.84 | 0.38 | 0.78 | 1.34 | 100% | 0.005 | ventaja probable |
| Expectancy (R) | 1.586 | 0.537 | 0.951 | 1.613 | 95% | 0.055 | indicio débil (no concluyente) |

En la caída máxima, «mejor» = caer menos (percentil alto = el real cayó menos que los monos).

## ¿Se parecen los monos a la estrategia real?
| qué | real | monos (media) | monos p5–p95 |
|---|---|---|---|
| Nº operaciones | 116.0 | 110.4 | 104.0 – 116.0 |
| Duración media (velas) | 29.8 | 29.0 | 24.8 – 33.9 |
| Exposición media | 46% | 40% | 34% – 46% |

Factor de duración calibrado: 1.55 (duración media de los pilotos: 21.6, 27.4, 28.7).

## Cómo se construyen los monos
- Mismo universo y mismo nº de operaciones por activo que la estrategia real en el periodo.
- Cada operación dura lo que dura una operación real (sorteada entre las duraciones reales que no acabaron en stop), alargada por un factor calibrado con monos piloto para que la duración media **después** de los stops se parezca a la real.
- Entradas colocadas al azar sin solaparse; stop = el `stop_price` que la estrategia daría ese día (cierre − k·ATR); mismo sizing al 1 %, máx. posiciones, costes y kill switch (si está activado) vía `portfolio_sim`.

## Avisos
- Ganarle al azar es condición **necesaria, no suficiente**: una estrategia puede batir a los monos y aun así no ganarle a comprar y mantener, o no sobrevivir al kill switch.
- El p-valor es para **una** métrica (Sharpe). Si miras cinco métricas, alguna saldrá 'significativa' por suerte; decide la métrica antes de mirar.
- Los monos usan las mismas duraciones (calibradas para que, tras los stops, la duración media se parezca a la real), el mismo stop que daría la estrategia ese día y el mismo sizing del 1 %. Solo cambia CUÁNDO entran.
- Comparación SIN kill switch (como en las baselines).
- Un p-valor in-sample no garantiza nada fuera de muestra (ni en paper).

## Datos y configuración
- Estrategia: `donchian_atr`, universo SPY, QQQ, BTC/USD, parámetros entry_n=20, exit_n=10, atr_mult=2.0, atr_n=20.
- Periodo: **in-sample** 2015-09-17 → 2023-07-06.
- Reglas: portfolio_sim con reglas duras: riesgo 1% por operación con stop, máx. 3 posiciones, exposición ≤ 100%, **SIN kill switch**.
- Costes (base): crypto: slippage 10 pb/lado, comisión 0.250 %/lado; equity: slippage 5 pb/lado, comisión 0.000 %/lado.
- Fuente de datos: yfinance (ajuste: auto_adjust).

## Archivos
- `azar.csv`: métricas de cada mono · `azar_resumen.csv`: la tabla de arriba.
- `curvas.csv.gz`: equity real y de los primeros monos (submuestreada).
- `azar.html`: interactivo (histograma, violines, espaguetis) · `azar.png`: preview.
