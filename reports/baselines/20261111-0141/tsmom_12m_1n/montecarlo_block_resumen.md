# Monte Carlo — TSMOM 12m 1/N (SPY, EFA, EEM, TLT, GLD)

Generado: 2026-11-11 02:04 (hora de Madrid)

## Qué se ha hecho

- Método: **block** (remuestrear bloques de rentabilidades diarias).
- Simulaciones: **5000**, semilla **42**.
- Capital inicial: 9.955 $. Periodo aproximado: 21.85 años.
- Eje de las trayectorias: días del calendario (misma longitud que el backtest).
- Kill switch (parada de emergencia): caída **mayor** del 10% desde el máximo.
- Umbral de ruina: el equity toca o baja de 7.964 $ (20% de pérdida desde el inicio).
- Las simulaciones **no se detienen** al tocar el kill switch; se deja seguir el camino y se cuenta cuántas lo habrían tocado.

## Resultados

| Métrica | Backtest (misma construcción) | p5 | p25 | p50 (mediana) | p75 | p95 | Rango del real (%) |
|---|---|---|---|---|---|---|---|
| Equity final | 37.735 $ | 21.160 $ | 30.035 $ | 39.083 $ | 50.111 $ | 72.857 $ | 46 |
| CAGR (crecimiento anualizado) | 6.3 % | 3.5 % | 5.2 % | 6.5 % | 7.7 % | 9.5 % | 46 |
| Máx. drawdown | -15.8 % | -30.5 % | -22.8 % | -19.1 % | -16.2 % | -13.3 % | 78 |
| Máx. días bajo el agua | 1005 | 582 | 887 | 1198 | 1668 | 2772 | 34 |

«Rango del real» es el porcentaje de simulaciones con un valor **menor o igual** al del backtest. En el CAGR, un rango alto significa que el histórico ganó más que la mayoría. En el drawdown (que es negativo), un rango alto significa que el histórico cayó *menos* que la mayoría (camino más suave).

## Probabilidades

| Pregunta | Probabilidad |
|---|---|
| ¿Tocar el kill switch (caída > 10% desde el máximo)? | 99.9 % |
| ¿Terminar por debajo del capital inicial? | 0.0 % |
| ¿Tocar el umbral de ruina (pérdida ≥ 20% desde el inicio)? | 2.1 % |

En el backtest (misma construcción que las sims): kill switch = sí; ruina = no; termina por debajo del inicio = no.

## ¿Fue suerte?

El CAGR histórico queda en el percentil 46 (típico); el drawdown queda en el percentil 78.

## Cómo leer los gráficos

- **Abanico (fan chart):** las bandas sombreadas cubren el 90 % (p5–p95) y el 50 % (p25–p75) de los caminos simulados. La línea gruesa es el backtest. Las líneas finas son una muestra, no las 5000.
- **Histograma de drawdown:** la línea roja es el kill switch (10%). Si mucha masa queda a la izquierda, la estrategia salta la parada de emergencia a menudo cuando se reordena el azar.
- **Histograma de CAGR:** en el método ``shuffle`` suele ser una sola barra (el CAGR no cambia). En ``bootstrap`` y ``block`` sí hay distribución.

## Advertencias

- Remuestreo por bloques de 21 rentabilidades diarias (conserva un poco la autocorrelación; asume que los bloques son intercambiables).
- Se asume que las operaciones (o los bloques de días) son intercambiables: en la realidad una racha de pérdidas puede tener causa común (un régimen de mercado), y barajarla las trata como independientes.
- Un Monte Carlo no convierte un backtest en predicción. Sirve para ver si el camino que ya vimos era frágil al orden o a la muestra.

