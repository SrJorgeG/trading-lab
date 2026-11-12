# Auditoría crítica del pre-registro de la ronda 2 (H5–H7) — 2026-11-12, 02:30 (hora de Madrid)

> Revisión "a la contra" de `docs/hipotesis_ronda2.md` y de las tareas «Ronda 2» de
> `docs/tareas_sonnet.md`, hecha **antes de que exista ningún backtest de H5–H7**.
> No se ha ejecutado ningún backtest ni se ha abierto ningún dato de precios. Comprobado antes de
> empezar: no hay código de `sector_mom`, `tom_etf` ni `sector_lowvol`, no hay informes suyos en
> `reports/`, y los ETFs sectoriales y de países no están en `data_cache/` (solo aparecen como
> nombres en `config/settings.toml`).
> No es asesoramiento financiero. Solo paper.

**Sobre los números de este documento.** No hay ninguna cifra de rentabilidad medida. Lo que
aparece es: (a) cifras de la ronda 1 copiadas de `docs/veredicto.md` con su informe; (b) fechas
de lanzamiento y de splits con su fuente web (§6); (c) aritmética sobre los **precios inventados**
de los ejemplos del pre-registro, marcada como tal; (d) recuerdos de literatura o de mercado,
marcados "de memoria, no medido". Nada de (c) ni (d) es un resultado.

Glosario mínimo: **look-ahead** = usar sin querer datos del futuro. **Grado de libertad oculto**
= una decisión que se podría tomar de varias formas después de ver resultados y elegir la que
más conviene. **Monos** = simulaciones al azar contra las que se compara la candidata.
**Tramo reservado** (*holdout*) = datos que no se miran hasta el final.

## 1. Veredicto de la auditoría (para Jorge, sin jerga)

- **El pre-registro es sólido y se puede seguir adelante.** No hay ningún fallo crítico: ninguna
  regla dura se rompe en el diseño, no he encontrado ningún uso de datos del futuro en las reglas
  y los criterios están escritos antes de ver nada.
- He encontrado **4 problemas de gravedad alta, 9 de gravedad media y 8 de gravedad baja**. Trece
  correcciones están ya aplicadas como enmiendas con fecha (ninguna suaviza un criterio; varias
  lo endurecen). Tres cosas necesitan que **tú** decidas (§5).
- Lo más importante que debes saber: **H6 (cambio de mes) tiene muy pocas posibilidades de
  aprobar tal como están los criterios**, no porque la idea sea mala sino porque pasa el 80 % del
  tiempo con el dinero parado al 0 % y se le exige ganar a las letras del Tesoro. Y el examen
  contra el azar de H5/H7 estaba, sin querer, inclinado a favor de las candidatas; ya está
  corregido.

## 2. Hallazgos por gravedad

Estado: **ENMENDADO** (corregido ya, ver §4) · **JORGE** (necesita tu decisión, §5) ·
**AVISO** (no se cambia nada; hay que saberlo) · **SONNET** (tarea añadida).

### Críticos
Ninguno.

### Altos

