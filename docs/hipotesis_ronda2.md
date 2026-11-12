# Hipótesis pre-registradas, ronda 2 — 2026-11-11 (hora de Madrid)
Estado: PRE-REGISTRADO (no modificar criterios después de ver resultados)

> Segunda ronda, después de que ninguna de H1–H4 aprobara (`docs/veredicto.md`). Este documento
> fija **qué se va a probar y qué significa "aprobar" antes de ver ningún resultado de las
> candidatas nuevas**. No contiene ninguna cifra de rentabilidad de H5–H7 (no se han probado).
> Los números que aparecen son: supuestos (costes, fechas, parámetros), ejemplos con precios
> inventados, estimaciones marcadas como tales, o cifras de la ronda 1 copiadas de
> `docs/veredicto.md` / `docs/baselines.md` con su origen.
> No es asesoramiento financiero. Solo paper.

Glosario (además del de `docs/hipotesis.md`):
- **Tramo reservado** (*holdout*): datos que no se miran hasta el final y se usan una sola vez. En la ronda 1 se llamaba OOS.
- **Relación rentabilidad/caída**: CAGR (crecimiento anual compuesto) dividido por la caída máxima (drawdown) en valor absoluto, en el mismo tramo. Ejemplo: 6 % anual con una caída máxima del 12 % → 0,5.
- **Caja**: lo que rinde el dinero sin riesgo. Aquí, las letras del Tesoro de EE. UU. a 3 meses.
- **Momentum relativo** (o fuerza relativa): ordenar activos por lo que han subido y quedarse con los primeros. Distinto del momentum "absoluto" de H2 (mirar si un activo sube o baja por sí solo).
- **Monos**: 1.000 simulaciones que deciden al azar justo aquello que la candidata dice decidir bien. Sirven para saber si el resultado se distingue de la suerte.
- **Réplica**: aplicar las mismas reglas, con los mismos números, a otros activos distintos.

## 0. Fuente, decisiones de Jorge y lo que ya está visto

### 0.1 Fuente
- Leídos: `CLAUDE.md` (con la enmienda del 2026-11-11), `docs/veredicto.md`, `docs/hipotesis.md`, `docs/baselines.md`, `docs/tareas_sonnet.md`, `config/settings.toml`, el índice de `docs/estrategias.md` y las primeras filas de `docs/registro_pruebas.md`. Ningún dato crudo, ningún backtest nuevo.
- `docs/estrategias.md` es el informe real de 20 estrategias. Sus candidatas "de lista corta" ya se gastaron en la ronda 1. **Las tres candidatas nuevas salen de conocimiento propio** (literatura que conozco), no del informe; solo el momentum por sectores aparece allí de pasada (nº 7, "versión solo-compras con pocos ETFs sectoriales"). Las citas son de memoria: solo pongo las que conozco con seguridad, y ninguna cifra de esos trabajos se usa como resultado.
- No he hecho ninguna comprobación de datos en esta sesión (para no gastar cupo). Todo lo que depende de que un dato exista está marcado "a verificar por Sonnet", con la regla de qué hacer si no existe.

### 0.2 Decisiones de Jorge del 2026-11-11 (ya anotadas en `CLAUDE.md` y en `docs/hipotesis.md`, «Enmiendas»)
1. **Objetivo = punto medio entre caída y rentabilidad.** No se exige batir a SPY en CAGR. Sí: rentabilidad claramente por encima de la renta fija/caja y mejor relación rentabilidad/caída que comprar y mantener. → criterios 16 y 17 de §4.
2. **Kill switch al −15 %** (antes −10 %). → calibración de riesgo y criterios 4, 10 y 12 de §4.
3. Todo lo demás sigue igual: solo paper, riesgo máx. 1 % por operación, stop obligatorio, máx. 3 posiciones, sin apalancamiento, cortos ni opciones.

### 0.3 Por qué murieron H1–H4 y qué cambia por ello (sin reciclarlas)

| Qué pasó (según `docs/veredicto.md`) | Lección | Respuesta en esta ronda |
|---|---|---|
| **H1** (tendencia cripto): caída IS de −22,6 % incluso con riesgo 0,5 %. | Tres posiciones en criptos que se mueven juntas son una sola apuesta muy volátil; no cabe en un freno de emergencia del 10 % y, con esos números, tampoco en uno del 15 %. | **Ninguna candidata cripto** (ver §1). Bajar más el riesgo de H1 hasta que quepa sería un retoque sobre datos vistos. |
| **H2** (momentum 12 meses): 43 operaciones, p = 0,597 contra el azar. | Una señal lenta con pocas operaciones no se distingue de "estar comprado en activos que subieron". Y los monos deben decidir al azar **lo mismo** que la candidata dice decidir bien. | Candidatas con más decisiones independientes (H6: unas 36 al año). Monos **hechos a medida** de cada hipótesis (§3.4) y umbral más duro (p < 0,02). |
| **H3** (RSI): 0,01 R; negativa con costes × 2 y con un día de retraso. | Las ventajas pequeñas y rápidas no sobreviven a entrar en la apertura siguiente. | Las pruebas de costes × 2 y de retraso se mantienen tal cual, también para H6 (que es la más expuesta a este problema; se dice en su ficha). |
| **H4** (ruptura 55/20 en ETFs): 13 de 14 criterios; CAGR 3,45 % en OOS con exposición media del 40,3 %. | Lo que más limitó no fue la señal sino ir **medio vacío**: riesgo 0,5 % + pocas entradas. | Candidatas que están invertidas por diseño cuando hay algo que comprar (rotación: siempre los 3 primeros que cumplan), y kill switch al 15 % (deja usar más riesgo). |
| El criterio 3 comparaba con SPY al 100 %. | El rival no era el que Jorge quería. | Criterios 16–17 nuevos, escritos según su decisión. |
| p = 0,047 de H4, sin corregir por intentos. | Un 0,05 pelado con varias candidatas es poco. | p < 0,02 y presupuesto de variantes más corto. |

**Los criterios nuevos no son una puerta trasera para H4.** Con las cifras de `H4-OOS` (veredicto): relación de H4 = 3,45 / 7,04 = 0,49; relación de SPY = 14,65 / 24,50 = 0,60. H4 **también suspendería** el criterio 17 nuevo en ese tramo. No se vuelve a juzgar: está muerta (enmienda 16 de `docs/hipotesis.md`).

### 0.4 Inventario de contaminación (lo que ya se ha visto antes de escribir esto)

| Qué | Dónde se vio | Qué contamina |
|---|---|---|
| Comprar y mantener SPY, 60/40 y BTC en todos los tramos, incluido 2021-01 → 2026-10 | `baselines.md`, veredicto | Conozco el listón que hay que superar en el criterio 17 (p. ej. relación de SPY ≈ 0,60 en 2021–2026 y ≈ 0,19 en el periodo completo de H4). **No puedo fingir que no lo sé.** |
| Faber, momentum 12 m, dual momentum y Donchian 20/10 en periodo completo sobre SPY, QQQ, EFA, EEM, TLT, GLD, BTC | `baselines.md` | La familia "tendencia" en esos activos. |
| H4 en OOS 2021–2026 sobre SPY, EFA, EEM, IEF, GLD, DBC, VNQ, con detalle por activo | veredicto | Ese tramo, para esos 7 ETFs, está **gastado**. |
| IS de H1 (cripto hasta 2023-06), H2, H3 (SPY, QQQ, IWM, DIA, EFA, EEM), H4 | veredicto | Los IS de esas familias. Además: los monos de H2 son, en la práctica, "estar comprado en clases de activo con stop de 4 ATR" (ver descartada «cartera permanente» en §1). |
| **Mi propio conocimiento general** de lo que hicieron los mercados hasta mediados de 2026 (qué sectores subieron, cuándo cayeron los bonos, etc.) | No es un archivo: es lo que sé | **Todo el pasado, para cualquier activo.** Ningún backtest que yo diseñe es una prueba limpia del todo. |
| Lo que **no** se ha visto en este proyecto | — | Ningún backtest con ETFs sectoriales (XL*) ni de países (EW*), ni `MDY`; nada anterior a 2005 (baselines) / 2007-07 (candidatas); ninguna regla de calendario; el OOS de cripto 2023-07 → 2026-10 con una estrategia (sigue intacto y esta ronda no lo toca). |

Consecuencia, dicha sin rodeos: **el tramo 2021-01 → 2026-10 ya no puede ser "el examen final"**. En esta ronda solo puede **vetar** (si una candidata falla ahí, muere), nunca **demostrar**. La validación creíble se reparte en una escalera de cuatro pruebas (§3.1), de las cuales tres no se han visto nunca en este proyecto y la última (paper) no la ha visto nadie.

