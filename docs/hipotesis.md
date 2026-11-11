# Hipótesis pre-registradas — 2026-11-11, 15:26 (hora de Madrid)
Estado: PRE-REGISTRADO (no modificar criterios después de ver resultados)

> Este documento fija **qué vamos a probar y qué significa "aprobar" antes de ver ningún
> resultado de las candidatas**. No contiene ninguna cifra de rentabilidad de las candidatas
> (no se han probado). Los números que aparecen son supuestos (costes, fechas, parámetros),
> ejemplos con precios inventados o estimaciones marcadas como tales.
> No es asesoramiento financiero. Solo paper.

Glosario rápido (términos que se repiten):
- **IS / OOS**: *in-sample* (datos para desarrollar) / *out-of-sample* (datos reservados que se miran una sola vez, al final).
- **ATR(n)**: tamaño medio reciente de las velas (*Average True Range*), media de Wilder de n velas.
- **R**: el riesgo inicial de una operación en dólares (lo que se pierde si salta el stop, con costes). Una operación que gana 2R ha ganado el doble de lo que arriesgaba.
- **Expectancy**: ganancia media por operación, medida en R.
- **Drawdown (DD)**: caída del capital desde un máximo hasta el mínimo siguiente.
- **Sharpe**: rentabilidad media dividida por su volatilidad, anualizada (aquí con tipo libre de riesgo 0).
- **Hueco** (*slot*): cada una de las 3 posiciones que se pueden tener abiertas a la vez.

## 0. Fuente

- Se ha usado **`docs/estrategias.md`** (informe real de 20 estrategias + copy trading; no es el texto de ejemplo). Las citas de evidencia que aparecen abajo son las de ese informe, salvo donde se indica "conocimiento propio".
- También se han leído `CLAUDE.md`, `docs/PREP_NOTES.md`, `docs/VERIFICACIONES.md` y `docs/baselines.md`, y (solo para copiar la interfaz) el código de la rama `prep/motor-backtest`.
- Comprobación mínima de datos hecha en esta sesión con el MCP de Alpaca (solo la fecha de la primera barra, sin calcular nada):
  - Acciones/ETFs en Alpaca: primera barra en **2016-01** (probado con DBC pidiendo desde 2015).
  - Cripto en Alpaca: `BTC/USD`, `ETH/USD`, `LTC/USD`, `BCH/USD` empiezan en **2021-01**; `XRP/USD` en **2024-01**.
  - Consecuencia: la historia larga del backtest sale de **yfinance**; Alpaca sirve para contrastar el tramo común y para operar.
- Comisión cripto verificada en `docs/VERIFICACIONES.md` (doc oficial de Alpaca): tramo más bajo 15 pb *maker* / **25 pb *taker***. Se usa la *taker*.

### Aviso de contaminación (lo que ya he visto antes de pre-registrar)
El pre-registro ideal se escribe sin haber visto ningún resultado. No es el caso al 100 %, y hay que decirlo:

1. `docs/baselines.md` (que PREP_NOTES me autoriza a ver) trae resultados de **periodo completo, incluido lo que aquí será OOS**, de: buy & hold de SPY y BTC, Faber, TSMOM 12 meses, dual momentum y una ruptura Donchian 20/10 con stop 2×ATR sobre SPY, QQQ y BTC.
2. Al comprobar el formato de `docs/registro_pruebas.md` en la rama `prep` vi sus 6 filas, entre ellas un barrido in-sample de 330 combinaciones de Donchian cuya mejor celda era 20/10/2,0.

Medidas tomadas para que eso no decida nada:
- **Ningún parámetro sale de esas tablas.** Los de Donchian son los del "Sistema 2" de los Turtles que cita el informe (55/20, stop 2×ATR), no la celda 20/10 que salió mejor en el barrido. El de momentum es el de 12 meses de la literatura. Los de RSI(2) son los habituales de Connors.
- Los universos de las candidatas son distintos de los de los baselines.
- Los 330 + 72 intentos de los barridos previos **cuentan** como intentos previos de la familia (Donchian: H1 y H4; TSMOM: H2) al calcular cualquier corrección por pruebas múltiples en el paso 3.
- Aun así, el OOS de las candidatas de tendencia **no es del todo virgen**: sé que la tendencia en BTC y en ETFs "ha ido bien" en el periodo completo. Por eso el OOS se trata como condición necesaria, no suficiente: **la prueba de verdad es el paper trading posterior**, que nadie ha visto.

## 1. Descartadas

| Estrategia (nº en `estrategias.md`) | Motivo |
|---|---|
| 1. Comprar y mantener + rebalanceo | No es candidata: es el **benchmark** (el rival a batir). Además no lleva stop. |
| 2. DCA / DCA con filtro | Plan de acumulación, no sistema de entrada/salida; sin stop; con capital fijo de 10.000 $ no aplica. |
| 3. Cruce de medias | Misma familia que H2/H4 (tendencia) con evidencia más floja tras corregir *data-snooping* (Sullivan et al., 1999). Redundante. |
| 4. Faber (media de 10 meses) | **Absorbida en H2**: misma idea (tendencia mensual por activo). Probar Faber y TSMOM por separado serían dos variantes de lo mismo. |
| 7. Momentum cruzado en acciones | Pide muchas acciones individuales (sesgo de supervivencia) y, en su forma académica, cortos. Su idea de "ordenar por fuerza" se usa como desempate en H2. |
| 8. Dual momentum (GEM) | **Absorbida en H2**. La receta pura mete el 100 % en un solo ETF sin stop: choca con las reglas de 1 % y stop obligatorio. Evidencia "mixta" (solo del autor). |
| 9. Volatility targeting | Es una capa de tamaño, no una señal. El sizing por ATR al 1 % de riesgo ya reduce tamaño cuando sube la volatilidad. La versión académica usa apalancamiento. |
| 11. Bandas de Bollinger | Misma familia que H3 (reversión corta) sin evidencia mejor. Con una de reversión basta. |
| 12. Swing en pullbacks | La "vela de giro" exige criterio humano; no es 100 % mecánica. |
| 13. Pairs trading | Necesita cortos. Prohibido. |
| 14. PEAD | Necesita datos de sorpresa de beneficios (de pago) y acciones individuales. |
| 15. Carry / funding cripto | Necesita futuros perpetuos y cortos; no existe en Alpaca. |
| 16. ORB | Intradía; fuera de "baja frecuencia". |
| 17. VWAP | Intradía; herramienta de ejecución, no ventaja. |
| 18. Grid trading | Sin stop claro, acumula en caídas; alta frecuencia. |
| 19. Scalping | Alta frecuencia; evidencia en contra para particulares. |
| 20. Covered calls / Wheel | Opciones. Prohibido en esta fase. |
| 21. Copy trading | No es una regla propia ni backtesteable. |

