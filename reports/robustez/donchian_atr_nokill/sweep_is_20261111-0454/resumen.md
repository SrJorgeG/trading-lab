# Mapa de parámetros — Donchian (SPY, QQQ, BTC) sin kill switch
Generado: 2026-11-11 04:54 (hora de Madrid)

> Herramienta de **robustez**, no de optimización. Enseña si el resultado aguanta al mover los parámetros (meseta) o si solo sale bien en un punto (pico). **No elijas los parámetros mirando este mapa**: eso sería sobreajustar. Todas las cifras salen de `scripts/param_sweep.py` ejecutado con el motor real.

## Veredicto
**Robustez 89/100 → meseta: robusto a los parámetros** (métrica: Sharpe; «casi igual» = dentro del 20% del mejor).

| indicador | valor | qué significa |
|---|---|---|
| Mejor Sharpe | 1.60 | en entry_n=20, exit_n=10, atr_mult=2 |
| Mediana del mapa | 1.21 | lo típico al mover los parámetros |
| Mejor / mediana | 1.32 | cerca de 1 = todo el mapa parecido; > 2 = el mejor es excepcional (sospechoso) |
| Vecinos del mejor dentro del 20% | 88 % (26 vecinos) | si se tuerce un poco un parámetro, ¿sigue bien? |
| Meseta conectada al mejor | 31 % del mapa (101 celdas) | tamaño de la zona buena alrededor del mejor |
| Ancho de la meseta por parámetro | entry_n: 73 %, exit_n: 100 %, atr_mult: 100 % | qué parte de cada eje cubre la zona buena |
| Combinaciones con Sharpe > 0 | 100 % | |
| Parámetros por defecto (entry_n=20, exit_n=10, atr_mult=2) | 1.60 (percentil 100 %) | dentro de la meseta del mejor; vecinos dentro del 20% de su valor: 88 % |

Fórmula de la puntuación: 100 × (0,5 · vecinos + 0,3 · min(1, meseta / 30 %) + 0,2 · mediana/mejor). ≥ 70 meseta, 40–70 mixto, < 40 pico. Es una regla práctica, no un test estadístico.

### La misma prueba con otras métricas
| métrica | robustez | veredicto | mejor | mediana |
|---|---|---|---|---|
| Sharpe | 89/100 | meseta | 1.60 | 1.21 |
| CAGR | 56/100 | mixto | 26.0% | 14.2% |
| Máx. caída | 58/100 | mixto | -8.2% | -14.5% |
| MAR (CAGR / caída) | 25/100 | pico | 1.84 | 0.95 |
| Expectancy (R) | 51/100 | mixto | 3.458 | 1.602 |

## Sobreajuste: Deflated Sharpe y PBO
- **Deflated Sharpe Ratio (DSR) = 0.999** con N = 330 intentos. Probabilidad de que el Sharpe del mejor sea real y no fruto de elegir el máximo de 330. Regla habitual: fiarse solo si DSR ≥ 0,95.
  - Sharpe diario del mejor 0.0838 (anualizado ≈ 1.60); Sharpe que se esperaría solo por suerte al elegir el máximo: 0.0224 (anualizado ≈ 0.43). Asimetría 0.58, curtosis 24.4, 2850 días.
  - Contando también lo anotado antes en el registro (N = 331): DSR = 0.999.
  - Ojo: las configuraciones vecinas están muy correladas, así que N exagera el nº de intentos independientes (el DSR sale conservador).
- **PBO (probabilidad de sobreajuste, CSCV) = 33 %** sobre 12.870 particiones de 16 bloques. Es la frecuencia con la que la mejor configuración en una mitad de la historia queda por debajo de la mediana en la otra mitad. < 10 % bien, 10–50 % regular, ≥ 50 % elegir 'la mejor' no sirve.
  - Sharpe diario mediano fuera de muestra del elegido: 0.0688.

## Las 10 mejores combinaciones por Sharpe
| entry_n | exit_n | atr_mult | sharpe | cagr | max_dd | mar | expectancy_r | trades | exposure |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 10 | 2 | 1.60 | 22.5% | -12.2% | 1.84 | 1.586 | 116 | 46.4% |
| 15 | 10 | 2 | 1.56 | 21.3% | -13.5% | 1.57 | 1.418 | 129 | 46.6% |
| 20 | 10 | 2.5 | 1.55 | 18.3% | -10.8% | 1.70 | 1.315 | 114 | 40.6% |
| 20 | 5 | 2.5 | 1.54 | 12.7% | -9.4% | 1.34 | 0.626 | 157 | 35.2% |
| 20 | 5 | 3 | 1.54 | 10.7% | -8.8% | 1.22 | 0.527 | 157 | 30.1% |
| 20 | 10 | 3 | 1.54 | 15.7% | -9.6% | 1.63 | 1.106 | 114 | 35.1% |
| 15 | 5 | 3 | 1.53 | 10.9% | -10.0% | 1.08 | 0.488 | 172 | 31.7% |
| 20 | 5 | 2 | 1.53 | 14.9% | -10.4% | 1.43 | 0.768 | 158 | 40.3% |
| 25 | 10 | 3 | 1.52 | 15.6% | -9.7% | 1.61 | 1.183 | 106 | 34.5% |
| 15 | 10 | 3 | 1.51 | 15.4% | -10.9% | 1.41 | 0.996 | 125 | 36.2% |

## Avisos
- Se han probado **330 configuraciones**. Quedarse con la mejor de 330 infla el resultado por pura suerte (sesgo de selección). Usa el mapa para ver la FORMA (meseta o pico), no para elegir el máximo.
- PBO = 33%: riesgo de sobreajuste moderado al elegir la mejor.
- Barrido SIN kill switch (como en las baselines). Con la regla del 10 % activada los números cambian mucho; repite con kill switch antes de cualquier veredicto.

## Datos y configuración
- Estrategia: `donchian_atr` (baseline), universo SPY, QQQ, BTC/USD.
- Periodo: **in-sample** 2015-09-17 → 2023-07-06 (corte IS/OOS como `runner.py`).
- Rejilla: entry_n=10..60 (11) × exit_n=5..30 (6) × atr_mult=1.5..3.5 (5) = **330 configuraciones** (0 calculadas, 330 de caché). Resto de parámetros: atr_n=20
- Reglas: portfolio_sim con reglas duras: riesgo 1% por operación con stop, máx. 3 posiciones, exposición ≤ 100%, **SIN kill switch**.
- Costes (base): crypto: slippage 10 pb/lado, comisión 0.250 %/lado; equity: slippage 5 pb/lado, comisión 0.000 %/lado.
- Fuente de datos: yfinance (ajuste: auto_adjust).
- Intentos ya anotados en el registro para `donchian_atr` antes de este barrido: 1.

## Archivos
- `sweep.csv`: una fila por combinación con todas las métricas.
- `robustez.json`: puntuaciones, DSR, PBO y avisos.
- `mapa.html`: interactivo (mapa de calor, superficie 3D, PBO). Ábrelo en el navegador; funciona sin internet.
- `mapa.png`: preview.