## 1. Descartadas (ronda 2)

| Idea | Motivo |
|---|---|
| H1–H4 juzgadas otra vez con los criterios nuevos, o con otro riesgo/parámetros | Sobreajuste: datos ya vistos. Prohibido (enmienda 16 de `hipotesis.md`). |
| Tendencia con **velas semanales** en los 7 ETFs de H4 (idea del veredicto) | Una ruptura de ~11 semanas sobre los mismos activos es H4 con otro reloj. Demasiado cerca de una reescritura con retoques, y su tramo 2021–2026 está gastado. |
| **Rotación de los 3 más fuertes entre las 7 clases de activo** de H2/H4 (idea del veredicto) | La idea (rotar por fuerza relativa) sí se prueba, pero en un universo **no visto** (H5). Sobre esos 7 ETFs ya sé qué activos ganaron y perdieron en 2021–2026. |
| **Cripto** (tendencia con un solo hueco, o cualquier otra) | (1) El IS está visto y la caída no cabe en el 15 %. (2) Con la decisión 1, el rival sería "relación rentabilidad/caída de comprar y mantener BTC", y con las cifras de `H1-IS` la tendencia quedaba por debajo (26,84 / 32,62 = 0,82 frente a 87,07 / 83,40 = 1,04): propondría algo que ya sé que suspende, o tendría que inventar un criterio a medida. (3) No conozco un efecto de calendario o de selección en cripto con evidencia sólida. Su OOS queda intacto para el futuro. **PENDIENTE DE JORGE (P9).** |
| **Cartera permanente con stops** (bolsa + bonos + oro siempre comprados, tamaño por riesgo) | Encaja con el objetivo, pero **ya la hemos visto sin querer**: los monos de H2 eran justo "estar comprado en clases de activo con las mismas salidas y stops", y H2 no se distinguió de ellos con Sharpe 0,41 (`H2-AZAR`), por debajo del mínimo de 0,5. No sería una hipótesis nueva sino una ya medida. |
| Dual momentum / Faber "puros" | Vistos en `baselines.md` (periodo completo) y absorbidos en H2. |
| Ajuste de la exposición por volatilidad (Moreira y Muir, 2017) | No es una señal de entrada/salida; el tamaño por ATR ya reduce la posición cuando sube la volatilidad. Con una sola posición el tope de equity/3 la deja en un tercio invertida. |
| "Vender en mayo" (Bouman y Jacobsen, 2002) | 2 decisiones al año: unas 27 en todo el IS. Imposible de distinguir del azar (lección de H2). |
| Deriva antes de las reuniones de la Fed (Lucca y Moench, 2015) | 8 al año; el efecto ocurre en las 24 h previas al anuncio y nuestro script opera una vez al día en la apertura; hay indicios publicados de que se ha debilitado. |
| Semana de vencimiento de opciones, efecto víspera de festivo | Misma familia que H6 (calendario) con evidencia más floja. Con una de calendario basta. |
| Efecto "noche" (comprar al cierre, vender en la apertura) | Una operación diaria: los costes se lo comen; exige operar al cierre. |
| Reversión semanal, Bollinger, IBS y similares | Familia de H3. Muerta por costes y retraso. |
| Acciones individuales (máximos de 52 semanas, etc.) | Sesgo de supervivencia. |

## 2. Candidatas

Tres candidatas, de **dos familias**: selección entre sectores (H5 por fuerza, H7 por calma; comparten esqueleto a propósito, para que la única diferencia sea la hipótesis) y calendario (H6). Como mucho una de H5/H7 puede acabar operándose (§5).

### Reglas comunes (pre-registradas)

Las de `docs/hipotesis.md` §2 «Reglas comunes» siguen en vigor sin cambios: ejecución en la apertura de `t+1`; stop fijo `cierre_t − k × ATR(20)_t` puesto antes de entrar; no se entra si la apertura ya está en el stop; `ATR` de Wilder con `atr_n = 20` fijo; tamaño `floor(f × equity / riesgo_por_unidad)` con costes dentro; **acciones enteras**; tope por posición de `equity / 3`; cantidad 0 → no se opera; máx. 3 posiciones; cierres ajustados; efectivo al 0 %; mismos parámetros para todo el universo.

Añadidos de esta ronda:
- **Fracción de riesgo `f`:** 1 % como máximo; se calibra en IS con el kill switch nuevo (§3.3).
- **Día de revisión mensual** (H5, H7): la vela `t` es la primera sesión del mes (su mes es distinto del de la vela anterior). Igual que en H2: se sabe con datos ≤ t.
- **Calendario de sesiones** (solo H6): la lista de días en que abre la bolsa de Nueva York se conoce con meses de antelación; usarla **no es mirar al futuro**. En vivo sale de `get_calendar` de Alpaca. En el backtest se usa la lista de sesiones que realmente hubo (el índice de SPY). Limitación declarada: los cierres no programados (p. ej. el huracán de finales de octubre de 2012) están en esa lista aunque no se conocían de antemano; son un puñado de días en 26 años.

---

### H5 — `sector_mom`
- **Idea en una frase:** una vez al mes, tener los 3 sectores de la bolsa de EE. UU. que más han subido en los últimos 6 meses (y solo si han subido), y soltar el que se descuelga.
- **Razón económica / evidencia:** el momentum en acciones es en buena parte momentum **de industrias** (Moskowitz y Grinblatt, 1999, *Journal of Finance*): las noticias de un sector se incorporan despacio y el dinero llega por oleadas. Faber (2010, "Relative Strength Strategies for Investing") lo aplica a sectores con reglas mensuales simples. Quien paga es quien rota tarde. Conocimiento propio. Ojo: los trabajos académicos usan carteras largo/corto y sin stops; esto es una versión solo larga, con 3 huecos y stop. Parte del esqueleto (filtro "ha subido" + stop + revisión mensual) se parece a H2: por eso los monos de H5 **conservan** ese esqueleto y solo barajan el orden (§3.4). Lo que se pone a prueba es la **selección**, que H2 no tenía (H2 no rotaba).
- **Universo y timeframe:** los 9 ETFs sectoriales Select Sector SPDR que existen desde diciembre de 1998: `XLB`, `XLE`, `XLF`, `XLI`, `XLK`, `XLP`, `XLU`, `XLV`, `XLY`. Se excluyen `XLRE` (2015) y `XLC` (2018) para que el universo sea el mismo en todos los tramos. Velas diarias, **decisión mensual**. Nunca usados en un backtest de este proyecto.
- **Datos (fuente, desde, ajustes):** yfinance ajustado, desde **1998-12** (a verificar por Sonnet; `settings.toml` hoy empieza en 2003). Cada activo entra cuando tiene ≥ 365 velas (≈ junio de 2000). Alpaca desde 2016 para contrastar.
- **Indicadores (fórmulas):**
  - `mom_t = cierre_t / cierre_{t−126} − 1` (126 sesiones ≈ 6 meses; cierres ajustados).
  - `apto_t = (mom_t > 0)` y ATR disponible.
  - `puesto_t` = posición del activo (1 = el mejor) al ordenar **solo los aptos** por `mom_t` de mayor a menor; empates por símbolo alfabético.
  - `ATR(20)_t`.
- **Entrada:** día de revisión, `apto_t` y `puesto_t ≤ 3` → comprar en la apertura de `t+1` si hay hueco (primero se ejecutan las salidas del día).
- **Salida:** día de revisión y (`no apto_t` **o** `puesto_t > 5`) → vender en la apertura de `t+1`. O antes si salta el stop. El margen entre 3 y 5 evita cambiar de sector cada mes por diferencias mínimas (menos costes). Si un sector que ya se tiene está en el puesto 4–5, conserva su hueco aunque otro haya entrado en los 3 primeros. Tras un stop se puede volver a entrar en la siguiente revisión si cumple.
- **Stop (fórmula exacta):** `stop = cierre_t − 3,0 × ATR(20)_t` (vela de señal). Fijo. 3 ATR diarios son algo menos de una desviación típica mensual: es un stop de catástrofe para una posición que se revisa cada mes. Se elige 3 y no los 4 de H2 por la lección de H4 (exposición): con 4 la cartera iría aún más vacía. Decidido por ese razonamiento, sin mirar ningún dato de sectores.
- **Ranking si hay > 3 señales:** `rank = mom_t`, mayor primero.
- **Parámetros por defecto | rango robustez:** `lookback = 126` | {95, 126, 158} · `atr_mult = 3,0` | {2,25, 3,0, 3,75} · `keep_n = 5` | {4, 5, 6} · fijos: `top_n = 3` (son los huecos), `atr_n = 20`. Rejilla 3×3×3 = 27.
- **Ejemplo numérico de sizing (equity 10.000 $, precios inventados, slippage 5 pb):**
  - XLK a 250 $, ATR 4 $ → stop 238. Riesgo por unidad = 250,125 − 237,881 = 12,244 $ → `floor(100 / 12,244)` = **8 acciones** (2.001,00 $; riesgo 97,95 $).
  - XLE a 90 $, ATR 1,80 $ → stop 84,60. Riesgo por unidad = 90,045 − 84,558 = 5,487 $ → **18 acciones** (1.620,81 $; riesgo 98,77 $).
  - XLU a 80 $, ATR 0,90 $ → stop 77,30. Riesgo por unidad = 80,04 − 77,261 = 2,779 $ → **35 acciones** (2.801,40 $; riesgo 97,25 $).
  - Total: 3 posiciones, 6.423 $ = **64 % de exposición** ≤ 100 % ✔; cada riesgo ≤ 100 $ ✔; ninguna supera 3.333 $ ✔.