Se quedan: **5 (Donchian)** → H1 y H4, **6 (momentum de series temporales, con 4 y 8 dentro)** → H2, **10 (RSI(2))** → H3. El informe no recomendaba RSI(2) esta semana por evidencia floja; se incluye igualmente porque el prompt pide candidatas **diversas** y es la única de reversión que es 100 % mecánica y de velas diarias. Entra con esa advertencia y con el mismo listón que las demás.

## 2. Candidatas

### Reglas comunes a todas (pre-registradas)

- **Ejecución:** la señal se calcula con la vela cerrada en `t` y se ejecuta en la **apertura de `t+1`**. ETFs: orden a mercado en la apertura de la sesión siguiente. Cripto: velas diarias que cierran a las 00:00 UTC; ejecución a las ~00:15 UTC.
- **Stop:** siempre fijado en la vela de señal, antes de entrar: `stop = cierre_t − k × ATR(20)_t`. Es **fijo** (no se mueve). Si la apertura de `t+1` ya está en el stop o por debajo, **no se entra**.
- **ATR:** `TR_t = max(máx_t − mín_t, |máx_t − cierre_{t−1}|, |mín_t − cierre_{t−1}|)`; `ATR(n)` = media de Wilder de TR (`ewm(alpha=1/n, adjust=False, min_periods=n)`, la de `tlab.indicators.atr`). `atr_n = 20` en todas (no se varía).
- **Tamaño (sizing):** `cantidad = floor( f × equity / riesgo_por_unidad )`, con `riesgo_por_unidad = (entrada con slippage − stop con slippage) + comisiones de entrada y salida` (`risk.position_size`). `f` = fracción de riesgo, **1 % como máximo** (ver calibración en §3). ETFs: **acciones enteras** (redondeo hacia abajo). Cripto: fracciones de 0,000001.
- **Tope por posición (regla nueva, pre-registrada):** el coste de una posición nunca supera **equity / 3**. Con 3 posiciones como máximo, esto garantiza por construcción exposición ≤ 100 % y evita que un ETF de poca volatilidad (bonos) se coma toda la caja. Si el tope recorta la cantidad, el riesgo real queda por debajo de `f`.
- **Si la cantidad sale 0** (una sola acción ya arriesga más que `f × equity`, o no hay caja): **no se opera** y se anota.
- **Máximo 3 posiciones** abiertas. Si hay más señales que huecos libres, se ordenan por `rank` (de mayor a menor) y, a igualdad, por símbolo alfabético.
- **Datos:** cierres **ajustados** por splits y dividendos. El efectivo no rinde nada (pesimista para la estrategia frente al benchmark).
- **Sin parámetros distintos por activo.** Los mismos números para todo el universo de cada candidata.

---

### H1 — `donchian_crypto`
- **Idea en una frase:** comprar una cripto cuando cierra por encima de su máximo de 55 días y venderla cuando cierra por debajo de su mínimo de 20 días (seguimiento de tendencia).
- **Razón económica / evidencia:** las tendencias persisten porque la información se incorpora despacio y porque muchos inversores compran lo que ya sube (comportamiento de rebaño); en cripto hay además mucho particular apalancado. Quien paga es el que vende pronto en las subidas y aguanta en las caídas. Evidencia: Hurst, Ooi y Pedersen (2017) para tendencia en muchos mercados durante un siglo; Liu y Tsyvinski (2021) documentan momentum en las criptos principales (a horizontes de 1–2 semanas, más cortos que el nuestro: es respaldo parcial, no de esta regla exacta). Las reglas Turtle son texto de practicantes, no un paper.
- **Universo y timeframe:** `BTC/USD`, `ETH/USD`, `LTC/USD`, `BCH/USD`. Velas **diarias** (corte 00:00 UTC). Criterio de elección para limitar el sesgo de supervivencia: monedas que ya eran de las mayores por capitalización a principios de 2018 (dato de memoria, conocimiento propio) y que hoy tienen par USD en Alpaca con datos desde 2021. Se excluyen a propósito las ganadoras posteriores (SOL, etc.): elegirlas hoy sería hacer trampa. LTC y BCH han ido relativamente mal desde entonces, lo que juega en contra de la estrategia, no a favor.
- **Datos (fuente, desde, ajustes):** yfinance (`BTC-USD` y `LTC-USD` desde 2014-09; `ETH-USD` y `BCH-USD` desde ~2017-11, **fechas a verificar por Sonnet**). Alpaca desde 2021-01 para contrastar. Cada activo entra en el universo cuando tiene **≥ 365 velas** de historia. Simulación desde **2015-10-01**.
- **Indicadores (fórmulas):**
  - `canal_alto_t = max(máx_{t−55} … máx_{t−1})` (excluye la vela actual).
  - `canal_bajo_t = min(mín_{t−20} … mín_{t−1})`.
  - `ATR(20)_t`.
