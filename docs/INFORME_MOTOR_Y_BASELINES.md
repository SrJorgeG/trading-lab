# Informe del motor de backtest y resultados de referencia

Preparado el 11 nov 2026 (hora de Madrid). El **código del motor no está en `main`**: vive en la rama [`prep/motor-backtest`](https://github.com/SrJorgeG/trading-lab/tree/prep/motor-backtest) y no se fusiona hasta que Fable lo revise. Aquí solo está el resumen de lo que hace, los números de referencia y las decisiones que hay que tomar mañana.

Detalle técnico: `docs/PREP_NOTES.md`. Tabla completa y advertencias: `docs/baselines.md`. CSV: `reports/baselines/20261111-0141/resumen.csv`.

## Qué hace el motor

Es un motor de backtest en Python 3.12 (gestionado con uv) preparado en esa rama, **sin usar cupo de Claude**. Descarga y cachea velas diarias, simula una cartera vela a vela con las reglas duras del kit (riesgo del 1 % por operación, stop obligatorio, máximo 3 posiciones, sin apalancamiento ni cortos, parada de emergencia si la cuenta cae más de un 10 % desde su máximo) y genera métricas e informes. También incluye walk-forward y pruebas de estrés, y un simulador por pesos solo para las estrategias mensuales de referencia.

En esa rama: **56 tests offline y 2 de red, todos en verde**; ruff (el linter) está limpio.

## Cómo leer los números

- **CAGR** (crecimiento anual compuesto): lo que habría crecido el capital, de media, cada año, si el crecimiento se hubiera repetido de forma compuesta.
- **Máximo drawdown** (peor caída): la mayor bajada desde un máximo hasta el siguiente mínimo. Un −55 % significa que, en el peor momento, se perdió más de la mitad.
- **Sharpe**: rentabilidad respecto al riesgo (al vaivén). Cuanto más alto, mejor. Aquí se calcula sin tipo libre de riesgo.

## Resultados de referencia (no son hipótesis)

Esto **no** son las hipótesis pre-registradas. Son estrategias clásicas con parámetros de manual, corridas **una sola vez** el 11 nov 2026 a las 01:41 (hora de Madrid), sin optimizar, con 10.000 $ virtuales y costes incluidos (ETFs: 5 pb de slippage por lado; cripto: 0,25 % de comisión + 10 pb de slippage por lado). Periodo 2005-01-03 → 2026-11-10 (BTC desde 2015-01-01). No uses estos números para elegir parámetros mañana.

| Estrategia | CAGR | Máx. drawdown | Sharpe |
|---|---|---|---|
| Comprar y mantener SPY | 10.7 % | -55.2 % | 0.63 |
| Comprar y mantener BTC (desde 2015) | 58.7 % | -83.4 % | 1.03 |
| Faber SMA 10 meses (SPY) | 7.8 % | -25.9 % | 0.66 |
| Momentum 12 meses (SPY) | 9.4 % | -33.7 % | 0.68 |
| Momentum 12 meses, 5 activos al 1/N (SPY, EFA, EEM, TLT, GLD) | 6.3 % | -15.8 % | 0.70 |
| Dual momentum (SPY/EFA → IEF; filtro BIL) | 8.1 % | -33.7 % | 0.57 |
| Donchian 20/10, stop 2×ATR (SPY, QQQ, BTC) — reglas duras completas | 0.7 % | -10.1 % | 0.21 |
| Donchian 20/10 — igual pero **sin** kill switch (solo informativo) | 9.7 % | -12.2 % | 1.10 |

## Tres decisiones para Fable

1. **Kill switch (parada de emergencia).** Con la regla literal (caer un 10 % desde el máximo → parar para siempre), el Donchian de referencia se detiene el **2015-09-13** y pasa unos 11 años en efectivo. Por eso, con todas las reglas, el CAGR se queda en **0.7 %** (Sharpe 0.21). Sin el kill switch, el mismo sistema da **9.7 %** de CAGR y Sharpe 1.10, con una caída máxima de -12.2 %. Hay que decidir si el criterio de aprobado se mide con el kill switch permanente (como en real) o también sin él, y pre-registrar ambos números.

2. **Estrategias mensuales (Faber, momentum 12 meses y dual momentum).** Van al 100 % del capital y **no tienen stop por operación**, así que no encajan con las reglas de arriesgar un 1 % y stop obligatorio. Hoy solo existen como referencia. Hay que decidir cómo adaptarlas (por ejemplo, un stop de catástrofe y sizing al 1 %, sizing por volatilidad con tope del 100 %, o un cambio explícito de la regla) **antes** de probarlas como candidatas.

3. **Peso de BTC en el Donchian.** En la variante sin kill switch (costes base), el beneficio se reparte así: BTC 43.193 $, QQQ 11.654 $, SPY 10.053 $. BTC aporta **aproximadamente dos tercios** del beneficio. Conviene tenerlo en cuenta al fijar el universo y los criterios.

## Advertencias (léelas antes de creerte nada)

- Los datos salen de **yfinance** (precios ajustados por splits y dividendos). Falta contrastarlos con Alpaca cuando haya claves.
- El cargador de Alpaca está escrito y **no se ha ejecutado**.
- **vectorbt** y el simulador propio (`portfolio_sim`) no siempre coinciden al céntimo, sobre todo con stops cercanos (vectorbt no aplica slippage a la salida por stop y desempata distinto). El veredicto debe salir de `portfolio_sim`.
- No se modelan impuestos, liquidez, subastas de apertura ni el rendimiento del efectivo (en la simulación el efectivo no rinde nada).
- Una sola trayectoria histórica (2005–2026, un mercado alcista largo en EE. UU.; BTC solo desde 2015) no es una predicción.