- **Nº de operaciones esperado (estimación, no medido):** 3 huecos con permanencias de 3–4 meses más algún stop → ~10–15 al año cuando el mercado sube, menos en los bajistas. IS (13,5 años): **~120–190**. Reservado antiguo (7 años): ~50–90. Reservado reciente (5,8 años): ~55–85.
- **Benchmark:** comprar y mantener **SPY** (el del criterio 17) y **caja** (criterio 16). Informativo: 60/40 y los 9 sectores a partes iguales.
- **Riesgos conocidos / cuándo dejaría de funcionar:** los 9 sectores caen juntos en un desplome (3 posiciones = una apuesta de bolsa; el filtro "ha subido" llega tarde en caídas rápidas tipo 2020); giros bruscos de liderazgo (el sector fuerte de ayer es el que más cae); exposición media por debajo del 100 % con el efectivo al 0 %; el momentum sectorial es un efecto modesto y, con 3 de 9, puede no distinguirse de elegir al azar: si es así, muere en el criterio 14.

---

### H6 — `tom_etf`
- **Idea en una frase:** estar comprado en bolsa solo alrededor del cambio de mes (desde el último día del mes hasta el tercero del siguiente) y en efectivo el resto del tiempo.
- **Razón económica / evidencia:** efecto "cambio de mes" (*turn of the month*): Ariel (1987, *Journal of Financial Economics*), Lakonishok y Smidt (1988, *Review of Financial Studies*, 90 años del Dow) y McConnell y Xu (2008, *Financial Analysts Journal*), que lo encuentran en EE. UU. y en la mayoría de los países que miran. Explicación más citada (Ogden, 1990, *Journal of Finance*): nóminas, aportaciones a planes de pensiones y pagos se concentran a fin de mes y una parte entra en bolsa esos días. Quien paga es quien vende sin prisa justo antes de esa entrada de dinero. Conocimiento propio. Dos avisos honrados: (1) es una anomalía de calendario conocida desde hace décadas y puede haberse gastado; el IS (2007–2020) es **posterior** a las publicaciones, lo que lo convierte en una prueba más seria que para una idea recién minada; (2) la ganancia por operación es pequeña: es la candidata con más riesgo de morir como H3, por costes o por entrar tarde.
- **Universo y timeframe:** `SPY` (grandes de EE. UU.), `IWM` (pequeñas de EE. UU.), `EFA` (desarrollados fuera de EE. UU.). Tres activos, tres huecos: no hace falta ordenar. Velas diarias; hay algo que hacer **dos días al mes**.
- **Datos (fuente, desde, ajustes):** yfinance ajustado: SPY desde 1993; IWM desde ~2000-05 y EFA desde ~2001-08 (a verificar por Sonnet). Cada activo entra con ≥ 365 velas.
- **Indicadores (fórmulas):** con el calendario de sesiones `C`:
  - `quedan_t` = nº de sesiones de `C` posteriores a `t` dentro del mismo mes (0 = última sesión del mes).
  - `ordinal_t` = posición de `t` dentro de su mes (1 = primera sesión).
  - `ATR(20)_t`.
- **Entrada:** `quedan_t = 1` (penúltima sesión del mes) y ATR disponible → comprar en la **apertura de la última sesión del mes**.
- **Salida:** `ordinal_t = 3` → vender en la **apertura de la 4.ª sesión del mes**. O antes si salta el stop (y entonces no se vuelve a entrar hasta el mes siguiente). La posición vive: la última sesión del mes y las tres primeras del siguiente. La ventana clásica de los papers va de cierre a cierre (días −1 a +3); la nuestra va de apertura a apertura porque el script ejecuta en la apertura siguiente: se pierde el salto de la víspera y se gana el de la 4.ª apertura. Declarado.
- **Stop (fórmula exacta):** `stop = cierre_t − 3,0 × ATR(20)_t` (vela de señal). Fijo. Para una posición de 4 sesiones, 3 ATR queda fuera del ruido normal.
- **Ranking si hay > 3 señales:** no aplica (3 activos); por símbolo alfabético.
- **Parámetros por defecto | rango robustez:** `entry_before_end = 1` | {1, 2} · `exit_day = 3` | {2, 3, 4} · `atr_mult = 3,0` | {2,25, 3,0, 3,75} · `atr_n = 20` fijo. Son días enteros: el "±25 %" se traduce en mover un día. Rejilla 2×3×3 = 18.
- **Ejemplo numérico de sizing (equity 10.000 $, precios inventados, slippage 5 pb):**
  - SPY a 600 $, ATR 6 $ → stop 582. Riesgo por unidad = 600,30 − 581,709 = 18,591 $ → **5 acciones** (3.001,50 $; riesgo 92,96 $).
  - IWM a 220 $, ATR 3,30 $ → stop 210,10. Riesgo por unidad = 220,11 − 209,995 = 10,115 $ → **9 acciones** (1.980,99 $; riesgo 91,04 $).
  - EFA a 85 $, ATR 0,85 $ → stop 82,45. Riesgo por unidad = 85,0425 − 82,4088 = 2,6337 $ → **37 acciones** (3.146,57 $; riesgo 97,45 $).
  - Total: 8.129 $ = **81 % de exposición** durante la ventana ✔; cada riesgo ≤ 100 $ ✔; ninguna supera 3.333 $ ✔. El resto del mes: 0 %.
- **Nº de operaciones esperado (estimación, no medido):** 12 al año por activo → **~36 al año**. IS: **~480**. Reservado antiguo: ~170–200 (IWM y EFA entran más tarde). Reservado reciente: ~210. Es la candidata con más muestra.
- **Benchmark:** comprar y mantener **SPY** y **caja**. Informativo: 60/40.
- **Riesgos conocidos / cuándo dejaría de funcionar:** efecto pequeño frente a costes (12 idas y vueltas al año por activo); muy sensible a entrar un día tarde; los 3 activos son bolsa (una sola apuesta de ~4 días); un desplome que caiga en la ventana se come varios meses de ganancias; puede estar arbitrado. Lo bueno, si existe: el dinero está fuera del mercado ~80 % de los días.

---

### H7 — `sector_lowvol`
- **Idea en una frase:** el mismo esqueleto que H5 (revisión mensual, 3 huecos, solo sectores que han subido en 6 meses), pero eligiendo los 3 sectores **más tranquilos** en vez de los 3 que más han subido.
- **Razón económica / evidencia:** anomalía de baja volatilidad: los activos tranquilos han rendido, por unidad de riesgo, más de lo que la teoría dice (Ang, Hodrick, Xing y Zhang, 2006; Blitz y van Vliet, 2007; Baker, Bradley y Wurgler, 2011; Frazzini y Pedersen, 2014). Explicación habitual: muchos inversores no pueden apalancarse y, para ganar más, compran lo más movido, que queda caro. Quien paga es quien compra "lotería". Conocimiento propio. Aviso: esa evidencia es de **acciones individuales**; a nivel de sectores es más floja y en la práctica significa cargar consumo básico, salud y eléctricas. Es la candidata con **peor respaldo** de las tres y la de menos operaciones; entra porque es la que más directamente persigue el objetivo de Jorge (caer poco estando invertido) y porque casi no cuesta trabajo extra (comparte datos y código con H5).
- **Universo, timeframe y datos:** los de H5.
- **Indicadores (fórmulas):**
  - `mom_t` y `apto_t` como en H5 (`lookback = 126`).
  - `vol_t` = desviación típica (muestral) de las últimas 126 rentabilidades diarias logarítmicas `ln(cierre_i / cierre_{i−1})`, hasta `t` incluida.
  - `puesto_t` = posición al ordenar **solo los aptos** por `vol_t` de menor a mayor.