- **Entrada:** `cierre_t > canal_alto_t` y ATR disponible → comprar en la apertura de `t+1`.
- **Salida:** `cierre_t < canal_bajo_t` → vender en la apertura de `t+1`. O antes si salta el stop.
- **Stop (fórmula exacta):** `stop = cierre_t − 2,0 × ATR(20)_t` (vela de señal). Fijo.
- **Ranking si hay > 3 señales:** `rank = (cierre_t − canal_alto_t) / ATR(20)_t` (cuánto ha roto, medido en ATRs), mayor primero.
- **Parámetros por defecto | rango robustez:** `entry_n = 55` | {41, 55, 69} · `exit_n = 20` | {15, 20, 25} · `atr_mult = 2,0` | {1,5, 2,0, 2,5} · `atr_n = 20` fijo. Rejilla: 3×3×3 = 27 combinaciones.
- **Ejemplo numérico de sizing (equity 10.000 $, precios inventados):** BTC a 100.000 $, ATR(20) = 3.500 $. Stop = 100.000 − 7.000 = 93.000 $. Con costes cripto (slippage 20 pb, comisión 0,25 % por lado): entrada 100.200; salida en stop 92.814; comisiones 250,50 + 232,04. Riesgo por unidad = 7.386 + 482,54 = **7.868,54 $**. Cantidad = 100 / 7.868,54 = **0,012708 BTC** (≈ 1.273 $, el 12,7 % del equity). Tope por posición (3.333 $): no se alcanza. Tres posiciones parecidas ≈ 38 % de exposición ≤ 100 %. Riesgo = 99,99 $ ≤ 100 $ ✔.
- **Nº de operaciones esperado (estimación, no medido):** una ruptura de 55 días con salida de 20 días da del orden de 3–5 operaciones por activo y año. Años-activo ≈ 11 (BTC) + 11 (LTC) + 8 (ETH) + 8 (BCH) ≈ 38 → ~110–190 señales; como las criptos rompen a la vez y solo hay 3 huecos, espero **~90–140 operaciones**, de las cuales **~30–45 en OOS**. Puede quedarse por debajo de 100: ver justificación en §4.
- **Benchmark:** comprar y mantener **BTC** (principal, el del criterio). Informativo: 50 % BTC / 50 % caja con rebalanceo mensual.
- **Riesgos conocidos / cuándo dejaría de funcionar:** mercados laterales con rupturas falsas (rachas largas de pérdidas pequeñas); huecos de fin de semana más grandes que el stop; costes altos (≈ 0,9 % ida y vuelta); las 4 monedas se mueven casi juntas, así que 3 posiciones son en la práctica una sola apuesta de 3 % de riesgo; el resultado suele depender de 3–4 operaciones enormes (por eso existe el criterio "quitando las 5 mejores"); pocas operaciones en OOS → veredicto con mucha incertidumbre. En vivo, Alpaca solo admite `stop_limit` en cripto: el stop puede no ejecutarse en un hueco (a resolver en el paso 5).

---

### H2 — `tsmom_etf`
- **Idea en una frase:** una vez al mes, estar comprado en los ETFs (de clases de activo distintas) que han subido en los últimos 12 meses y fuera de los que han bajado; como máximo los 3 más fuertes.
- **Razón económica / evidencia:** momentum de series temporales: Moskowitz, Ooi y Pedersen (2012) lo documentan en 58 futuros; Faber (2007) con la media de 10 meses; Hurst, Ooi y Pedersen (2017). Explicación habitual: reacción lenta a la información y coberturas que obligan a vender en caídas. Lo que se "cobra" es evitar parte de las grandes caídas a cambio de perder en mercados laterales. Ojo: los papers usan muchos futuros, con cortos y sin stops; esto es una versión reducida, solo larga y con stop.
- **Universo y timeframe:** 7 ETFs, uno por clase de activo: `SPY` (bolsa EE. UU.), `EFA` (bolsa desarrollada ex-EE. UU.), `EEM` (emergentes), `IEF` (bonos del Tesoro 7–10 años), `GLD` (oro), `DBC` (materias primas), `VNQ` (inmobiliario). Son las 5 clases de Faber más emergentes y oro; todos existían en 2006. Velas diarias, **decisión mensual**.
- **Datos (fuente, desde, ajustes):** yfinance ajustado (el más joven, DBC, desde 2006-02). Alpaca (`adjustment="all"`) desde 2016 para contrastar. Simulación desde **2007-07-01**.
- **Indicadores (fórmulas):**
  - `mom_t = cierre_t / cierre_{t−252} − 1` (rentabilidad de 252 sesiones ≈ 12 meses, con cierres ajustados).
  - `día_de_revisión_t` = la vela `t` es la **primera sesión del mes** (su mes es distinto al de la vela anterior del mismo activo). Se usa la primera sesión y no la última porque así se sabe con datos ≤ t, sin calendario.
  - `ATR(20)_t`.
- **Entrada:** `día_de_revisión_t` y `mom_t > 0` → comprar en la apertura de `t+1` (si hay hueco).
- **Salida:** `día_de_revisión_t` y `mom_t ≤ 0` → vender en la apertura de `t+1`. O antes si salta el stop. Una posición **no** se vende por dejar de estar entre las 3 más fuertes (menos rotación, menos costes). Si salta el stop, se puede volver a entrar en la siguiente revisión mensual si `mom > 0`.
- **Stop (fórmula exacta):** `stop = cierre_t − 4,0 × ATR(20)_t`. Fijo. Es un **stop de catástrofe**: 4 ATR diarios equivalen aproximadamente a una desviación típica mensual, para que el ruido normal de un mes no saque la posición.
- **Ranking si hay > 3 señales:** `rank = mom_t`, mayor primero (esto es la parte "momentum relativo" del dual momentum).
- **Parámetros por defecto | rango robustez:** `lookback = 252` | {189, 252, 315} · `atr_mult = 4,0` | {3,0, 4,0, 5,0} · `atr_n = 20` fijo. Rejilla: 3×3 = 9 combinaciones.
- **Ejemplo numérico de sizing (equity 10.000 $, precios inventados, costes ETF 5 pb):**
  - SPY a 600 $, ATR 6 $ → stop 576. Riesgo por unidad = 600,30 − 575,71 = 24,59 $. Cantidad = floor(100 / 24,59) = **4 acciones** (2.401 $; riesgo 98,35 $).
  - IEF a 95 $, ATR 0,45 $ → stop 93,20. Riesgo por unidad 1,894 $ → 52 acciones (4.942 $) → **el tope de 3.333 $ lo recorta a 35 acciones** (3.327 $; riesgo 66,29 $).
  - GLD a 380 $, ATR 4,20 $ → stop 363,20. Riesgo por unidad 17,17 $ → **5 acciones** (1.901 $; riesgo 85,86 $).
  - Total: 3 posiciones, 7.629 $ = **76 % de exposición** ≤ 100 % ✔; cada riesgo ≤ 100 $ ✔.
- **Nº de operaciones esperado (estimación, no medido):** la señal de 12 meses cambia de signo menos de una vez al año por activo; sumando salidas por stop y reentradas, y con solo 3 huecos, espero **~80–150 operaciones** en 19 años y **~25–45 en OOS**. Es la candidata con más riesgo de no llegar a 100: ver §4.
- **Benchmark:** comprar y mantener **SPY** (principal). Informativo: 60 % SPY / 40 % IEF con rebalanceo mensual.
- **Riesgos conocidos / cuándo dejaría de funcionar:** la señal llega tarde (caídas rápidas tipo 2020 y rebotes en V); mercados laterales; el stop convierte la regla en algo distinto de lo publicado (puede sacar justo antes de que la tendencia siga); con 3 huecos y 7 activos se pierde diversificación; poca exposición media → menos rentabilidad que SPY en mercados alcistas.

