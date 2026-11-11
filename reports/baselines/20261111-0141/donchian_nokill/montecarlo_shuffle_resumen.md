# Monte Carlo — Donchian 20/10 — igual pero SIN kill switch (informativo)

Generado: 2026-11-11 02:04 (hora de Madrid)

## Qué se ha hecho

- Método: **shuffle** (barajar el orden de las operaciones (sin reemplazo)).
- Simulaciones: **5000**, semilla **42**.
- Capital inicial: 10.000 $. Periodo aproximado: 21.85 años.
- Eje de las trayectorias: número de operación (el equity solo se actualiza al cerrar).
- Kill switch (parada de emergencia): caída **mayor** del 10% desde el máximo.
- Umbral de ruina: el equity toca o baja de 8.000 $ (20% de pérdida desde el inicio).
- Las simulaciones **no se detienen** al tocar el kill switch; se deja seguir el camino y se cuenta cuántas lo habrían tocado.

## Resultados

| Métrica | Backtest (misma construcción) | p5 | p25 | p50 (mediana) | p75 | p95 | Rango del real (%) |
|---|---|---|---|---|---|---|---|
| Equity final | 74.899 $ | 74.899 $ | 74.899 $ | 74.899 $ | 74.899 $ | 74.899 $ | 50 |
| CAGR (crecimiento anualizado) | 9.7 % | 9.7 % | 9.7 % | 9.7 % | 9.7 % | 9.7 % | 50 |
| Máx. drawdown | -8.6 % | -34.5 % | -21.2 % | -15.5 % | -11.5 % | -7.5 % | 91 |
| Máx. días bajo el agua | 708 | 673 | 895 | 1154 | 1488 | 2226 | 8 |

«Rango del real» es el porcentaje de simulaciones con un valor **menor o igual** al del backtest. En el CAGR, un rango alto significa que el histórico ganó más que la mayoría. En el drawdown (que es negativo), un rango alto significa que el histórico cayó *menos* que la mayoría (camino más suave).

## Probabilidades

| Pregunta | Probabilidad |
|---|---|
| ¿Tocar el kill switch (caída > 10% desde el máximo)? | 84.6 % |
| ¿Terminar por debajo del capital inicial? | 0.0 % |
| ¿Tocar el umbral de ruina (pérdida ≥ 20% desde el inicio)? | 11.4 % |

En el backtest (misma construcción que las sims): kill switch = no; ruina = no; termina por debajo del inicio = no.

## ¿Fue suerte?

El CAGR y el equity final no cambian al barajar, así que no sirven para hablar de suerte en el resultado final: mira el drawdown. El drawdown histórico queda alrededor del percentil 91 de las simulaciones (ni extremo).

## Backtest original (marcado a mercado, cada día)

Estas cifras sí incluyen el vaivén de las posiciones abiertas. No se comparan directamente con las bandas de arriba.

- Equity final: 74.899 $
- CAGR: 9.7 %
- Máx. drawdown: -12.2 %
- Máx. días bajo el agua: 999

## Cómo leer los gráficos

- **Abanico (fan chart):** las bandas sombreadas cubren el 90 % (p5–p95) y el 50 % (p25–p75) de los caminos simulados. La línea gruesa es el backtest. Las líneas finas son una muestra, no las 5000.
- **Histograma de drawdown:** la línea roja es el kill switch (10%). Si mucha masa queda a la izquierda, la estrategia salta la parada de emergencia a menudo cuando se reordena el azar.
- **Histograma de CAGR:** en el método ``shuffle`` suele ser una sola barra (el CAGR no cambia). En ``bootstrap`` y ``block`` sí hay distribución.

## Advertencias

- Se baraja el P&L en dólares de cada operación ya cerrada (tamaño fijo, no se recompone el 1 % sobre el equity del momento).
- La trayectoria solo se actualiza al cerrar cada operación: no captura el drawdown intradía ni el de posiciones aún abiertas.
- Al barajar sin reemplazo, la suma de P&L (sizing aditivo) y el producto de factores (sizing compuesto) no cambian: el equity final y el CAGR son idénticos en todas las simulaciones. Solo cambia el camino y el drawdown.
- El drawdown «a mercado» del backtest (marcado cada día, con posiciones abiertas) puede ser peor que el de la trayectoria de P&L realizado que se compara con las simulaciones.
- Se asume que las operaciones (o los bloques de días) son intercambiables: en la realidad una racha de pérdidas puede tener causa común (un régimen de mercado), y barajarla las trata como independientes.
- Un Monte Carlo no convierte un backtest en predicción. Sirve para ver si el camino que ya vimos era frágil al orden o a la muestra.