- **Entrada / Salida / Stop:** idénticos a H5 (`puesto ≤ 3` entra; `no apto` o `puesto > 5` sale; `stop = cierre_t − 3,0 × ATR(20)_t`).
- **Ranking si hay > 3 señales:** `rank = −vol_t`.
- **Parámetros por defecto | rango robustez:** `lookback = 126` | {95, 126, 158} (la misma ventana para `mom` y `vol`) · `atr_mult = 3,0` | {2,25, 3,0, 3,75} · `keep_n = 5` | {4, 5, 6}. Rejilla 27.
- **Ejemplo numérico de sizing (equity 10.000 $, precios inventados):**
  - XLP a 80 $, ATR 0,70 $ → stop 77,90. Riesgo por unidad = 80,04 − 77,861 = 2,179 $ → 45 acciones (3.601,80 $) → **el tope de 3.333 $ lo deja en 41** (3.281,64 $; riesgo 89,34 $).
  - XLV a 150 $, ATR 1,50 $ → stop 145,50. Riesgo por unidad = 150,075 − 145,427 = 4,648 $ → **21 acciones** (3.151,58 $; riesgo 97,60 $).
  - XLU a 80 $, ATR 0,90 $ → **35 acciones** (2.801,40 $; riesgo 97,25 $).
  - Total: 9.235 $ = **92 % de exposición** ≤ 100 % ✔. En sectores tranquilos el tope manda a menudo.
- **Nº de operaciones esperado (estimación, no medido):** los sectores tranquilos cambian poco: ~5–8 operaciones al año. IS: **~70–110**. Reservados: ~35–55 cada uno. Puede no llegar a 100 en IS; con los tres tramos sí debería. Ver criterio 1.
- **Benchmark:** como H5.
- **Riesgos conocidos / cuándo dejaría de funcionar:** concentración en 3 sectores defensivos sensibles a los tipos de interés; se queda atrás en mercados alcistas liderados por tecnología (sé, por conocimiento general, que 2023–2025 fue así: lo declaro, y es una razón para esperar que le cueste el tramo reciente); pocas operaciones; con tan poca rotación, los monos pueden parecerse mucho a ella.

## 3. Diseño de validación

Todo con `portfolio_sim`, costes incluidos, 10.000 $ iniciales, parámetros por defecto y **sin optimizar nada** (el walk-forward es la única prueba que elige parámetros, y solo dentro del IS).

### 3.1 La escalera: cuatro pruebas, en este orden, cada una **una sola vez**

| Peldaño | Qué es | Fechas | ¿Visto antes? | Papel |
|---|---|---|---|---|
| **0. IS** (desarrollo) | Universo de la candidata | 2007-07-01 → 2020-12-31 | Sectores: no. SPY/IWM/EFA: sí en otras reglas | Filtros: si falla algo aquí, muere sin gastar nada más |
| **1. Réplica** | Mismas reglas y números, **otros activos** (§3.2) | 2000-07-01 → 2026-10-31 | No | Coherencia: ¿la idea funciona fuera de los tickers elegidos? |
| **2. Reservado antiguo** | Universo de la candidata | 2000-07-01 → 2007-06-30 | **No** (nada del proyecto mira antes de 2005; nada de las candidatas antes de 2007-07) | Prueba principal en backtest. Incluye el mercado bajista de 2000–2002 |
| **3. Reservado reciente** | Universo de la candidata | 2021-01-01 → 2026-10-31 | **Parcialmente** (§0.4) | **Solo veto.** Pasarlo no demuestra nada |
| **4. Paper** (examen final) | Alpaca paper, en vivo | 12 meses desde el arranque | No lo ha visto nadie | La única prueba limpia de verdad (§3.6) |

Reglas de la escalera:
- Se sube de uno en uno. **Fallar un peldaño mata a la candidata** y los siguientes **no se ejecutan** (quedan intactos para otra ronda).
- Antes del peldaño 1 se **congelan** parámetros y fracción de riesgo en un commit (como en la ronda 1). Nada se cambia después.
- Cada ejecución de los peldaños 1–3 se anota en `reports/oos_log.csv` con el peldaño. Las de estrés (costes × 2, retraso) y la ejecución completa (abajo) llevan el mismo hash de parámetros y se anuncian aquí, antes de ver nada.
- **Ejecución completa:** después del peldaño 3, **una** ejecución continua 2000-07-01 → 2026-10-31 con lo congelado, para los criterios que necesitan todo el periodo (1, 4, 9, 10, 11, 13, 16d). No decide los criterios de tramo. Costes de esa ejecución: los de cada época (10 pb hasta 2007-06-30, 5 pb después).
- Calentamiento de indicadores con datos anteriores a cada inicio. Cada tramo arranca con 10.000 $ y sin posiciones.
- Si un dato no existe en la fecha prevista (lo verifica Sonnet **sin** calcular rentabilidades): el inicio del peldaño afectado se retrasa, para todo su universo, al primer día del mes siguiente a la primera fecha válida, y se anota como enmienda **antes** de ejecutar nada. Si un símbolo de una réplica no existe o no es operable en Alpaca, se quita sin sustituirlo.
- **Por qué el reservado antiguo vale:** no lo he mirado y este proyecto tampoco. **Por qué no es perfecto:** el mercado de entonces era distinto (ETFs con menos liquidez) y los papers de H6 cubren parte de esos años. Por eso allí los costes base se **doblan** (§3.5) y por eso hay réplica y paper además.

### 3.2 Universos de réplica (fijados ahora, por criterios que no son "lo que mejor fue")

| Candidata | Universo de réplica | Cómo se eligió |
|---|---|---|
| H5 y H7 | 9 ETFs de países de iShares lanzados en 1996: `EWJ` (Japón), `EWG` (Alemania), `EWU` (Reino Unido), `EWC` (Canadá), `EWQ` (Francia), `EWI` (Italia), `EWA` (Australia), `EWL` (Suiza), `EWH` (Hong Kong) | Los 6 países del G7 que no son EE. UU. más los 3 mercados desarrollados siguientes que recuerdo de esa primera tanda. 9, como los sectores. El momentum entre países está documentado (Asness, Liew y Stevens, 1997); la baja volatilidad entre países, mucho menos (se asume). |
| H6 | `MDY` (medianas de EE. UU.), `EEM` (emergentes), `EWJ` (Japón) | Tres bolsas que no son las de H6. `EEM` entra cuando tiene 365 velas (≈ 2004). McConnell y Xu encuentran el efecto fuera de EE. UU. |

La réplica no es independiente (todas las bolsas caen juntas), así que no cuenta como segunda prueba estadística. Sirve para una cosa: detectar si el resultado depende de **estos** 9 o 3 tickers.

### 3.3 Kill switch y calibración del riesgo (con el −15 % nuevo)
1. Las métricas se miden con el kill switch **desactivado**, como en la ronda 1, y aparte se cuentan los episodios de caída > 15 % (reiniciando el máximo tras cada uno).
2. **Calibración, solo con IS:** la mayor `f` ∈ {1,0 %, 0,75 %, 0,5 %} con caída máxima IS **≤ 12 %**. Se deja un margen de 3 puntos bajo el 15 % porque la peor caída futura suele ser mayor que la peor del pasado; calibrar justo al 15 % sería diseñar para que el freno salte. Si ni con 0,5 % se cumple, la candidata muere en IS. **PENDIENTE DE JORGE (P10).**
3. `f` queda congelada para todos los peldaños y para el paper.

### 3.4 Monos a medida (criterio 14 y réplica), 1.000 simulaciones, semilla 42
> Ampliado y precisado por las enmiendas E4 y E5 (2026-11-12), al final del archivo.
- **H5 y H7:** mismas reglas, mismo filtro `apto`, mismos stops, tamaños y costes; lo único que cambia es que el **orden** de los aptos se sortea en cada revisión (se sortea una vez por mes y se usa para `puesto` y `rank`). Pregunta que contesta: ¿elegir por fuerza (o por calma) es mejor que elegir 3 sectores aptos al azar?
- **H6:** mismos activos, stops, tamaños y costes; en cada mes se sortea **la sesión de entrada** entre todas las del mes (la misma para los 3 activos) y se sale en la apertura 4 sesiones después de la de entrada. Pregunta: ¿el cambio de mes es mejor que 4 sesiones cualesquiera?
- Estadístico: Sharpe del tramo. p = proporción de monos con Sharpe ≥ el real.
- Informativo (no criterio): los monos de entrada al azar de la ronda 1.