---

### H3 — `rsi2_etf`
- **Idea en una frase:** en un índice que está en tendencia alcista de fondo, comprar tras una caída brusca de 2–3 días y vender en el primer rebote (reversión a la media a muy corto plazo).
- **Razón económica / evidencia:** quien compra en una venta precipitada está dando liquidez a quien necesita vender ya, y cobra por ello; esa compensación crece cuando hay miedo. Conocimiento propio (no está en el informe): la reversión a corto plazo está documentada en acciones por Jegadeesh (1990) y Lehmann (1990), y Nagel (2012) la interpreta como pago por dar liquidez. **Pero** esa evidencia es sobre acciones individuales con cortos, no sobre esta regla en ETFs de índices. La regla concreta viene de los libros de Larry Connors; el informe califica su evidencia de **insuficiente** y frágil tras costes. Es la candidata con peor respaldo y se prueba precisamente para comprobarlo con costes y stop.
- **Universo y timeframe:** `SPY`, `QQQ`, `IWM`, `DIA`, `EFA`, `EEM` (6 ETFs de índices de bolsa, muy líquidos). Velas **diarias**, revisión diaria.
- **Datos (fuente, desde, ajustes):** yfinance ajustado (todos existen desde ≤ 2003). Alpaca desde 2016 para contrastar. Simulación desde **2007-07-01**.
- **Indicadores (fórmulas):**
  - `SMA(n)_t` = media simple de los últimos n cierres (incluido `t`).
  - `RSI(2)_t` de Wilder: `d_t = cierre_t − cierre_{t−1}`; `sube = Wilder(max(d,0), 2)`; `baja = Wilder(max(−d,0), 2)`; `RSI = 100 − 100 / (1 + sube/baja)` (la de `tlab.indicators.rsi`).
  - `ATR(20)_t`.
- **Entrada:** `cierre_t > SMA(200)_t` **y** `RSI(2)_t < 10` → comprar en la apertura de `t+1`.
- **Salida:** `cierre_t > SMA(5)_t` → vender en la apertura de `t+1`. O antes si salta el stop.
- **Stop (fórmula exacta):** `stop = cierre_t − 3,0 × ATR(20)_t`. Fijo. (La receta original no lleva stop; aquí es obligatorio.)
- **Ranking si hay > 3 señales:** `rank = −RSI(2)_t` (el más sobrevendido primero).
- **Parámetros por defecto | rango robustez:** `rsi_entry = 10` | {7,5, 10, 12,5} · `exit_sma_n = 5` | {4, 5, 6} · `atr_mult = 3,0` | {2,25, 3,0, 3,75} · fijos: `rsi_n = 2`, `trend_n = 200`, `atr_n = 20`. Rejilla: 27 combinaciones, más 2 pruebas sueltas de `trend_n` ∈ {150, 250} con el resto por defecto.
- **Ejemplo numérico de sizing (equity 10.000 $, precios inventados):** QQQ a 500 $, ATR 7 $ → stop 479. Riesgo por unidad = 500,25 − 478,76 = 21,49 $. Cantidad = floor(100 / 21,49) = **4 acciones** (2.001 $; riesgo 85,96 $). Tres posiciones así ≈ 60 % de exposición; por el tope de equity/3 nunca pasan del 100 % ✔.
- **Nº de operaciones esperado (estimación, no medido):** RSI(2) < 10 con tendencia alcista ocurre del orden de 8–12 veces al año por índice, pero los 6 caen el mismo día y solo hay 3 huecos: espero **~25–35 operaciones al año**, es decir **~450–650 en total** y **~150–200 en OOS**. Es la candidata con más muestra.
- **Benchmark:** comprar y mantener **SPY** (principal). Informativo: 60/40.
- **Riesgos conocidos / cuándo dejaría de funcionar:** gana poco muchas veces y pierde mucho de golpe ("coger un cuchillo que cae": inicio de un desplome); margen por operación estrecho, muy sensible a costes y al retraso (entramos en la apertura siguiente, no en el cierre como la receta original, y parte del rebote ya ha pasado); el stop corta operaciones que luego rebotarían; los 6 índices están muy correlacionados (3 posiciones = una sola apuesta); es una regla muy conocida y puede estar agotada.

---

### H4 — `donchian_etf`
- **Idea en una frase:** la misma ruptura 55/20 de H1, aplicada a ETFs de clases de activo distintas.
- **Razón económica / evidencia:** la de H1 y H2 (Hurst, Ooi y Pedersen, 2017: la tendencia funciona sobre todo **diversificando entre mercados distintos**). Usar exactamente las mismas reglas y parámetros que H1 en otro mercado es, en sí mismo, una prueba de robustez.
- **Universo y timeframe:** los mismos 7 ETFs de H2 (`SPY`, `EFA`, `EEM`, `IEF`, `GLD`, `DBC`, `VNQ`). Velas diarias, revisión diaria.
- **Datos (fuente, desde, ajustes):** como H2. Simulación desde **2007-07-01**.
- **Indicadores, entrada, salida, stop, ranking:** idénticos a H1 (`cierre_t > canal_alto(55)`; salida `cierre_t < canal_bajo(20)`; `stop = cierre_t − 2,0 × ATR(20)_t`; `rank = (cierre − canal_alto)/ATR`).
- **Parámetros por defecto | rango robustez:** los de H1: `entry_n = 55` | {41, 55, 69} · `exit_n = 20` | {15, 20, 25} · `atr_mult = 2,0` | {1,5, 2,0, 2,5}. 27 combinaciones.
- **Ejemplo numérico de sizing (equity 10.000 $, precios inventados):** SPY a 600 $, ATR 6 $ → stop 588. Riesgo por unidad = 600,30 − 587,71 = 12,59 $ → 7 acciones (4.202 $) → **el tope de 3.333 $ lo deja en 5 acciones** (3.002 $; riesgo 62,97 $ = 0,63 %). Con stops de 2 ATR en ETFs tranquilos el tope manda casi siempre: 3 posiciones ≈ 90–100 % de exposición, nunca más ✔.
- **Nº de operaciones esperado (estimación, no medido):** ~3 por activo y año → ~400 señales en 19 años; con 3 huecos, **~200–280 operaciones** y **~60–85 en OOS**.
- **Benchmark:** comprar y mantener **SPY** (principal). Informativo: 60/40.
- **Riesgos conocidos / cuándo dejaría de funcionar:** rupturas falsas en mercados laterales; en ETFs las tendencias son más suaves que en futuros o cripto y el beneficio por operación puede no cubrir costes; **misma familia que H2** (tendencia en los mismos ETFs): como mucho **una de las dos** puede acabar en la cartera final (§5).