**A1. Los monos de H5 y H7 no solo barajan la selección: también rotan mucho más que la
candidata. — ENMENDADO (E4)**
El §3.4 sortea el orden de los sectores aptos **de nuevo cada mes**. Pero la regla de salida
depende de ese orden (`puesto > 5` → vender). Con los 9 sectores aptos, un mono vende cada
posición con probabilidad 4/9 ≈ 44 % cada mes (pura combinatoria), mientras que un orden real por
fuerza de 6 meses, y más aún uno por volatilidad, cambia despacio. Los monos pagan por tanto
bastantes más costes y reinician stops y tamaños mucho más a menudo. La comparación deja de medir
"¿elegir por fuerza es mejor que elegir al azar?" y pasa a medir en parte "¿rotar poco es mejor
que rotar mucho?". El sesgo de los costes va **a favor de la candidata**, justo en el criterio que
mató a H2. (El propio pre-registro esperaba lo contrario para H7: "los monos pueden parecerse
mucho a ella"; con este sorteo no se parecen.)
*Corrección:* se añade un segundo tipo de mono, "persistente": usa el orden real pero **de otro
sector** (permutación fija de etiquetas por simulación, sin que ningún sector use el suyo). Tiene
la misma rotación que la candidata y ninguna información sobre el activo. El criterio 14 exige
p < 0,02 contra **los dos** tipos; el 15, percentil ≥ 75 contra los dos. Solo endurece.

**A2. Los casos a mano C1 y C3 de H6 se contradicen con su propia fórmula, y la fórmula miraría
un "fin de mes" que no puede conocer. — ENMENDADO (E6)**
`entry = (quedan == 1)` cuenta las sesiones que quedan en el mes **según el calendario
inyectado**. Si el calendario se acaba a mitad de mes, la penúltima fecha del calendario parece
"penúltima sesión del mes". En C1 (calendario hasta el 02-06) la fórmula da `entry = True` también
el 02-05, y C1 dice "solo el 01-30". En C3 da `entry` **y** `exit` el 01-06, que §6.1 prohíbe.
En el backtest el fallo aparecería al final de cada tramo; en vivo, si alguien pide el calendario
"hasta hoy", compraría casi cada día.
*Corrección:* un mes solo cuenta como completo si el calendario contiene alguna sesión de un mes
posterior; en un mes no completo nunca hay `entry`. Con eso C1–C3 quedan bien en cuanto a
entradas.

**A3. H6 no tiene salida de emergencia: si falla el día de la señal de venta, la posición se
queda un mes entero. — ENMENDADO (E6)**
`exit = (ordinal == 3)` es verdadero **un solo día**. Si ese día el símbolo no tiene vela
(posible en los primeros años de `EFA`, `EEM` o `EWJ`) o, en paper, el script no se ejecuta, no
hay otra señal de venta hasta el mes siguiente. Sería una posición de bolsa de un mes que ninguna
regla escrita cubre (regla dura 8).
*Corrección:* `exit` es verdadero **todos** los días desde la 3.ª sesión hasta la víspera de la
señal de entrada ("si lo tienes, véndelo"). Con datos completos da exactamente las mismas
operaciones que la regla original; solo cambia cuando algo falla. Casos C1–C3 actualizados y
C5–C7 nuevos.

**A4. H6 tiene los criterios 2 y 16 casi fuera de alcance por construcción. — JORGE (P14)**
No es un error del pre-registro (aplica tu decisión de "claramente por encima de la caja"), pero
conviene verlo antes y no después:
- H6 está comprada unas 4 sesiones al mes. Con los precios inventados del ejemplo (81 % de
  exposición durante la ventana), para sacar un 3 % anual necesita ganar de media
  3 / (12 × 0,81) ≈ **0,31 % neto por ventana**, es decir ≈ 0,41 % bruto con 5 pb por lado.
  El criterio 2 (0,10 R) pide casi lo mismo: 0,10 × 3 ATR ≈ 0,30 % con el ATR del ejemplo.
  (Aritmética sobre supuestos, no un resultado.)
- En el tramo reservado antiguo es peor: `IWM` y `EFA` no cumplen las 365 velas hasta
  ≈ finales de 2001 y ≈ principios de 2003 (estimado desde sus fechas de lanzamiento, §6; lo
  confirmará R2-3). Mientras solo está `SPY`, el tope de equity/3 deja la exposición en ≤ 33 %:
  haría falta ≈ 0,76 % neto por ventana para un 3 % anual, más 10 pb por lado de coste. Y en esos
  años las letras rendían bastante (de memoria, no medido: entre el 1 % y el 6 % según el año).
- Además el stop de 3 ATR fija cuánto vale "R": con un stop tan lejano para una posición de 4
  días, la misma ganancia en dólares son menos R. El criterio 2 depende de esa elección.
Lo honrado es decirlo: H6 solo aprueba si el efecto sigue vivo con toda la fuerza que le
atribuyen los trabajos antiguos. Si muere, no será una sorpresa ni un motivo para retocar.

### Medios

**M1. El "tramo reservado antiguo" (2000-07 → 2007-06) no es terreno virgen para las ideas, solo
para este proyecto. — ENMENDADO (E1)**
El §3.1 lo llama "prueba principal en backtest". Pero las tres ideas vienen de trabajos cuyas
muestras cubren esos años (de memoria: McConnell y Xu llegan hasta mediados de los 2000; el
trabajo de Faber sobre fuerza relativa llega hasta 2009; los de baja volatilidad hasta
2006–2012). Es decir: las hipótesis se eligieron, en parte, **porque** funcionaron ahí. Para H6
los papeles están invertidos: el tramo posterior a la publicación es el IS (2007–2020), y el
"reservado" es donde ya se sabía que el efecto existía.
*Corrección:* se cambia la descripción del papel, no los criterios: ningún peldaño de backtest
demuestra nada; el antiguo sirve de veto y de coherencia en otro régimen de mercado. La única
prueba limpia sigue siendo el paper.

**M2. No estaba escrito en qué orden se prueban las tres candidatas. — ENMENDADO (E2)**
"Antes del peldaño 1 se congelan parámetros y `f`" se podía leer candidata por candidata. Así,
H5 podría recorrer sus tramos reservados y **después** calibrarse el riesgo de H7, que usa los
mismos 9 sectores: H7 se congelaría habiendo visto ya esos años. *Corrección:* todo el IS de las
tres y un único commit de congelación antes de que ninguna toque un peldaño 1–3.

**M3. La réplica enseña los tramos reservados antes de tiempo. — ENMENDADO (E3)**
La réplica (peldaño 1) recorre 2000-07 → 2026-10 con activos muy parecidos a los principales
(`MDY` frente a `SPY`/`IWM`; países frente a sectores), antes de los peldaños 2 y 3. Como todo
está ya congelado no permite retocar nada, pero (a) si la candidata muere en la réplica, sus
tramos reservados **no** quedan "intactos" como dice §3.1: ya se ha visto cómo fue esa familia en
esos años; y (b) el criterio 15 incluye los años del IS, donde la candidata ya ha pasado con
activos muy correlacionados, así que es más fácil de lo que parece.
*Corrección:* informe de réplica "a ciegas" (solo las cifras del criterio 15 hasta terminar los
peldaños 2–3) y anotación obligatoria en el inventario de contaminación. El punto (b) queda como
aviso: la réplica ya se declara "no independiente".

**M4. El criterio 17 solo aprieta de verdad en 2021–2026. — AVISO**
La relación rentabilidad/caída de SPY es muy baja en cualquier tramo que contenga 2008 o
2000–2002. Con las cifras de la ronda 1: SPY en IS 9,08 / 55,19 ≈ 0,16 (`H2-IS`); en 2007–2026
10,64 / 55,19 ≈ 0,19 (`H4-FULL`); en 2021–2026 14,65 / 24,50 ≈ 0,60 (`H4-OOS`). Una candidata
calibrada a caída ≤ 12 % supera 0,16 con un CAGR del 2 %, menos de lo que ya pide el criterio 16.
En el tramo antiguo pasará lo mismo (de memoria, no medido: la bolsa estaba a mediados de 2007
más o menos donde a mediados de 2000). Por tanto "mejor relación que comprar y mantener" se
decide casi solo en 2021–2026, el tramo que el propio pre-registro declara contaminado y "solo
veto". No se cambia (es tu decisión tal cual), pero el criterio que manda en los demás tramos es
el 16.

**M5. El criterio 17 no estaba definido en los casos raros. — ENMENDADO (E9)**
Con CAGR negativo la relación engaña (perder un 1 % con caída del 2 % da −0,5, "peor" que perder
un 5 % con caída del 50 %). Y sin caída hay división por cero. *Corrección:* reglas explícitas.

**M6. La "caja" podía quedar medida por lo bajo. — ENMENDADO (E10)**
`DTB3` de FRED es un tipo "de descuento" (así se titula la serie, §6) y `^IRX` muy probablemente
también (no lo he podido confirmar en la web). Un tipo de descuento es algo menor que la
rentabilidad real de la letra: con un 5 % de descuento a 91 días, la rentabilidad es ≈ 5,13 %.
Usarlo sin convertir haría el criterio 16 un poco más fácil. *Corrección:* convertir.

**M7. Regla de "si el dato no existe, se retrasa el inicio" contra "cada activo entra con 365
velas". — ENMENDADO (E8)**
Para H6 las dos reglas chocan (`IWM` y `EFA` no existen con 365 velas el 2000-07-01 y el propio
texto dice que "entran más tarde"). Quedaba a elegir después. *Corrección:* se fija cuál aplica a
cada universo.

**M8. Día de revisión de H5/H7 y símbolos sin vela ese día. — ENMENDADO (E7)**
§2 define el día de revisión por activo; §6.2 por "índice común", sin decir si es unión o
intersección, ni qué pasa si un símbolo no cotizó ese día. *Corrección:* unión de índices;
sin vela no hay señal; se cuentan los casos antes del IS.

**M9. Regla dura 5 (sin margen) en la apertura real. — JORGE (P15)**
El simulador vende primero y compra después "en la misma apertura", con el dinero de la venta y
con el precio de apertura ya conocido. En Alpaca las dos órdenes se envían antes de abrir: la
compra se dimensiona con el cierre anterior y sin que la venta se haya cobrado. Con H7 al 92 %
de exposición o tres posiciones en el tope de equity/3, una apertura con hueco al alza puede
costar más que la caja disponible, y una cuenta paper (que tiene margen) lo cubriría con margen.
No afecta al backtest, pero sí a la fidelidad del paper (§3.6 a) y a la regla 5. Ver §5.

### Bajos

- **B1. Universo de réplica elegido "de los que recuerdo". — AVISO.** En marzo de 1996 salieron
  17 ETFs de países (§6), no 9. Los 6 del G7 son una regla objetiva; `EWA`, `EWL` y `EWH` se
  eligieron de memoria. Es un grado de libertad pequeño, tomado sin ver datos. No lo cambio:
  cambiarlo ahora con **mi** memoria añadiría otro. Queda declarado.
- **B2. "El universo es el mismo en todos los tramos" no es del todo cierto. — AVISO.** Los 9
  tickers son los mismos, pero su contenido cambió: `XLRE` se separó de `XLF` y en 2018 `XLC` se
  llevó empresas de `XLK` y `XLY` (§6). Limitación a declarar en el informe.
- **B3. Rejilla de H6 con un solo lado en `entry_before_end` ({1, 2}). — AVISO.** El vecino que
  falta (entrar un día más tarde) es exactamente la prueba de "retraso de 1 vela" (criterios
  8-IS y 8), así que está cubierto.
- **B4. Monte Carlo (criterio 10) flojo para H6. — AVISO.** Barajar operaciones sueltas trata
  como independientes las tres operaciones simultáneas de cada mes, que son casi la misma
  apuesta: subestima la caída. Los criterios 4 y 12 (caída real de la curva) no tienen ese
  defecto. Se pide a Sonnet la variante informativa barajando por meses.
- **B5. Coste variable en la ejecución completa. — ENMENDADO (E11).** No decía qué coste paga
  una operación que abre antes del 2007-06-30 y cierra después.
- **B6. Cartera combinada (§5.4): "criterios 4, 12, 16 y 17" sin decir cuáles ni dónde. —
  ENMENDADO (E12).**
- **B7. Sorteo de los monos de H6 sin definir del todo. — ENMENDADO (E5).** No decía qué es "la
  sesión de entrada", ni qué pasa si la ventana sorteada pisa la del mes anterior.
- **B8. Verificación de datos demasiado atada. — ENMENDADO (E13).** La prohibición de "calcular
  rentabilidades" impedía detectar un split mal ajustado, y R2-3 no pedía el contraste
  yfinance ↔ Alpaca de los símbolos nuevos (en la ronda 1 era obligatorio). Hay splits recientes
  que vigilar (§6).

### Lo que he revisado y está bien
- **Look-ahead en las reglas:** `mom`, `vol`, ATR y el día de revisión usan solo datos ≤ t; se
  ejecuta en la apertura de t+1; el calendario bursátil se conoce de antemano. Los cierres no
  previstos (2001-09-11 a 14, que cae en el tramo antiguo; el huracán de 2012; funerales de
  Estado) no cambian cuál es la última sesión de un mes: afectan, como mucho, al sorteo de los
  monos de H6. Sin efecto práctico.
- **Simulador** (`portfolio_sim.py`, leído): las salidas se ejecutan antes que las entradas en la
  misma apertura; una señal de entrada sobre un activo que ya se tiene se ignora (ni se amplía la
  posición ni se mueve el stop); una entrada sin hueco se descarta. Es lo que el pre-registro
  supone. Faltaban tests que lo fijen (añadidos a las tareas).
- **Reglas duras en el diseño:** stop definido antes de entrar en las tres; riesgo ≤ 1 % con
  costes; ≤ 3 posiciones; la caja nunca queda negativa en el simulador, luego exposición ≤ 100 %;
  sin cortos ni opciones; kill switch al 15 % con calibración al 12 %. El código aún tiene el
  10 % por defecto en seis sitios: R2-1 lo cubre y ahora es requisito previo explícito del IS.
- **Aritmética:** rehechos a mano los tres ejemplos de tamaño (H5, H6, H7) y los casos S1–S3:
  correctos.
- **Puerta trasera para H4:** no la hay (suspendería también el criterio 17 nuevo).

## 3. Huecos en las tareas de Sonnet (casos a mano que faltaban)

Añadidos a `docs/tareas_sonnet.md` como R2-14 a R2-18, con los números de cada caso. Resumen:

| Qué faltaba | Por qué importa |
|---|---|
| Empates, menos aptos que huecos, ningún apto, historia insuficiente (S5–S7) | Son los caminos del código que más se rompen y S1–S4 no los tocan. |
| Fuga entre símbolos: envenenar el futuro de **otro** activo (S8) | El test de look-ahead heredado trunca un activo cada vez; una señal de panel puede filtrar el futuro por el ranking. |
| Símbolo sin vela el día de revisión (S9) | Enmienda E7. |
| Simulador: hueco que conserva el puesto 4–5, entrada descartada sin cola, rotación en la misma apertura, señal repetida que no mueve el stop (S10–S12) | El pre-registro lo da por hecho; solo había un test pedido. |
| H6: mes incompleto, salida de emergencia, vela ausente, calendario ausente, operación completa de punta a punta con su resultado a mano (C5–C9) | Enmienda E6 y el fallo A2. |
| Monos: "mono con el orden verdadero = candidata exacta", igualdad con ≤ 3 aptos, mono persistente, sorteo de H6 sin solapes | Sin el test de identidad no se sabe si el mono cambia **solo** lo que dice cambiar. |
| Métricas: relación con CAGR ≤ 0 y con caída 0; CAGR conjunto 16a con números a mano; conversión de la caja; umbral del kill switch en el borde y techo del 15 % | Fórmulas nuevas sin ningún caso a mano. |
| Tramos: guarda de un solo uso, orden obligado, coste por fecha en el cambio 2007-06-30/07-01, IS que no puede tocar fechas fuera del IS | La guarda es lo que protege los tramos reservados. |
| Datos: saltos de precio de un día, contraste con Alpaca, velas ausentes en días de señal, operabilidad en Alpaca | Enmienda E13. |

## 4. Enmiendas aplicadas (todas antes del primer backtest)

Texto completo en `docs/hipotesis_ronda2.md`, «Enmiendas», 2026-11-12. Ninguna suaviza un
criterio. Jorge o Fable pueden revertir cualquiera **antes** del primer IS de la ronda 2.

| # | Qué | Efecto |
|---|---|---|
| E1 | Papel del tramo antiguo: veto y coherencia, no "prueba principal" | Solo interpretación |
| E2 | Orden: IS de las tres y un único commit de congelación antes de cualquier peldaño 1–3 | Procedimiento |
| E3 | Réplica a ciegas + anotar la contaminación | Procedimiento |
| E4 | Monos persistentes; criterios 14 y 15 contra los dos tipos | **Endurece** |
| E5 | Definición exacta del sorteo de los monos de H6 | Aclara |
| E6 | H6: mes completo para `entry`; `exit` sostenido; casos C1–C3 corregidos | Corrige; mismas operaciones con datos completos |
| E7 | Día de revisión = unión de índices; sin vela no hay señal | Aclara |
| E8 | Qué regla de inicio aplica a cada universo | Aclara |
| E9 | Criterio 17 con CAGR ≤ 0 y con caída 0 | Aclara (lectura más dura) |
| E10 | Caja en rentabilidad real, no en tipo de descuento | **Endurece** un poco |
| E11 | Coste según la fecha de cada compra o venta | Aclara |
| E12 | Criterios exactos de la cartera combinada | Aclara (lectura más dura) |
| E13 | Qué comprobaciones de datos se permiten y se exigen | Procedimiento |

## 5. Preguntas para Jorge (decidir antes del primer backtest IS)

**P14. H6 y el efectivo parado (amplía P7).**
Tal como está, el dinero fuera del mercado rinde 0 % y a H6 se le exige batir a las letras.
- (a) **Dejarlo así** y aceptar que H6 probablemente muera. El informe ya dará, solo como
  información, cómo quedaría con el efectivo rindiendo como la caja.
- (b) Juzgar los criterios 16 con el efectivo rindiendo como las letras. Sería suavizar, y en la
  cuenta paper el efectivo no rinde nada.
- **Recomendación: (a).** Es lo que pasa de verdad en la cuenta y es coherente con "no bajar el
  listón". H6 cuesta poco de implementar y, si muere, se aprende igual.

**P15. Regla dura 5 en la apertura (hallazgo M9).** ¿Qué significa "nunca usar el margen" cuando
la venta y la compra de una rotación van a la misma apertura?
- (a) **Se cumple si, una vez ejecutadas las órdenes, la exposición es ≤ 100 %**; las dos órdenes
  se envían a la vez y, en el paso 5, el ejecutor recorta la compra si
  `posiciones resultantes valoradas al cierre anterior × 1,03 > equity` (recorte documentado
  como diferencia frente al backtest).
- (b) Lectura estricta: no comprar hasta que la venta esté ejecutada. Entonces la compra de una
  rotación se haría una sesión más tarde, y **el backtest tendría que simularlo así desde el
  principio** (cambia H5 y H7).
- **Recomendación: (a).** Mantiene el backtest como está y la exposición real nunca pasa del
  100 %. Si prefieres (b), hay que decirlo antes del primer IS.

**P16. Operabilidad en Alpaca: pendiente de comprobar.** En esta sesión la herramienta de Alpaca
no tenía permiso, así que **no he comprobado símbolo a símbolo** que los 24 ETFs sean operables
(la doc de Alpaca dice que se mira en el campo `tradable` de cada activo, §6). Son ETFs grandes
de bolsas de EE. UU. y no hay motivo para dudar, pero no lo he verificado. Queda en R2-3
(`get_asset`), con la regla ya escrita: símbolo de réplica no operable → se quita sin sustituir;
símbolo principal no operable → parar y preguntar.
- **Recomendación:** nada que decidir ahora; solo que R2-3 se haga antes del IS.

## 6. Verificación de los ETFs (fuentes web, consultadas el 2026-11-12)

| Símbolos | Dato del pre-registro | Verificado | Fuente |
|---|---|---|---|
| `XLB XLE XLF XLI XLK XLP XLU XLV XLY` | "existen desde diciembre de 1998" | ✔ Lanzamiento el 1998-12-16 de los nueve originales; la ficha de `XLI` de State Street da 1998-12-22 como fecha en bolsa (primera vela esperable). Con primera vela el 12-22, la vela 365 cae a primeros de junio de 2000 (cuenta de calendario mía, a confirmar con los datos): antes del 2000-07-01, con unas 20 sesiones de margen. | [ETF Action](https://www.etfaction.com/the-ultimate-trading-tools-an-etf-story-about-the-select-sector-spdrs/) · [State Street, XLI](https://www.ssga.com/uk/en_gb/intermediary/etfs/state-street-industrial-select-sector-spdr-etf-xli) · [Market Chameleon, XLV](https://marketchameleon.com/Overview/XLV/ETFProfile) |
| `XLRE`, `XLC` (excluidos) | 2015 y 2018 | ✔ `XLRE` sale de `XLF` (2015); `XLC` nace del cambio de clasificación sectorial de 2018 | [ETF Action](https://www.etfaction.com/the-ultimate-trading-tools-an-etf-story-about-the-select-sector-spdrs/) |
| `EWJ EWG EWU EWC EWQ EWI EWA EWL EWH` | "lanzados en 1996" | ✔ para la serie: 17 fondos de países (WEBS) empezaron a cotizar el 1996-03-12 y los 17 seguían vivos en 2015; rebautizados iShares MSCI en 2000. Fecha por símbolo confirmada solo en `EWQ`; los otros ocho se deducen de la serie (a confirmar con la primera vela). | [SEC, informe de 1996](https://www.sec.gov/Archives/edgar/data/0000930667/000093506996000124/0000935069-96-000124.txt) · [ETFdb](https://etfdb.com/international-etfs/single-country-etfs-many-returns/) · [Market Chameleon, EWQ](https://marketchameleon.com/Overview/EWQ/ETFProfile/) · [IPE](https://ipe.com/webs-become-ishares/13543.article) |
| `MDY` | (sin fecha en el pre-registro) | ✔ 1995-05-04 | [State Street, MDY](https://www.ssga.com/us/en/institutional/etfs/state-street-spdr-sp-midcap-400-etf-trust-mdy) |
| `IWM` | "~2000-05" | ✔ mayo de 2000 (las fuentes dan el 21, el 22 o primera vela el 26) | [etfreplay](https://www.etfreplay.com/summary?Id=1) · [finspry](https://finspry.com/etf/issuers/blackrock) |
| `EFA` | "~2001-08" | ✔ 2001-08-14 (una fuente da el 13) | [ETFdb](https://etfdb.com/etfs/country/eafe/) |
| `EEM` | "≈ 2004 con 365 velas" | ✔ lanzado en abril de 2003 (6–7); 365 velas ≈ otoño de 2004 | [finspry](https://finspry.com/etf/issuers/blackrock) |
| `IEF` | "~2002-07" | ✔ julio de 2002 (21–22) → el 2002-08-01 del criterio 16d vale | [etfreplay](https://www.etfreplay.com/summary?Id=1) |
| `SPY` | "desde 1993" | No buscado en esta sesión (ya está en la caché del proyecto desde la ronda 1) | — |

**Splits que el ajuste de precios debe recoger** (si no, aparecería un salto falso de ±50 % o más):

| Símbolos | Qué | Cuándo | Fuente |
|---|---|---|---|
| `XLK XLY XLE XLU XLB` | Split 2 por 1 | Cotizan al precio nuevo desde el 2025-12-05 | [Business Wire / State Street](https://www.businesswire.com/news/home/20251120957218/en/State-Street-Investment-Management-Announces-Share-Splits-for-Five-Select-Sector-SPDR-ETFs) · [FAQ de State Street](https://www.ssga.com/library-content/products/fund-docs/etfs/us/information-schedules/select-sector-spdr-fund-share-splits-faq.pdf) |
| `EWJ` | Contrasplit 1 por 4 | 2016-11-07 | [SEC, suplemento de iShares](https://www.sec.gov/Archives/edgar/data/0000930667/000119312516737784/d231942d497.htm) · [MIAX](https://www.miaxglobal.com/alert/2016/11/04/miax-corporate-action-alert-ishares-msci-japan-etf-ewj) |
| `EWU`, `EWI` | Contrasplit 1 por 2 | 2016-11-07 | [MIAX, EWU](https://miaxglobal.com/alert/2016/11/04/miax-corporate-action-alert-ishares-msci-united-kingdom-etf-ewu) · [MIAX, EWI](https://miaxglobal.com/sites/default/files/alert-files/EWI_Split_39964.pdf) |

No es una lista completa: es lo que ha salido en la búsqueda. Por eso E13 exige el control de
saltos de un día en todos los símbolos.

**Caja:** `DTB3` de FRED es "3-Month Treasury Bill Secondary Market Rate, **Discount Basis**"
([FRED](https://fred.stlouisfed.org/series/DTB3)). La base de `^IRX` no la he podido confirmar
en la web.

**Operabilidad en Alpaca:** no verificada símbolo a símbolo (ver P16). La doc de Alpaca indica
que cada activo trae los campos `tradable` y `fractionable`
([Alpaca, Get Assets](https://docs.alpaca.markets/us/reference/get-v2-assets-1)).

## 7. Qué no he hecho
- No he ejecutado ningún backtest ni mirado precios.
- No he comprobado en Alpaca los 24 símbolos (herramienta sin permiso).
- No he confirmado la fecha de lanzamiento símbolo a símbolo de 8 de los 9 ETFs de países, ni la
  base de cotización de `^IRX`.
- No he auditado código de H5–H7: todavía no existe. Cuando Sonnet lo entregue, hay que repetir
  la auditoría del motor (fase A) sobre lo nuevo antes del primer IS.