### 3.5 Walk-forward, presupuesto y costes
- **Walk-forward** (solo IS): igual que en la ronda 1 para ETFs. Entrenamiento creciente desde 2007-07-01; **8 ventanas** de un año natural (2013 … 2020); en cada paso, la combinación de la rejilla con mayor Sharpe en el entrenamiento (empate → la más cercana a la de por defecto). Mismas convenciones (enmienda 7 de `hipotesis.md`). Hacen falta ≥ 5 ventanas válidas.
- **Presupuesto de variantes:** máximo **30 por candidata** (rejilla + niveles de riesgo), 90 en total. Sin barridos extra. Todo a `docs/registro_pruebas.md`, salga como salga. Intentos heredados: las familias "selección entre sectores" y "calendario" no tienen intentos previos en este proyecto; el proyecto en conjunto lleva 74 variantes de candidatas y dos barridos de 330 y 72 (veredicto), y se dirá al informar de DSR/PBO.
- **Costes por lado:**

  | Dónde | Slippage base | Estrés |
  |---|---|---|
  | IS y reservado reciente, universos principales | 5 pb | × 2 |
  | **Reservado antiguo** (2000-07 → 2007-06) | **10 pb** (los ETFs tenían más horquilla entonces) | × 2 (20 pb) |
  | **Réplicas** (todo el tramo, todos sus ETFs) | **15 pb** (el valor del prompt para ETFs menos líquidos; el motor solo admite un coste por ejecución, se aplica el pesimista a todos) | × 2 |

  Comisión 0 $ (ETFs). El efectivo no rinde nada.
- **Benchmarks:** comprar y mantener SPY con los mismos costes y tramos; **caja** = capitalizar a diario el tipo de las letras a 3 meses (`^IRX` en yfinance; a verificar por Sonnet, con alternativa en `docs/tareas_sonnet.md`); `IEF` comprar y mantener (existe desde ~2002-07); 60/40 informativo.

### 3.6 El examen final: paper (peldaño 4), pre-registrado ahora
Una candidata que supera los peldaños 0–3 queda **"apta para paper"**, no "aprobada". El aprobado definitivo de este experimento se decide así:

- **Duración:** 12 meses naturales desde la primera orden. Revisión intermedia a los 6 meses que **solo** mira fidelidad y seguridad (puntos a, c y d); no se cambia ningún parámetro en ningún caso. **PENDIENTE DE JORGE (P8).**
- **(a) Fidelidad:** cada semana se vuelve a ejecutar el backtest sobre las fechas del paper con los datos reales. Las entradas y salidas del paper deben coincidir en fecha y activo con las del backtest, salvo diferencias de datos documentadas una a una. El slippage medio realmente sufrido (precio de ejecución frente a la apertura oficial) debe ser ≤ el de estrés (10 pb).
- **(b) Dentro de lo previsto:** antes de la primera orden, el paso 3 calcula con el backtest una banda de resultados esperados a 12 meses (remuestreo por bloques de 21 sesiones de las rentabilidades diarias de la ejecución completa, 10.000 trayectorias, semilla 42) y la escribe en `STRATEGY.md`. Si a los 12 meses el resultado está **por debajo del percentil 5**, la estrategia queda **refutada**.
- **(c) Seguridad:** el kill switch (−15 %) no salta.
- **(d) Reglas duras:** ninguna violación. Una violación es un fallo del ejecutor: se arregla y el reloj vuelve a cero.
- **Qué demuestra y qué no:** 12 meses no bastan para demostrar una ventaja (harían falta muchos años). Superarlo significa "**no refutada y operable**". Suspenderlo sí es informativo. Y en ningún caso autoriza dinero real: eso queda fuera de este proyecto.
- Mientras dura el paper, los datos nuevos (desde 2026-11-01) son también un tramo reservado que crece solo: se informa de él en la revisión semanal, sin tocar nada.

## 4. Criterios de aceptación (checklist)

Una candidata es **apta para paper** solo si **todas** las casillas son "sí". Salvo que se diga otra cosa: costes base del tramo, parámetros por defecto, `f` calibrada, kill switch desactivado, Sharpe con tipo libre de riesgo 0.

"Relación" = CAGR / |caída máxima| del mismo tramo. "Caja" y "SPY" = los benchmarks de §3.5 en el mismo tramo.

**A. Filtros en IS (peldaño 0). Si falla uno, muere y no gasta ningún tramo reservado.**
- [ ] **0. Corte rápido:** expectancy IS con costes > 0.
- [ ] **Calibración (§3.3):** existe `f` con caída máxima IS ≤ 12 %.
- [ ] **3-IS.** Sharpe IS ≥ 0,5.
- [ ] **5. Walk-forward:** ≥ 60 % de las ventanas válidas positivas (≥ 5 de 8).
- [ ] **6. Robustez:** ≥ 70 % de las vecinas de la rejilla con expectancy > 0 **y** Sharpe ≥ 50 % del central (vecina sin operaciones = fallo).
- [ ] **7-IS. Costes × 2:** expectancy > 0.
- [ ] **8-IS. Retraso de 1 vela** en la entrada: expectancy > 0.
- [ ] **10-IS. Monte Carlo** (1.000 barajados, semilla 42): percentil 95 de la caída ≤ **22,5 %** (1,5 × 15 %; antes 30 %).
- [ ] **14. Mejor que sus monos (§3.4):** p **< 0,02** en Sharpe IS (antes 0,05).
- [ ] **16-IS.** CAGR IS ≥ CAGR de la caja en IS **+ 2,0 puntos**.
- [ ] **17-IS.** Relación IS **>** relación de SPY en IS.

**B. Réplica (peldaño 1).**
- [ ] **15.** En el universo de réplica, tramo completo: expectancy > 0, Sharpe > 0 **y** Sharpe por encima del 75 % de sus monos (percentil ≥ 75). No se le exige significación propia: se le exige apuntar en la misma dirección.

**C. Tramos reservados (peldaños 2 y 3). Cada casilla debe cumplirse en el antiguo y en el reciente, por separado, salvo 16a.**
- [ ] **2.** Expectancy > 0,10 R.
- [ ] **3.** Sharpe ≥ 0,5.
- [ ] **7.** Costes × 2: expectancy > 0.
- [ ] **8.** Retraso de 1 vela: expectancy > 0.
- [ ] **12.** El kill switch literal (−15 % desde el máximo, arrancando al inicio del tramo) **no salta**.
- [ ] **16b.** CAGR > CAGR de la caja en ese tramo (sin margen: en 6–7 años el margen de 2 puntos lo decidiría la suerte; el margen se exige en 16a).
- [ ] **16a (los dos tramos juntos).** CAGR conjunto ≥ CAGR conjunto de la caja **+ 2,0 puntos**, con `CAGR conjunto = (G_antiguo × G_reciente)^(1 / años totales) − 1` y `G` = capital final / inicial de cada tramo.
- [ ] **17.** Relación **>** relación de SPY (en cada tramo; los dos contienen una caída de SPY de más del 20 %, que es cuando la comparación tiene sentido).

**D. Ejecución completa (2000-07-01 → 2026-10-31).**
- [ ] **1. Muestra:** ≥ 100 operaciones cerradas; o, si no llega, ≥ 30 sumando los dos tramos reservados, y entonces se etiqueta "muestra pequeña" (aplica sobre todo a H7).
- [ ] **4. Caída máxima ≤ 15 %** (antes 20 %): con un kill switch permanente al 15 %, una estrategia que lo cruza una vez en la historia se habría quedado parada.
- [ ] **9.** Quitando las 5 mejores operaciones: resultado ≥ 0.
- [ ] **10.** Monte Carlo: percentil 95 de la caída ≤ 22,5 %.
- [ ] **11. Estabilidad:** expectancy > 0 en **≥ 3 de 4** subperiodos (2000-07-01 → 2007-06-30 · 2007-07-01 → 2013-12-31 · 2014-01-01 → 2020-06-30 · 2020-07-01 → 2026-10-31) y en ≥ 2 activos con al menos 10 operaciones cada uno.
- [ ] **13.** Quitando todas las operaciones del activo que más ha ganado: resultado ≥ 0.
- [ ] **16d (renta fija).** En el trozo de la ejecución completa en el que existe `IEF` (desde 2002-08-01, a verificar): CAGR de la estrategia ≥ CAGR de comprar y mantener `IEF` **y** ≥ caja + 2,0 puntos.
- [ ] **17d.** Relación > relación de SPY en la ejecución completa.

**E. Examen final:** peldaño 4 (§3.6). Solo tras superarlo la estrategia queda "aprobada en paper".