## 3. Diseño de validación

Todo se mide con el simulador de cartera propio (`portfolio_sim`), con costes, sobre 10.000 $ iniciales. vectorbt solo para rejillas rápidas.

- **Fechas in-sample / OOS** (fin de datos común: **2026-10-31**, último mes completo):

  | Candidatas | Inicio | In-sample (≈ 70 %) | OOS (≈ 30 %) |
  |---|---|---|---|
  | H2, H3, H4 (ETFs) | 2007-07-01 | 2007-07-01 → **2020-12-31** | **2021-01-01 → 2026-10-31** |
  | H1 (cripto) | 2015-10-01 | 2015-10-01 → **2023-06-30** | **2023-07-01 → 2026-10-31** |

  Los indicadores se "calientan" con datos anteriores al inicio. El OOS **se ejecuta una sola vez por candidata**, con los parámetros por defecto y la fracción de riesgo ya fijada en IS, y solo si la candidata ha pasado antes todos los criterios que se pueden medir en IS.

- **Walk-forward** (optimizar en un tramo y probar en el siguiente, avanzando), **solo dentro del IS**:
  - ETFs: entrenamiento inicial 2007-07-01 → 2012-12-31, que va creciendo; **8 ventanas de prueba** de un año natural (2013, 2014, …, 2020).
  - Cripto: entrenamiento inicial 2015-10-01 → 2018-12-31, creciente; **6 ventanas de prueba** de 9 meses (2019-01-01 → 2019-09-30, …, 2022-10-01 → 2023-06-30).
  - En cada paso se elige, de la rejilla ±25 % de la candidata, la combinación con mayor Sharpe en el entrenamiento (empate → la más cercana a la de por defecto) y se aplica a la ventana de prueba, que arranca sin posiciones y con 10.000 $.
  - Una ventana es "positiva" si su resultado neto es > 0. Una ventana sin ninguna operación no cuenta (ni a favor ni en contra), pero hacen falta **≥ 5 ventanas válidas**.

- **Presupuesto de variantes:** máximo **40 combinaciones de parámetros por candidata** (rejilla + pruebas sueltas + niveles de riesgo), 160 en total. No se permiten barridos adicionales con `param_sweep.py` sobre las candidatas fuera de ese presupuesto. **Todas** se anotan en `docs/registro_pruebas.md`, salgan bien o mal. Las pruebas de estrés de la configuración por defecto (costes × 2, retraso, quitar las 5 mejores, Monte Carlo, contra el azar) no son variantes pero también se anotan. Intentos previos heredados: 330 (familia Donchian) y 72 (familia TSMOM).

- **Costes base y de estrés** (por lado):

  | Clase | Comisión | Slippage base | Estrés |
  |---|---|---|---|
  | ETFs (todos los del universo) | 0 $ | 5 pb | × 2 |
  | Cripto | 0,25 % | **20 pb** (subido desde 10 pb) | × 2 |

  Motivo del cambio en cripto: LTC y BCH tienen menos liquidez en Alpaca que BTC/ETH y el motor solo admite un coste por clase de activo; se aplica el pesimista a todas. Endurece, no suaviza.

- **Kill switch en el backtest (respuesta a la pregunta 1 de PREP_NOTES):** se pre-registran **los dos números**.
  1. Las **métricas de aprobado** se miden con el kill switch **desactivado**. Si no, la simulación se para en el primer bache y no hay nada que medir.
  2. Aparte se informa de **cuántas veces habría saltado** (episodios de caída > 10 % desde el máximo, reiniciando el máximo tras cada episodio) en IS y en OOS, y la fecha del primero con la regla literal.
  3. **Calibración del riesgo, solo con IS:** se usa la mayor fracción de riesgo `f` ∈ {1,0 %, 0,75 %, 0,5 %} con la que el drawdown máximo en IS (sin kill switch) es **≤ 10 %**. Si ni con 0,5 % se cumple, **la candidata muere en IS** y no gasta su OOS. Esa `f` queda congelada para el OOS y para el paper.
  4. En el OOS se exige que el kill switch **no salte** (criterio 12).

  Razón: con la regla dura 6 tal como está (parada permanente hasta que Jorge borre el archivo), una estrategia que la dispara no se puede operar. **PENDIENTE DE JORGE (P1).**

- **Motor de datos:** antes de cualquier resultado, contrastar yfinance contra Alpaca en el tramo común (ETFs 2016+, cripto 2021+): las rentabilidades diarias deben coincidir con una tolerancia que fije Sonnet y documente; si no cuadran, se para y se investiga.

## 4. Criterios de aceptación (checklist)

Una candidata **aprueba solo si todas las casillas son "sí"**. Salvo que se diga otra cosa: costes base, parámetros por defecto, fracción de riesgo calibrada, kill switch desactivado, simulador de cartera.

