# Mapa de parámetros — TSMOM (SPY): meses de lookback × meses saltados
Generado: 2026-11-11 04:54 (hora de Madrid)

> Herramienta de **robustez**, no de optimización. Enseña si el resultado aguanta al mover los parámetros (meseta) o si solo sale bien en un punto (pico). **No elijas los parámetros mirando este mapa**: eso sería sobreajustar. Todas las cifras salen de `scripts/param_sweep.py` ejecutado con el motor real.

## Veredicto
**Robustez 97/100 → meseta: robusto a los parámetros** (métrica: Sharpe; «casi igual» = dentro del 20% del mejor).

| indicador | valor | qué significa |
|---|---|---|
| Mejor Sharpe | 0.67 | en months=19, skip=2 |
| Mediana del mapa | 0.56 | lo típico al mover los parámetros |
| Mejor / mediana | 1.19 | cerca de 1 = todo el mapa parecido; > 2 = el mejor es excepcional (sospechoso) |
| Vecinos del mejor dentro del 20% | 100 % (5 vecinos) | si se tuerce un poco un parámetro, ¿sigue bien? |
| Meseta conectada al mejor | 54 % del mapa (37 celdas) | tamaño de la zona buena alrededor del mejor |
| Ancho de la meseta por parámetro | months: 62 %, skip: 100 % | qué parte de cada eje cubre la zona buena |
| Combinaciones con Sharpe > 0 | 100 % | |
| Parámetros por defecto (months=12, skip=0) | 0.49 (percentil 25 %) | fuera de la meseta del mejor; vecinos dentro del 20% de su valor: 100 % |

Fórmula de la puntuación: 100 × (0,5 · vecinos + 0,3 · min(1, meseta / 30 %) + 0,2 · mediana/mejor). ≥ 70 meseta, 40–70 mixto, < 40 pico. Es una regla práctica, no un test estadístico.

### La misma prueba con otras métricas
| métrica | robustez | veredicto | mejor | mediana |
|---|---|---|---|---|
| Sharpe | 97/100 | meseta | 0.67 | 0.56 |
| CAGR | 96/100 | meseta | 9.3% | 7.4% |
| Máx. caída | 25/100 | pico | -21.1% | -33.7% |
| MAR (CAGR / caída) | 28/100 | pico | 0.30 | 0.23 |

## Sobreajuste: Deflated Sharpe y PBO
- **Deflated Sharpe Ratio (DSR) = 0.969** con N = 69 intentos. Probabilidad de que el Sharpe del mejor sea real y no fruto de elegir el máximo de 69. Regla habitual: fiarse solo si DSR ≥ 0,95.
  - Sharpe diario del mejor 0.0419 (anualizado ≈ 0.67); Sharpe que se esperaría solo por suerte al elegir el máximo: 0.0113 (anualizado ≈ 0.18). Asimetría -0.53, curtosis 19.6, 3850 días.
  - Contando también lo anotado antes en el registro (N = 72): DSR = 0.969.
  - Ojo: las configuraciones vecinas están muy correladas, así que N exagera el nº de intentos independientes (el DSR sale conservador).
- **PBO (probabilidad de sobreajuste, CSCV) = 87 %** sobre 12.870 particiones de 16 bloques. Es la frecuencia con la que la mejor configuración en una mitad de la historia queda por debajo de la mediana en la otra mitad. < 10 % bien, 10–50 % regular, ≥ 50 % elegir 'la mejor' no sirve.
  - Sharpe diario mediano fuera de muestra del elegido: 0.0258.

## Las 10 mejores combinaciones por Sharpe
| months | skip | sharpe | cagr | max_dd | mar | expectancy_r | trades | exposure |
|---|---|---|---|---|---|---|---|---|
| 19 | 2 | 0.67 | 9.3% | -33.7% | 0.28 | — | 9 | 86.4% |
| 21 | 2 | 0.66 | 9.3% | -33.7% | 0.28 | — | 3 | 87.5% |
| 22 | 2 | 0.65 | 9.0% | -33.7% | 0.27 | — | 3 | 86.4% |
| 15 | 2 | 0.65 | 9.0% | -33.7% | 0.27 | — | 11 | 84.6% |
| 16 | 2 | 0.64 | 9.1% | -33.7% | 0.27 | — | 9 | 87.0% |
| 22 | 1 | 0.64 | 8.9% | -33.7% | 0.26 | — | 3 | 85.8% |
| 7 | 1 | 0.64 | 8.6% | -33.7% | 0.26 | — | 19 | 79.9% |
| 18 | 2 | 0.63 | 8.8% | -33.7% | 0.26 | — | 7 | 85.3% |
| 20 | 1 | 0.63 | 8.8% | -33.7% | 0.26 | — | 3 | 87.5% |
| 17 | 2 | 0.63 | 8.8% | -33.7% | 0.26 | — | 7 | 86.4% |

## Avisos
- Se han probado **72 configuraciones**. Quedarse con la mejor de 72 infla el resultado por pura suerte (sesgo de selección). Usa el mapa para ver la FORMA (meseta o pico), no para elegir el máximo.
- El mejor resultado está en el **borde** de la rejilla (skip): el óptimo podría estar fuera. Ampliar la rejilla suma configuraciones (y anótalo en el registro).
- Los parámetros por defecto **no** están en la meseta del mejor: si se cambian para 'subirse' al máximo, eso es una variante nueva que hay que re-validar.
- **PBO = 87%**: la configuración que gana en una mitad de la historia queda por debajo de la mediana en la otra mitad la mayoría de las veces. Elegir 'la mejor' aquí no aporta nada. Con una meseta ancha es lo esperable: las combinaciones dan casi lo mismo y su orden cambia por ruido. Lectura práctica: no optimices, quédate con los parámetros pre-registrados (o los de manual).
- Estrategia mensual por pesos (allocation_sim): sin stop ni 1 % de riesgo ni kill switch. Es una referencia, no cumple las reglas duras tal cual.

## Datos y configuración
- Estrategia: `tsmom_12m` (baseline), universo SPY.
- Periodo: **in-sample** 2005-01-01 → 2020-04-20 (corte IS/OOS como `runner.py`).
- Rejilla: months=1..24 (24) × skip=0..2 (3) = **72 configuraciones** (0 calculadas, 72 de caché). Resto de parámetros: 
- Reglas: asignación mensual por pesos (allocation_sim): decide con el cierre de fin de mes y ejecuta en la apertura siguiente; **sin** stop, sin 1 % de riesgo y sin kill switch.
- Costes (base): crypto: slippage 10 pb/lado, comisión 0.250 %/lado; equity: slippage 5 pb/lado, comisión 0.000 %/lado.
- Fuente de datos: yfinance (ajuste: auto_adjust).
- Intentos ya anotados en el registro para `tsmom_12m (SPY)` antes de este barrido: 0.

## Archivos
- `sweep.csv`: una fila por combinación con todas las métricas.
- `robustez.json`: puntuaciones, DSR, PBO y avisos.
- `mapa.html`: interactivo (mapa de calor, superficie 3D, PBO). Ábrelo en el navegador; funciona sin internet.
- `mapa.png`: preview.