Reglas finales:
- Si falla en un tramo reservado, **muere**. No se reajusta ni se vuelve a probar ahí.
- **Qué cambia respecto a la ronda 1, y en qué sentido.** Sustituido por decisión de Jorge: la cláusula "Sharpe ≥ SPY, o caída ≤ 60 % y CAGR ≥ 50 % de SPY" → criterios 16 y 17. Endurecidos: p de los monos (0,05 → 0,02), caída máxima (20 % → 15 %), Monte Carlo (30 % → 22,5 %), Sharpe ≥ 0,5 también en IS, dos tramos reservados en vez de uno, réplica, y paper como examen. Relajado **solo** por la decisión 2 de Jorge: el límite del kill switch (10 % → 15 %, con calibración al 12 %). Ningún otro mínimo del prompt se ha suavizado.
- Se informa además, sin ser criterio: exposición media, rentabilidad con el efectivo rindiendo como la caja, relación frente a 60/40, peor año, peor racha, DSR y PBO.

### Opinión, escrita antes de ver nada
El listón es alto. Los criterios 16 y 17 juntos piden, en la práctica, algo así como "varios puntos por encima de las letras con caídas de un dígito", con el efectivo parado al 0 % y sin pasar del 1 % de riesgo. Es bastante probable que el resultado vuelva a ser **"ninguna apta"**, y sería un resultado válido. Lo digo ahora para que, si pasa, nadie tenga la tentación de bajar el listón después.

## 5. Criterio de selección final
1. Solo entre las aptas para paper (todo el §4, A–D).
2. **H5 y H7 no pueden ir juntas** (mismo universo y esqueleto). Si pasan las dos: la de mayor porcentaje en el criterio 6; si empatan, la de menor p en el criterio 14.
3. Si pasan H6 y una de sectores, se prefiere operar **una sola**: la de menor p en el criterio 14 (empate → más operaciones en los tramos reservados).
4. **Combinación (solo si pasan H6 y una de sectores):** las dos usan los 3 huecos, así que no caben enteras. Se pre-registra una única cartera combinada: sectores con **2 huecos** como máximo y H6 con **1 hueco, solo `SPY`**, misma `f` (la menor de las dos). Se simula **una vez** en los mismos tramos, sin cambiar ningún parámetro, y solo se opera si cumple por sí misma los criterios 4, 12, 16 y 17 **y** su relación en la ejecución completa es mayor que la de la preferida sola. Si no, se opera la preferida.
5. Si no pasa ninguna: "ninguna apta" y **no se opera**. Los peldaños que no se hayan ejecutado quedan intactos.

### Decisiones tomadas por prudencia — PENDIENTE DE JORGE
Jorge puede cambiarlas **solo antes de que se ejecute el primer backtest IS de la ronda 2**, con una enmienda fechada al final de este archivo.

| # | Decisión | Opción tomada (prudente) | Alternativa |
|---|---|---|---|
| **P7** | Efectivo parado | Rinde 0 % y así se juzga (es lo que pasa en la cuenta paper). | Aparcar el efectivo libre en un ETF de letras (`BIL`/`SGOV`). Chocaría con las reglas duras 3 y 4 (¿cuenta como posición?, ¿lleva stop?): solo Jorge. Haría bastante más fácil el criterio 16. |
| **P8** | Duración del examen en paper | 12 meses, con revisión de fidelidad a los 6. | 6 meses (más rápido, pero casi no distingue nada). |
| **P9** | Cripto | Fuera de la ronda 2; su OOS sigue intacto. | Una ronda propia de cripto, con un rival y un presupuesto de caída decididos antes por Jorge. |
| **P10** | Margen de calibración | Caída máxima IS ≤ 12 % (3 puntos bajo el kill switch). | Calibrar justo al 15 %: más rentabilidad esperada y más probabilidad de que el freno salte en paper. |
| **P11** | Qué es "renta fija/caja" | Listón duro = **letras a 3 meses** (+ 2 puntos); `IEF` solo en el tramo largo (16d), porque un fondo de bonos a 7–10 años no es "caja": también cae. | Exigir superar a `IEF` en cada tramo (más duro; depende mucho de si los tipos subían o bajaban en ese tramo). |
| **P12** | "Claramente por encima" | + 2,0 puntos porcentuales al año. | Otro margen. |
| **P13** | Rama | `ronda2/hipotesis` creada desde `paso2/candidatas`; sin fusionar y sin push. | — |

## 6. Especificación para implementar (para Sonnet)

Tareas detalladas en `docs/tareas_sonnet.md` («Ronda 2»). **Prohibido para Sonnet:** ejecutar cualquier backtest de H5–H7 con datos reales (ni IS ni ningún peldaño); solo tests con datos sintéticos. Los IS los lanza Fable en el paso 3 tras revisar el código nuevo.

### 6.1 Interfaz nueva para H5 y H7: señales "de panel"
La interfaz actual recibe **un** activo y no puede ordenar entre activos. Se añade un segundo tipo, también **puro** (sin E/S, red ni azar, sin datos > t):

`generate_signals_panel(bars: dict[str, pd.DataFrame], params: dict) -> dict[str, pd.DataFrame]`

- Entrada: OHLCV por símbolo. Salida: por símbolo, un DataFrame con el índice de ese símbolo y columnas `entry`, `exit`, `stop_price`, `rank` (partir de `empty_signals`).
- No tiene estado ni sabe qué hay en cartera: `exit = True` significa "si lo tienes, véndelo"; el simulador lo ignora si no hay posición. Un mismo activo nunca lleva `entry` y `exit` el mismo día.
- El simulador no cambia; hay que **comprobar con un test** que en una misma apertura las salidas liberan hueco antes de procesar las entradas.
- Un activo con menos de `lookback + 1` cierres o sin ATR no es apto ni ocupa puesto.
- Los tests de look-ahead (truncar y "envenenar" el futuro) se extienden a este tipo.

### 6.2 `sector_mom` (H5) y `sector_lowvol` (H7)
> «Índice común» queda precisado por la enmienda E7 (2026-11-12), al final del archivo.
- Un módulo con un parámetro `rank_by ∈ {"mom", "lowvol"}`; dos TOML.
- `params` H5: `rank_by="mom", lookback=126, top_n=3, keep_n=5, atr_mult=3.0, atr_n=20`. H7: igual con `rank_by="lowvol"`. `robust_keys = ["lookback", "atr_mult", "keep_n"]`.
- En cada día de revisión `t` (primera sesión del mes en el índice común): `mom = close/close.shift(lookback) − 1`; `apto = (mom > 0) & atr.notna()`; `clave = mom` (H5) o `−std(ln rentabilidades, ventana lookback, ddof=1)` (H7); `puesto` = orden de los aptos por `clave` descendente, empates por símbolo. `entry = revisión & apto & (puesto ≤ top_n)`; `exit = revisión & (~apto | (puesto > keep_n))`; `stop_price = close − atr_mult × ATR`; `rank = clave`. Fuera de los días de revisión: todo `False`.
- TOML (los dos): `universe = ["XLB","XLE","XLF","XLI","XLK","XLP","XLU","XLV","XLY"]`, `benchmark = "SPY"`, `replica_universe = ["EWJ","EWG","EWU","EWC","EWQ","EWI","EWA","EWL","EWH"]`, tramos de §3.1, `status = "preregistrada"`, `risk_levels = [0.01, 0.0075, 0.005]`, `calibration_dd_limit = 0.12`.

Casos a mano (`lookback=2, top_n=2, keep_n=3, atr_mult=3, atr_n=1`). Fechas 2024-01-30, 01-31, **02-01** (revisión), 02-02. Cierres (velas con `open` = cierre anterior, `high = max`, `low = min`, salvo la indicada):

| | 01-30 | 01-31 | 02-01 | 02-02 |
|---|---|---|---|---|
| A | 100 | 101 | 110 | 111 |
| B | 100 | 100 | 105 | 106 |
| C | 100 | 100 | 102 | 103 |
| D | 100 | 99 | 97 | 96 |

- **Caso S1 (H5):** el 02-01, `mom` = A 0,10 · B 0,05 · C 0,02 · D −0,03. Aptos A, B, C con puestos 1, 2, 3. `entry` = A y B; C ni entra ni sale (puesto 3 ≤ `keep_n`); D `exit = True` (no apto). Vela de A el 02-01 = `(101, 111, 101, 110)` → TR = 10 → `stop_price = 110 − 30 = 80`; `rank(A) = 0,10`. Todo `False` los demás días.
- **Caso S2 (H5, deja de ser apto):** igual, pero C cierra a 99 el 02-01 → `mom = −0,01` → C `exit = True`; A y B igual.
- **Caso S3 (H7):** misma tabla con `rank_by="lowvol"`. Las dos últimas rentabilidades logarítmicas el 02-01 dan `vol` ≈ A 5,33 % · B 3,45 % · C 1,40 % (D ≈ 0,73 %, pero **no es apto y no ocupa puesto**). Puestos entre aptos: C 1, B 2, A 3. `entry` = C y B; A nada; D `exit = True`. Con `keep_n = 2`: A pasa a `exit = True`.
- **Caso S4 (sin mirar al futuro):** calcular con las velas hasta el 02-01 da ese día las mismas filas que con todas.