Mínimos del prompt (sin suavizar):
- [ ] **1. Muestra:** ≥ 100 operaciones cerradas en total (IS + OOS, todo el universo); o, si no llega, ≥ 30 en OOS. *Justificación escrita ahora para la segunda vía (aplica a H1 y H2):* son reglas de tendencia de baja frecuencia a propósito; pocas operaciones largas es su naturaleza, y forzar más operaciones obligaría a cambiar la regla. A cambio, con < 100 operaciones el veredicto se etiqueta **"aprobado con muestra pequeña"** y exige el doble de tiempo en paper antes de cualquier conclusión. Con < 30 en OOS: no aprueba.
- [ ] **2. Expectancy OOS > 0,10 R.**
- [ ] **3. Sharpe OOS ≥ 0,5** **y** al menos una de: (a) Sharpe OOS ≥ el del benchmark principal en el mismo periodo; (b) drawdown máximo OOS ≤ 60 % del del benchmark **y** CAGR (crecimiento anual compuesto) OOS ≥ 50 % del del benchmark.
- [ ] **4. Drawdown máximo** de la cartera ≤ **20 %** (ETFs) / ≤ **30 %** (cripto) en todo el periodo (IS + OOS).
- [ ] **5. Walk-forward:** ≥ 60 % de las ventanas de prueba válidas son positivas (≥ 5 de 8 en ETFs; ≥ 4 de 6 en cripto).
- [ ] **6. Robustez de parámetros (IS):** en la rejilla ±25 %, ≥ 70 % de las combinaciones vecinas tienen expectancy > 0 **y** Sharpe ≥ 50 % del de la combinación por defecto.
- [ ] **7. Costes × 2:** expectancy > 0 (en IS y en OOS).
- [ ] **8. Retraso de 1 vela** en la entrada: expectancy > 0 (en IS y en OOS).
- [ ] **9. Quitando las 5 mejores operaciones** de todo el periodo: el resultado total sigue ≥ 0.
- [ ] **10. Monte Carlo** (barajar el orden de las operaciones 1.000 veces, semilla 42): el percentil 95 del drawdown ≤ 1,5 × el límite (≤ 30 % ETFs / ≤ 45 % cripto).
- [ ] **11. Estabilidad:** expectancy > 0 en **≥ 2 de 3 subperiodos** (operaciones asignadas por fecha de entrada) y en **≥ 2 activos** con al menos 10 operaciones cada uno.
  - ETFs: 2007-07-01 → 2013-12-31 · 2014-01-01 → 2020-06-30 · 2020-07-01 → 2026-10-31.
  - Cripto: 2015-10-01 → 2019-06-30 · 2019-07-01 → 2023-02-28 · 2023-03-01 → 2026-10-31.

Endurecimientos añadidos en este pre-registro:
- [ ] **12. Compatible con el kill switch:** con la regla literal (−10 % desde el máximo, arrancando al inicio del OOS), el kill switch **no salta** en el OOS. (Y en IS el drawdown ≤ 10 % ya lo garantiza la calibración de §3.)
- [ ] **13. No depende de un solo activo:** quitando **todas** las operaciones del activo que más ha ganado, el resultado total del periodo completo sigue ≥ 0. (Respuesta a la duda sobre el peso de BTC.)
- [ ] **14. Mejor que el azar (IS):** frente a 1.000 estrategias que entran al azar con las mismas reglas de salida, stop, tamaño y costes (`random_benchmark.py`, semilla 42), p-valor < 0,05 en Sharpe.

Reglas finales:
- Los criterios 5, 6 y 14, la calibración de riesgo y la parte IS de 7 y 8 se evalúan **antes** de tocar el OOS. Si alguno falla, la candidata muere sin gastar su OOS.
- Si una candidata **falla en OOS, muere**. No se reajusta ni se vuelve a probar en el mismo OOS.
- Sobre el CAGR y la poca exposición (pregunta 3 de PREP_NOTES): **no se suaviza nada**. El criterio 3 ya tiene una vía que no depende de la exposición (el Sharpe no cambia si inviertes poco o mucho). El informe del paso 3 debe dar además, solo como información, la exposición media y la rentabilidad sobre el capital realmente invertido.
- Se informa también (sin ser criterio) de DSR y PBO (dos medidas del riesgo de haber elegido por suerte) contando los intentos heredados.
- Aprobar aquí **no** autoriza dinero real. Autoriza pasar a paper.

## 5. Criterio de selección final

1. Solo entre las que pasen **todo** el §4.
2. Si pasan varias, preferir en este orden: (a) la de **menos parámetros** (H2: 2; H1/H4: 3; H3: 3 + filtros fijos); (b) la de mayor porcentaje en el criterio 6 (robustez); (c) la de más operaciones en OOS.
3. Como máximo **2** estrategias en la cartera final, y solo si la correlación de sus rentabilidades diarias (periodo común completo) es **< 0,5**. H2 y H4 no pueden ir juntas (misma familia y universo).
4. **Reparto de huecos si van dos** (respuesta a la duda sobre el peso de BTC; **PENDIENTE DE JORGE, P3**): el total sigue siendo 3. Si una de las dos es H1 (cripto), cripto ocupa **como máximo 1 hueco** y la otra hasta 2. Todas las posiciones se dimensionan igual (misma `f`, la menor de las dos calibradas); BTC no recibe ningún peso extra.
5. La cartera combinada se simula una vez (IS y OOS, sin cambiar ningún parámetro) y debe cumplir también los criterios 4 y 12. Si no los cumple, se opera solo la estrategia preferida según el punto 2.
6. Si no pasa ninguna: el veredicto es "ninguna aprobada" y **no se opera**. Es un resultado válido, no un fracaso del proceso. No se proponen candidatas nuevas sobre el mismo OOS sin un pre-registro nuevo que lo declare.

### Decisiones tomadas por prudencia — PENDIENTE DE JORGE

Jorge puede cambiarlas, pero **solo antes de que se ejecute el primer OOS**, anotando el cambio con fecha en una sección "Enmiendas" al final de este archivo. Después, ya no.

| # | Decisión | Opción tomada (la más prudente) | Alternativa |
|---|---|---|---|
| **P1** | Kill switch en el backtest | Métricas sin kill switch + recuento de saltos; riesgo calibrado en IS para DD ≤ 10 %; exigir que no salte en OOS. La regla dura 6 no se toca. | Aceptar algún salto (p. ej. ≤ 1 cada 10 años) o hacerlo rearmable tras una pausa. Eso es cambiar una regla dura de `CLAUDE.md`: solo Jorge. |
| **P2** | Estrategias mensuales frente a "stop + 1 %" | Opción (a) de PREP_NOTES: H2 lleva stop de catástrofe de 4 × ATR(20) y tamaño al 1 % de riesgo, con tope de equity/3. Las reglas duras no se tocan. Faber y dual momentum no se prueban aparte (quedan dentro de H2). | (b) tamaño por volatilidad sin stop, o (c) excepción a la regla para mensuales. Ambas cambian reglas duras. |
| **P3** | Peso de BTC / cripto | Mismo riesgo por operación que cualquier otro activo; tope de equity/3 por posición; criterio 13 (aprobar sin el mejor activo); cripto ≤ 1 hueco si se combina con ETFs. | Dar a cripto hasta 2 o 3 huecos, o un peso fijo a BTC. |
| **P4** | Universo cripto | BTC, ETH, LTC, BCH (grandes ya en 2018; sin SOL ni ganadoras recientes). | Solo BTC y ETH (más limpio, pero con muy pocas operaciones: H1 difícilmente llegaría a 30 en OOS). |
| **P5** | Acciones enteras | Sin fracciones en ETFs. | Usar fracciones de Alpaca (habría que verificar qué tipos de orden stop admiten). |
| **P6** | Rama `prep/motor-backtest` | No se ha fusionado: lo decide Jorge. El paso 2 la necesita (o rehacer el motor). El motor **no está auditado** todavía (auditoría en el paso 3, fase A). | — |

