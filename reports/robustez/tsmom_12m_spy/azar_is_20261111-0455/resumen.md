# ¿Mejor que el azar? — TSMOM 12 meses (SPY)
Generado: 2026-11-11 04:55 (hora de Madrid)

> Se comparan los resultados de la estrategia con los de **1000 estrategias al azar** (semilla 42) que operan lo mismo, con las mismas reglas y costes, pero entrando en momentos aleatorios. Cifras de `scripts/random_benchmark.py`.

## Veredicto
**INDISTINGUIBLE DEL AZAR** en Sharpe: real 0.49, por encima del 68% de los monos, p-valor empírico = 0.326.

Umbrales (fijados antes de mirar): p < 0,05 → «ventaja probable»; 0,05 ≤ p < 0,10 → «indicio débil»; p ≥ 0,10 → «indistinguible del azar». p = (1 + nº de monos ≥ real) / (N + 1), una cola.

## Todas las métricas
| métrica | real | azar p5 | azar mediana | azar p95 | percentil real | p-valor | veredicto |
|---|---|---|---|---|---|---|---|
| Sharpe | 0.49 | 0.34 | 0.45 | 0.70 | 68% | 0.326 | indistinguible del azar |
| CAGR | 6.4% | 4.6% | 6.7% | 10.0% | 42% | 0.580 | indistinguible del azar |
| Máx. caída | -33.7% | -55.4% | -55.2% | -33.7% | 96% | 0.077 | indicio débil (no concluyente) |
| MAR (CAGR / caída) | 0.19 | 0.08 | 0.12 | 0.30 | 86% | 0.142 | indistinguible del azar |

En la caída máxima, «mejor» = caer menos (percentil alto = el real cayó menos que los monos).

## ¿Se parecen los monos a la estrategia real?
| qué | real | monos (media) | monos p5–p95 |
|---|---|---|---|
| Nº órdenes | 12.0 | 11.5 | 11.0 – 12.0 |
| Exposición media | 84% | 84% | 84% – 85% |
| Cambios de asignación (rotación) | 11.0 | 11.0 | 11.0 – 11.0 |

## Cómo se construyen los monos
- Se trocea la asignación real en tramos de meses con la misma cartera.
- Cada mono usa las mismas carteras, el mismo nº de tramos (misma rotación) y los mismos meses en cada cartera; solo cambia el orden y la longitud de los tramos.
- Se simula con `allocation_sim` (decisión a fin de mes, ejecución en la apertura siguiente, mismos costes).

## Avisos
- Ganarle al azar es condición **necesaria, no suficiente**: una estrategia puede batir a los monos y aun así no ganarle a comprar y mantener, o no sobrevivir al kill switch.
- El p-valor es para **una** métrica (Sharpe). Si miras cinco métricas, alguna saldrá 'significativa' por suerte; decide la métrica antes de mirar.
- Los monos de una estrategia mensual tienen exactamente los mismos meses invertidos y el mismo nº de cambios; con un solo activo y pocos cambios hay pocas combinaciones distintas, así que el p-valor es grueso.
- Un p-valor in-sample no garantiza nada fuera de muestra (ni en paper).

## Datos y configuración
- Estrategia: `tsmom_12m`, universo SPY, parámetros months=12, skip=0.
- Periodo: **in-sample** 2005-01-01 → 2020-04-20.
- Reglas: asignación mensual por pesos (allocation_sim): decide con el cierre de fin de mes y ejecuta en la apertura siguiente; **sin** stop, sin 1 % de riesgo y sin kill switch.
- Costes (base): crypto: slippage 10 pb/lado, comisión 0.250 %/lado; equity: slippage 5 pb/lado, comisión 0.000 %/lado.
- Fuente de datos: yfinance (ajuste: auto_adjust).

## Archivos
- `azar.csv`: métricas de cada mono · `azar_resumen.csv`: la tabla de arriba.
- `curvas.csv.gz`: equity real y de los primeros monos (submuestreada).
- `azar.html`: interactivo (histograma, violines, espaguetis) · `azar.png`: preview.