### 6.3 `tom_etf` (H6)
> **Ojo:** las fórmulas de `entry`/`exit` y los casos C1–C3 de abajo están corregidos por la enmienda E6 (2026-11-12), al final del archivo. Manda la enmienda.
- Función por activo de siempre, `generate_signals(bars, params)`, más el calendario: `params["sessions"]` = `DatetimeIndex` con todas las sesiones (pasadas y futuras programadas), que inyecta el runner (no va en el TOML). Backtest: índice de SPY de la caché. En vivo: `get_calendar`.
- `params`: `entry_before_end=1, exit_day=3, atr_mult=3.0, atr_n=20`. `robust_keys = ["entry_before_end", "exit_day", "atr_mult"]` con los valores de §2.
- Con `sessions` agrupadas por año-mes: `quedan` = sesiones posteriores a `t` en su mes; `ordinal` = posición de `t` en su mes (desde 1). `entry = (quedan == entry_before_end) & atr.notna()`; `exit = (ordinal == exit_day)`; `stop_price = close − atr_mult × ATR`; `rank = 0`.
- Truncar `bars` no debe cambiar ninguna fila anterior (el calendario no se trunca): test de look-ahead adaptado.
- TOML: `universe = ["SPY","IWM","EFA"]`, `benchmark = "SPY"`, `replica_universe = ["MDY","EEM","EWJ"]`, resto como 6.2.

Casos a mano (`atr_mult=3, atr_n=1`):
- **Caso C1:** sesiones 2024-01-29, 01-30, 01-31, 02-01, 02-02, 02-05, 02-06. `entry = True` solo el **01-30** (queda una sesión, el 31). `exit = True` solo el **02-05** (tercera sesión de febrero). Vela del 01-30 = `(100, 102, 99, 101)` con cierre anterior 100 → TR = 3 → `stop_price = 101 − 9 = 92`.
- **Caso C2:** con `entry_before_end = 2`, `entry = True` solo el 01-29. Con `exit_day = 2`, `exit = True` solo el 02-02.
- **Caso C3 (festivo):** sesiones 2024-12-27, 12-30, 12-31, 2025-01-02, 01-03, 01-06, 01-07 → `entry` el 12-30; `exit` el 01-06.
- **Caso C4 (sin mirar al futuro):** con `bars` cortado en el 01-30 y el mismo calendario, la fila del 01-30 es idéntica.

### 6.4 Infraestructura necesaria (resumen; detalle en `docs/tareas_sonnet.md`)
1. Kill switch al 15 % en configuración, valores por defecto y textos.
2. Datos: los 9 sectores, los 9 países, `MDY`, `^IRX`; historia desde 1998-12.
3. Tramos múltiples por estrategia (IS, réplica, reservado antiguo, reservado reciente, completa) con guardas de un solo uso y coste por tramo.
4. Señales de panel; calendario para H6.
5. Monos a medida (§3.4).
6. Benchmark de caja y métricas nuevas (relación, CAGR conjunto, 16d).
7. Banda de resultados esperados para el paper (§3.6 b).

## Enmiendas

### 2026-11-12, 02:30 (hora de Madrid) — auditoría crítica, ANTES de ejecutar ningún backtest de H5–H7
Origen: `docs/auditoria_ronda2.md` (cada enmienda cita su hallazgo). En este momento no existe
código de las candidatas, ni datos descargados de sus universos, ni ningún informe suyo.
**Ningún criterio de §4 se suaviza**; E4 y E10 endurecen. Jorge o Fable pueden revertir cualquiera
de estas enmiendas solo antes del primer backtest IS de la ronda 2.

**E1 (hallazgo M1) — papel del tramo reservado antiguo.** En §3.1, donde dice "Prueba principal
en backtest", léase: "**veto y coherencia en otro régimen de mercado**". Las muestras de los
trabajos que motivan H5–H7 cubren en todo o en parte 2000–2007, así que ese tramo no es virgen
para las ideas, solo para este proyecto; para H6, el tramo posterior a la publicación es el IS.
Ningún peldaño de backtest "demuestra": todos pueden vetar. La única prueba limpia es el paper
(§3.6). Los criterios de §4.C no cambian.

**E2 (M2) — orden entre candidatas.** Primero se completa la parte A (IS) de **las tres**
candidatas. Después, **un único commit** congela parámetros y `f` de todas las que sigan vivas.
Solo entonces empieza el peldaño 1 de cualquiera. Tras ese commit no se ejecuta ningún IS más.
Los peldaños 1–3 se recorren candidata por candidata en el orden H5, H6, H7. Se declara que los
tramos reservados de H7 no son independientes de los de H5 (mismos 9 sectores).

**E3 (M3) — réplica a ciegas y contaminación.** Del informe de la réplica solo se leen las
cifras del criterio 15 (expectancy, Sharpe, percentil frente a los monos) y el nº de
operaciones, hasta que la candidata haya terminado los peldaños 2–3 o haya muerto. El script
escribe esas cifras en un archivo aparte (`criterio15.md`) y el detalle en otro que no se abre
antes. Si una candidata muere en la réplica, sus tramos reservados no ejecutados **no** se
consideran intactos para esa familia de ideas: se anota en el inventario de contaminación de la
ronda siguiente.

**E4 (A1) — segundo tipo de mono para H5 y H7; criterios 14 y 15 contra los dos.**
Los monos de §3.4 ("sorteo mensual") rotan mucho más que la candidata, porque la salida depende
del puesto y el puesto se sortea de nuevo cada mes. Se mantienen y se añade:
- **Mono persistente:** al empezar cada simulación se sortea una permutación `π` de los símbolos
  del universo **sin puntos fijos** (ningún símbolo se queda en su sitio; se vuelve a sortear
  hasta que salga una así). En cada revisión `t`, el filtro `apto` de cada activo `i` es **el
  suyo** (sin cambios), pero su `clave` para ordenar es la clave verdadera del activo `π(i)` en
  `t` (`mom` en H5, `−vol` en H7; si es NaN, va el último). `puesto` y `rank` salen de ahí;
  empates por símbolo. Todo lo demás (stops, tamaños, costes, `top_n`, `keep_n`) es idéntico.
  Pregunta que contesta: con **la misma rotación** que la candidata, ¿importa que el orden sea
  el del propio activo?
- **Criterio 14:** p < 0,02 en Sharpe IS frente a los monos de sorteo mensual **y** frente a los
  persistentes (1.000 de cada tipo, semilla 42).
- **Criterio 15:** percentil ≥ 75 frente a los dos tipos.
- En §5 (desempates por "menor p en el criterio 14") se usa el **mayor** de los dos p de cada
  candidata.
- H6 no cambia: su mono no tiene este problema.

**E5 (B7) — sorteo de los monos de H6, definición exacta.** En cada mes `m` se sortea, con
probabilidad uniforme entre todas las sesiones de `m`, la **sesión de compra** `c` (la misma para
los 3 activos). La señal es la sesión anterior a `c` en el calendario (de ella salen el ATR y el
stop, como en la candidata). Se vende en la apertura de la 4.ª sesión posterior a `c` (igual que
la candidata: compra en la última sesión del mes, vende en la apertura de la 4.ª del siguiente).
Si `c` es anterior a la sesión de venta del mono del mes previo, se repite el sorteo de ese mes
(si `c` coincide con ella, vale: las salidas van antes que las entradas). Así cada mono hace,
como la candidata, una ventana por mes sin solapes. En el último mes del tramo solo se sortea
entre las sesiones cuya venta cabe en el tramo.

**E6 (A2, A3) — `tom_etf`: mes completo y salida sostenida.** Sustituye a las fórmulas de
entrada y salida de §2 (H6) y §6.3, y a los resultados esperados de C1–C3:
- `completo_t` = el calendario `sessions` contiene alguna sesión de un mes **posterior** al de `t`.
  Si no, no se puede saber cuántas sesiones quedan en el mes de `t`.
- `entry_t = completo_t & (quedan_t == entry_before_end) & atr.notna()`.
- `exit_t = (ordinal_t ≥ exit_day) & ~(completo_t & (quedan_t ≤ entry_before_end))`.
  En palabras: "si lo tienes, véndelo" es verdadero desde la sesión `exit_day` del mes hasta la
  víspera de la señal de entrada, no un solo día.
- Con datos completos las operaciones son **las mismas** que con la regla original (la primera
  señal de venta es la del día `ordinal == exit_day`; las siguientes no encuentran posición).
  Solo cambia si ese día falta la vela del símbolo o, en paper, el script no se ejecuta: se vende
  en la siguiente apertura en lugar de esperar un mes.