## 6. Especificación para implementar (para Sonnet)

Interfaz del repo (rama `prep/motor-backtest`): función **pura** por activo
`generate_signals(bars: pd.DataFrame, params: dict) -> pd.DataFrame`, donde `bars` es el OHLCV de **un** activo (columnas `open, high, low, close, volume`, índice `DatetimeIndex` UTC) y la salida tiene el mismo índice y columnas `entry` (bool), `exit` (bool), `stop_price` (float), `rank` (float). Partir de `empty_signals(bars.index)`. Sin E/S, sin red, sin aleatoriedad, sin datos > t. Registrar cada id en `SIGNAL_STRATEGIES` (así entran solas en `tests/test_lookahead.py`).

En los casos a mano, salvo que se indique, las velas se dan como `(open, high, low, close)` y se usa `atr_n = 1` para que `ATR = TR` de la propia vela y el resultado no dependa de cómo se inicializa la media.

### 6.1 `donchian_crypto` y `donchian_etf` (H1, H4)
- Mismo módulo (se puede reutilizar `donchian_atr.generate_signals` tal cual), dos TOML distintos.
- `params`: `entry_n=55, exit_n=20, atr_mult=2.0, atr_n=20`. `robust_keys = ["entry_n", "exit_n", "atr_mult"]` con los valores de §2.
- `entry = (close > donchian_high(bars, entry_n)) & atr.notna()` · `exit = close < donchian_low(bars, exit_n)` · `stop_price = close − atr_mult × ATR(atr_n)` · `rank = (close − donchian_high) / ATR`.
- TOML H1: `universe = ["BTC/USD","ETH/USD","LTC/USD","BCH/USD"]`, `benchmark = "BTC/USD"`, `start = "2015-10-01"`, `is_end = "2023-06-30"`, `end = "2026-10-31"`.
- TOML H4: `universe = ["SPY","EFA","EEM","IEF","GLD","DBC","VNQ"]`, `benchmark = "SPY"`, `start = "2007-07-01"`, `is_end = "2020-12-31"`, `end = "2026-10-31"`.

Casos a mano (`entry_n=3, exit_n=2, atr_mult=2, atr_n=1`):

| t | open | high | low | close |
|---|---|---|---|---|
| 0 | 10 | 11 | 9 | 10 |
| 1 | 10 | 12 | 9 | 11 |
| 2 | 11 | 12 | 10 | 11 |
| 3 | 11 | 14 | 11 | 13 |
| 4 | 13 | 13 | 11 | 12 |
| 5 | 12 | 12 | 8 | 9 |

- **Caso D1:** `entry = [F, F, F, T, F, F]` (en t=3 el canal alto es max(11,12,12)=12 y 13 > 12). `exit = [F, F, F, F, F, T]` (en t=5 el canal bajo es min(11,11)=11 y 9 < 11). En t=3: TR = 3 → `stop_price = 13 − 2×3 = 7,0`; `rank = (13−12)/3 ≈ 0,3333`.
- **Caso D2 (igualar no es romper):** misma tabla pero con `close = 12` en t=3 → `entry` es `False` en todas las velas.
- **Caso D3 (sin mirar al futuro):** calcular las señales solo con las velas 0–3 debe dar en t=3 exactamente la misma fila que con las velas 0–5.

### 6.2 `tsmom_etf` (H2)
- `params`: `lookback=252, atr_mult=4.0, atr_n=20`. `robust_keys = ["lookback", "atr_mult"]`.
- `mom = close / close.shift(lookback) − 1`.
- `revision` = `True` en la vela cuyo mes (año-mes del índice) es distinto del de la vela anterior; la primera vela de los datos es `False`.
- `entry = revision & (mom > 0) & atr.notna()` · `exit = revision & (mom <= 0)` · `stop_price = close − atr_mult × ATR` · `rank = mom`. Si `mom` es NaN: ni `entry` ni `exit`.
- TOML: `universe = ["SPY","EFA","EEM","IEF","GLD","DBC","VNQ"]`, `benchmark = "SPY"`, fechas como H4.

Casos a mano (`lookback=3, atr_mult=4, atr_n=1`), fechas 2024-01-29, 01-30, 01-31, **02-01**, 02-02, 02-05:

- **Caso T1:** cierres `100, 101, 102, 104, 105, 106`; la vela del 02-01 es `(102, 105, 102, 104)`. El 02-01 es día de revisión; `mom = 104/100 − 1 = 0,04 > 0` → `entry = True` solo ese día; `exit` todo `False`; TR = 3 → `stop_price = 104 − 4×3 = 92`; `rank = 0,04`. El 02-02 y el 02-05 tienen `mom > 0` pero no son día de revisión → `entry = False`.
- **Caso T2:** cierres `100, 99, 98, 97, 96, 95` → el 02-01 `mom = −0,03` → `exit = True` solo ese día; `entry` todo `False`.
- **Caso T3 (cero no es positivo):** cierres `100, 101, 102, 100, 101, 102` → el 02-01 `mom = 0` → `exit = True`, `entry = False`.

### 6.3 `rsi2_etf` (H3)
- `params`: `rsi_n=2, rsi_entry=10.0, trend_n=200, exit_sma_n=5, atr_mult=3.0, atr_n=20`. `robust_keys = ["rsi_entry", "exit_sma_n", "atr_mult"]`.
- `entry = (close > sma(close, trend_n)) & (rsi(close, rsi_n) < rsi_entry) & atr.notna()` · `exit = close > sma(close, exit_sma_n)` · `stop_price = close − atr_mult × ATR` · `rank = −rsi(close, rsi_n)`.
- TOML: `universe = ["SPY","QQQ","IWM","DIA","EFA","EEM"]`, `benchmark = "SPY"`, fechas como H4.

Casos a mano (`rsi_n=2, rsi_entry=10, trend_n=20, exit_sma_n=2, atr_mult=3, atr_n=1`). Velas construidas así: `open` = cierre anterior (en t=0, `open = close`), `high = max(open, close)`, `low = min(open, close)`.