- `entry` y `exit` nunca son verdaderos el mismo día.
- En vivo, el calendario se pide siempre hasta el final del mes **siguiente**. Si `sessions`
  falta o no contiene todas las fechas de `bars`, la función lanza un error (no deduce el
  calendario de las propias velas).
- Casos corregidos (comprobados con un script sobre fechas sintéticas, sin datos de mercado):
  - **C1:** `entry` solo el 01-30. `exit` el **02-05 y el 02-06**.
  - **C2:** con `entry_before_end = 2`: `entry` solo el 01-29. Con `exit_day = 2`: `exit` el
    02-02, el 02-05 y el 02-06.
  - **C3:** `entry` el 12-30; `exit` el **01-06 y el 01-07**.
  - C4 no cambia. C5–C9 nuevos en `docs/tareas_sonnet.md` (R2-15).

**E7 (M8) — día de revisión de H5/H7.** "Índice común" (§6.2) = **unión** de los índices de los
símbolos del universo. Día de revisión = primera fecha de cada mes en esa unión; la primera fecha
de la unión no es día de revisión. Un símbolo sin vela en el día de revisión no tiene fila: ni
entra, ni sale, ni ocupa puesto ese mes (si está en cartera, sigue con su stop hasta la revisión
siguiente). La verificación de datos (R2-3) cuenta cuántas veces pasa en cada universo y Fable
lo lee antes del primer IS; si pasa en el universo principal, se para y se decide por enmienda.

**E8 (M7) — qué regla de inicio aplica a cada universo.**
- H5/H7, universo principal: los **9** sectores deben tener ≥ 365 velas al inicio del peldaño. Si
  no, se retrasa el inicio (regla de §3.1), con enmienda previa.
- H6, universo principal: basta con que `SPY` cumpla; `IWM` y `EFA` entran escalonados cuando
  tienen 365 velas, como dice su ficha. Consecuencia declarada: al principio del tramo antiguo
  H6 opera con uno y luego con dos activos (exposición máxima de un tercio y de dos tercios).
- Réplicas: entrada escalonada (`EEM`); no se retrasa el inicio.

**E9 (M5) — criterio 17 en los casos raros.** (a) Además de lo escrito, 17, 17-IS y 17d exigen
CAGR de la estrategia **> 0** en ese tramo. (b) Si la relación de SPY es ≤ 0 y se cumple (a), la
casilla es "sí". (c) Si la caída máxima de la estrategia es 0 y hay al menos una operación
cerrada, la relación se toma como infinita. (d) Sin operaciones cerradas en el tramo: "no".

**E10 (M6) — la caja se mide en rentabilidad, no en tipo de descuento.** Si la serie usada
(`^IRX` o `DTB3`) cotiza como tipo de descuento `d` (en tanto por uno), se convierte antes de
capitalizar: `y = 365 × d / (360 − 91 × d)`. Sonnet documenta, con la fuente, en qué base viene
la serie que use. Alternativa válida sin conversión: `DGS3MO` de FRED, si su ficha confirma que
ya viene como rentabilidad. En caso de duda se aplica la conversión (es la lectura más exigente
para la candidata).

**E11 (B5) — coste en la ejecución completa.** Cada compra o venta paga el slippage que
corresponde a **su fecha** (10 pb hasta el 2007-06-30 inclusive, 5 pb desde el 2007-07-01). Una
operación abierta antes y cerrada después paga 10 pb al entrar y 5 pb al salir. El riesgo por
unidad al dimensionar usa el coste vigente en la fecha de entrada para los dos lados.

**E12 (B6) — criterios de la cartera combinada de §5.4.** Se ejecuta una vez en el reservado
antiguo, en el reciente y en la ejecución completa (no en IS ni en réplica). Debe cumplir: 12,
16b y 17 en cada tramo reservado; 16a; y 4, 16d y 17d en la completa. Además, lo ya escrito
(relación en la completa mayor que la de la preferida sola). `top_n` y `keep_n` no cambian: con 2
huecos, entran los dos primeros por `rank` que encuentren hueco.

**E13 (B8) — comprobaciones de datos.** La prohibición de "calcular rentabilidades de los
símbolos nuevos" se precisa. **Permitido y obligatorio**, sobre todos los símbolos nuevos y sobre
la historia nueva de los antiguos: (a) lista de fechas con variación de cierre a cierre mayor del
±20 % (solo fecha, símbolo y si coincide con un split conocido; sirve para detectar splits mal
ajustados: ver los de `docs/auditoria_ronda2.md` §6); (b) el contraste yfinance ↔ Alpaca del
tramo común con `scripts/check_alpaca_vs_yf.py`, como en la ronda 1 (compara fuentes entre sí);
(c) velas ausentes en días de revisión y en días de señal de H6; (d) operabilidad en Alpaca.
**Sigue prohibido:** cualquier rentabilidad acumulada, media, ranking o gráfico de un símbolo o
periodo, y cualquier ejecución de las reglas de H5–H7 sobre datos reales.

**Requisito previo del primer IS (recordatorio, no cambia nada):** R2-1 (kill switch al 15 % en
código y configuración) y R2-3 (datos verificados) hechos, y la auditoría del motor repetida
sobre el código nuevo.

### 2026-11-12, 10:05 (hora de Madrid) — precisiones de implementación, ANTES de ejecutar ningún backtest de H5–H7
Origen: `docs/especificaciones_ronda2.md` §0.1 (D1–D14). Sigue sin existir código, datos ni
informes de las candidatas. **Ningún criterio de §4 se suaviza.**

**E14 — huecos de definición cerrados al escribir las especificaciones.** Lo que cambia la
letra de este documento o de `docs/tareas_sonnet.md`:
- **Rejillas (D1):** los valores de §2 ({95, 126, 158}, {1, 2}, etc.) se escriben literales en
  el TOML. La rejilla automática ±25 % del código daría 94 en vez de 95 y dejaría
  `entry_before_end` solo en {1}.
- **Caja (D3):** el capital crece `(1 + y)^(días naturales / 365,25)` entre sesiones, con el
  tipo de la sesión anterior, en vez de `^(1/252)` por sesión (R2-4). Así una serie constante
  da exactamente su tipo como CAGR; con calendario real la diferencia es de centésimas y va en
  contra de la candidata.
- **Guarda (D4):** el hash de congelación incluye `f`; no hay `--force` para los tramos; hace
  falta `frozen = true` en el TOML para pasar del IS, y con él ya no se ejecuta ningún IS (E2).
- **Monos (D6, D7):** el mono de H6 lleva la misma venta sostenida que la candidata (E6); el
  «repetir el sorteo» de E5 se hace sorteando entre las sesiones válidas (misma distribución).
  p = `(1 + k) / (N + 1)`; un mono sin Sharpe cuenta como «no supera» y sigue en N. Con
  N = 1.000, `p < 0,02` es `k ≤ 19` con esta fórmula y con la proporción simple.
- **Universo incompleto (D10):** en H5/H7, principal y réplica, si un símbolo no tiene 365
  velas al inicio del tramo se para y se decide por enmienda (no se rebaraja el universo).
- **Cartera combinada (D9):** huecos por grupo (sectores ≤ 2, `SPY` ≤ 1; un sector no puede
  usar el hueco de `SPY`) y, en una misma apertura, `SPY` entra el último.
- **Calendario de H6 en backtest (D2):** índice de `SPY` recortado en 2026-10-31; octubre de
  2026 no es mes completo y no genera entrada.
- El resto (D5, D8, D11–D14) son detalles de informe y de código sin efecto sobre las reglas.

### Preguntas abiertas para Jorge tras la auditoría (detalle en `docs/auditoria_ronda2.md` §5)
| # | Decisión | Opción tomada mientras no digas otra cosa | Alternativa |
|---|---|---|---|
| **P14** | H6 con el efectivo al 0 % frente a las letras (amplía P7) | Se deja como está; H6 probablemente no llegue a los criterios 2 y 16. | Juzgar el criterio 16 con el efectivo rindiendo como la caja (suaviza). |
| **P15** | Regla dura 5 cuando venta y compra van a la misma apertura | Se cumple si la exposición tras ejecutarse las órdenes es ≤ 100 %; el ejecutor (paso 5) recorta la compra con un margen del 3 %. | Comprar solo cuando la venta esté ejecutada: obliga a simular la compra una sesión más tarde **desde el primer IS**. |
| **P16** | Operabilidad en Alpaca de los 24 ETFs | Sin verificar en la auditoría (herramienta sin permiso); lo hace R2-3 antes del IS. | — |