- **Caso R1:** cierres `100, 101, …, 125` (t=0…25, +1 cada día), luego `121` (t=26), `117` (t=27), `120` (t=28).
  - t=26: RSI(2) = 20 → no hay entrada. t=27: `sube = 0,25`, `baja = 3` → RSI(2) = 100×0,25/3,25 ≈ **7,69 < 10**; SMA(20) = 116,75 y 117 > 116,75 → `entry = True` **solo en t=27**. TR = 4 → `stop_price = 117 − 3×4 = 105`; `rank ≈ −7,69`.
  - `exit`: `True` en t=1…25 y en t=28 (120 > 118,5); `False` en t=0, t=26 (121 < 123) y t=27 (117 < 119).
- **Caso R2 (falla el filtro de tendencia):** igual, pero t=27 cierra en `113` → RSI(2) ≈ 4,76 < 10, pero SMA(20) = 116,55 y 113 < 116,55 → `entry = False` en todas las velas.
- **Caso R3 (extremos):** una serie siempre creciente da RSI = 100 y nunca `entry`; comprobar que no salen NaN convertidos en `True`.

### 6.4 Cambios de infraestructura necesarios (detalle en `docs/tareas_sonnet.md`)
1. **Tope por posición = equity/3** en `risk.apply_limits` (parámetro `max_position_fraction` en `settings.toml [risk]`, por defecto `0.3333`), con tests:
   - ETF: equity 10.000, apertura 95, stop 93,20, slippage 5 pb → sin tope 52 acciones; **con tope 35**.
   - ETF: equity 10.000, apertura 600, stop 576 → **4 acciones**; con stop 588 → 7 sin tope, **5 con tope**.
   - Cripto: equity 10.000, apertura 100.000, stop 93.000, slippage 20 pb, comisión 0,25 % → **0,012708**.
2. `risk_per_trade` configurable por estrategia (para la calibración 1,0 / 0,75 / 0,5 %).
3. `start`, `is_end`, `end` por estrategia en su TOML, y entrada de cada activo al universo cuando tenga ≥ 365 velas (hoy el `runner` recorta todo al activo más joven).
4. `settings.toml`: `costs.crypto.slippage_bps = 20`; añadir `DBC`, `VNQ`, `DIA`, `LTC/USD`, `BCH/USD` al universo.
5. Walk-forward según §3 (entrenamiento creciente, ventanas con fechas fijas, elección por Sharpe dentro de la rejilla).
6. Recuento de episodios de kill switch (con reinicio del máximo), prueba "quitar las 5 mejores", prueba "quitar el mejor activo", subperiodos con las fechas de §4.
7. Benchmarks: buy & hold SPY y BTC, 60/40 SPY/IEF y 50 % BTC / 50 % caja (rebalanceo mensual), con costes.
8. Contraste yfinance ↔ Alpaca en el tramo común y verificación de las fechas de inicio de `ETH-USD`, `BCH-USD`, `LTC-USD` en yfinance.
9. **Prohibido para Sonnet:** ejecutar `--mode oos` o cualquier cosa sobre fechas OOS de las candidatas. Eso lo hace Fable en el paso 3, una vez.

## Enmiendas

### 2026-11-11 (hora de Madrid) — Fable, paso 3, ANTES de ejecutar ningún backtest de las candidatas
Ningún criterio de §4 cambia. Son aclaraciones de procedimiento a las dudas de
`docs/INFORME_PASO2.md` §5, escritas sin haber visto ningún resultado de las candidatas.

1. **IS ahora:** los backtests in-sample se ejecutan en el paso 3, tras la auditoría (fase A). Confirmado.
2. **"≥ 365 velas"** = 365 velas del propio activo (lectura literal). `DBC` entra el 2007-07-19.
3. **Tope equity/3** = `0.3333 × equity` sobre el coste con slippage y comisión. Confirmado.
4. **Episodios de kill switch:** el máximo se reinicia al equity del día del episodio (lectura literal de §3). Confirmado.
5. **Calibración P1:** DD sobre equity al cierre diario del IS, sin kill switch. Las ejecuciones al 0,75 % y 0,5 % cuentan en el presupuesto de 40. Tras calibrar, `risk_per_trade` del TOML se fija en la `f` elegida y **walk-forward, robustez, azar y OOS se ejecutan con esa `f`**.
6. **Criterios que necesitan el periodo completo (1, 4, 9, 11, 13):** se miden con **una** ejecución `--mode full` posterior al OOS, con los mismos parámetros congelados. No es una segunda mirada para ajustar nada: el aprobado/suspenso del OOS (criterios 2, 3, 12 y la parte OOS de 7 y 8) sale solo de la ejecución `--mode oos` (que arranca con 10.000 $ y sin posiciones el primer día del OOS). Las ejecuciones de estrés en OOS (costes × 2 y retraso) y la `full` quedan anotadas en `reports/oos_log.csv` con el mismo hash de parámetros.
7. **Walk-forward:** se aceptan las convenciones de Sonnet (ventana arranca sin posiciones; lo abierto al final se cierra con costes; positiva = neto > 0; Sharpe NaN = el peor; solo se anota la fila del WF).
8. **Criterio 6:** una vecina sin operaciones cuenta como fallo; vecinas = rejilla menos la central. Confirmado (es la lectura más dura).
9. **Benchmarks:** confirmado.
10. **Criterio 10 (Monte Carlo):** se evalúa sobre las operaciones del IS antes del OOS (filtro) y, si la candidata llega al final, también sobre las del periodo completo; deben cumplirse las dos.
11. **Contraste yfinance ↔ Alpaca:** las tolerancias **no se tocan** y el resultado formal sigue siendo REVISAR en 7 ETFs. Verificado en `reports/datos/verificacion_fable_20261111.md`: las diferencias son días sueltos (sobre todo marzo de 2020, cierres distintos entre proveedores que en buena parte se deshacen al día siguiente), no una deriva del ajuste; quitando los 5 peores días la correlación es ≥ 0,9995 en todos, y las señales de las tres candidatas de ETFs coinciden casi por completo entre fuentes en el tramo IS común. Decisión: **no bloquea**; la fuente sigue siendo yfinance. Queda como riesgo de divergencia backtest ↔ paper.
12. **Corte rápido (prompt 03, fase B.1):** si en IS la expectancy con costes es ≤ 0, la candidata se descarta sin más pruebas. Es un filtro añadido (endurece).
