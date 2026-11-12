# Informe del estudio trading-lab — revisión independiente (2026-11-12, hora de Madrid)

> Revisor: Opus (independiente de Fable y de Sonnet). Para Jorge y su amigo; no hace falta
> saber estadística. Experimento educativo, **solo paper**. No es asesoramiento financiero.
>
> **Sobre las cifras.** Todas salen de ficheros de `reports/` o de documentos que las copian de
> ahí, y llevan su fuente al lado. **No he ejecutado ningún backtest** ni he tocado el OOS ni
> los tramos reservados. Lo único que he ejecutado en esta sesión:
> `uv run ruff check .` → «All checks passed!»; `uv run ruff format --check .` →
> «127 files already formatted»; `uv run pytest -q` → **162 passed, 2 skipped, 2 deselected,
> 22 warnings**. Cuando hago una cuenta con cifras de un informe lo digo («cálculo mío»).

---

## 1. Resumen ejecutivo (una página)

**Qué se buscaba.** 1–2 estrategias con reglas escritas, de velas diarias, que se puedan operar
en la cuenta paper de Alpaca respetando reglas de riesgo muy estrictas: máx. 1 % de riesgo por
operación, stop siempre, máx. 3 posiciones, sin apalancamiento y un freno de emergencia
permanente (kill switch) si se cae un 10 % desde el máximo (15 % desde la ronda 2).

**Qué ha pasado hasta hoy.**
- **Ronda 1 (cerrada): ninguna de las 4 candidatas aprobó → no se opera nada.**
  (`docs/veredicto.md`)
  - H1 (tendencia en cripto): rentable en desarrollo, pero caía demasiado: −22,6 % incluso
    arriesgando la mitad (`reports/donchian_crypto/is_20261111-1613/resumen.md`).
  - H2 (momentum mensual en ETFs): no se distinguía de entrar al azar, p = 0,597
    (`reports/robustez/tsmom_etf_nokill/azar_is_20261111-1634/resumen.md`).
  - H3 (RSI(2), rebote corto): no ganaba nada tras costes; negativa con costes × 2 o con un día
    de retraso (`reports/rsi2_etf/robust_20261111-1624/resumen.md`).
  - H4 (ruptura de 55 días en 7 ETFs): la mejor. Pasó 13 de 14 criterios, pero en el examen
    final (2021–2026) ganó un 3,45 % anual frente al 14,65 % de comprar SPY y no tocarlo, con
    una caída máxima del 7,04 % frente al 24,50 % (`reports/donchian_etf/oos_20261111-1636/resumen.md`).
    Suspendió el criterio de «rentabilidad frente a SPY» y, por regla, murió.
- **El motor de backtest está bien hecho** (auditoría 7/7 en `docs/veredicto.md`; lo he
  releído y estoy de acuerdo en lo esencial). Las diferencias de datos entre yfinance y Alpaca
  son unos pocos días de pánico (marzo de 2020) y no cambian los resultados.
- **Jorge cambió dos cosas para la ronda 2** (enmienda del 2026-11-11 en `CLAUDE.md`): el
  objetivo pasa a ser un «punto medio» (ganar claramente más que las letras del Tesoro y con
  mejor relación rentabilidad/caída que comprar y mantener), y el kill switch sube del 10 % al 15 %.
- **Ronda 2 (en preparación, sin ningún resultado todavía):** tres ideas nuevas pre-registradas
  — H5 rotación por fuerza entre sectores, H6 cambio de mes, H7 sectores más tranquilos —, con
  una auditoría que añadió 14 enmiendas antes de probar nada y unas especificaciones de 1.392
  líneas para que Sonnet las programe (`docs/hipotesis_ronda2.md`, `docs/auditoria_ronda2.md`,
  `docs/especificaciones_ronda2.md`). No hay código de H5–H7 todavía.

**Mi opinión en cuatro frases.**
1. La disciplina es buena de verdad: reglas escritas antes de mirar, un solo examen final,
   todas las variantes anotadas (74 en la ronda 1) y ninguna cifra retocada. Esto es lo más
   valioso del proyecto y lo que más se suele hacer mal.
2. El problema de fondo no es la señal sino la combinación de **kill switch permanente + 1 % de
   riesgo + 3 huecos + efectivo al 0 %**: obliga a ir medio vacío y hace casi imposible ganar
   bastante. La ronda 2 relaja un poco el freno pero endurece casi todo lo demás; el propio
   pre-registro reconoce que lo más probable es volver a «ninguna apta».
3. Hay fallos de trazabilidad y de herramienta que conviene arreglar **antes** del primer
   backtest de la ronda 2 (el candado del OOS no impide repetir, el veredicto cita un commit
   que ya no está en ninguna rama, la prueba contra el azar de la ronda 1 favorecía un poco a
   la estrategia). Ninguno cambia el veredicto de la ronda 1.
4. Recomiendo que Jorge decida ya las preguntas pendientes (P7–P16), sobre todo **P14 (H6 y el
   efectivo parado)**, porque H6 es la candidata que más trabajo de programación cuesta y la que
   la propia auditoría da casi por muerta.

---

## 2. Objetivo, reglas duras y metodología

### 2.1 Objetivo
- Original: estrategias de baja frecuencia, validadas con backtest riguroso, ejecutadas a diario
  en paper por Python puro (no por un LLM). Ronda 1: se exigía, entre otras cosas, acercarse a
  SPY (criterio 3 de `docs/hipotesis.md` §4).
- Desde la ronda 2 (decisión de Jorge, 2026-11-11): «punto medio». Traducido a criterios en
  `docs/hipotesis_ronda2.md` §4: **criterio 16** (CAGR ≥ letras a 3 meses + 2 puntos) y
  **criterio 17** (CAGR / caída máxima mejor que la de SPY).

### 2.2 Reglas duras (de `CLAUDE.md`, no negociables)
| # | Regla | Estado en el código |
|---|---|---|
| 1 | Solo paper | `src/tlab/broker/guard.py` rechaza URL real, `paper=False` o `ALPACA_PAPER_TRADE≠true`; `alpaca_paper.py` siempre pasa por la guardia. Aún no hay código que envíe órdenes. |
| 2 | Riesgo ≤ 1 % del equity con costes | `src/tlab/risk.py` (`position_size` incluye slippage y comisiones de ida y vuelta, redondea hacia abajo). |
| 3 | Stop obligatorio, definido antes | Toda estrategia devuelve `stop_price`; el simulador no entra si la apertura ya está en el stop. |
| 4 | Máx. 3 posiciones | `risk.apply_limits`. |
| 5 | Sin apalancamiento, cortos ni opciones | Exposición ≤ 100 %, caja nunca negativa, tope por posición = equity/3. |
| 6 | Kill switch (−10 % → −15 % desde la ronda 2) | En el simulador sí. El valor por defecto en el código sigue en 10 % (más estricto; tarea R2-1 pendiente). El ejecutor diario que debe comprobar el archivo `KILL_SWITCH` **todavía no existe**. |
| 7–10 | No inventar cifras, reglas escritas, secretos en `.env`, no publicar | Respetadas en los documentos revisados. |

### 2.3 Metodología (en palabras sencillas)
- **Pre-registro:** antes de mirar ningún resultado se escribe qué se prueba, con qué números y
  qué significa «aprobar». Después no se cambia (solo enmiendas fechadas **antes** de ver nada).
- **IS / walk-forward / OOS:** los datos se parten en un tramo de desarrollo (IS, 2007-07 →
  2020-12 en ETFs) y uno reservado (OOS, 2021-01 → 2026-10) que se mira **una sola vez**. El
  walk-forward repite «elige parámetros en el pasado, pruébalos el año siguiente» 8 veces dentro
  del IS.
- **Escalera de 4 peldaños en la ronda 2:** IS → réplica en otros activos → tramo reservado
  antiguo (2000–2007) → tramo reservado reciente (2021–2026, solo puede vetar) → 12 meses de
  paper como examen final (`docs/hipotesis_ronda2.md` §3.1).
- **Costes siempre activados:** ETFs 5 pb de slippage por lado (10 pb en 2000–2007 y 15 pb en
  las réplicas en la ronda 2); cripto 0,25 % de comisión + 20 pb; y una prueba con todo × 2
  (`config/settings.toml`, `docs/hipotesis.md` §3).
- **Azar («monos»):** se simulan 1.000 estrategias que entran al azar con las mismas salidas,
  stops, tamaños y costes. Si la estrategia real no queda claramente por encima, su «ventaja»
  puede ser suerte. Umbral: p < 0,05 en la ronda 1, p < 0,02 en la ronda 2, con monos hechos
  a medida de cada idea.
- **Otras pruebas de robustez:** parámetros vecinos (±25 %), retrasar la entrada un día, quitar
  las 5 mejores operaciones, quitar el mejor activo, Monte Carlo barajando operaciones,
  subperiodos.
- **Presupuesto de variantes:** máximo 40 por candidata (ronda 1) y 30 (ronda 2), todas
  anotadas en `docs/registro_pruebas.md`.

---

## 3. Ronda 1: H1–H4

Todas las cifras de esta sección vienen de `docs/veredicto.md` y de los informes que cita;
he comprobado contra el fichero original las marcadas con ✓.

### 3.1 Las cuatro ideas (de `docs/hipotesis.md` §2)
| | Idea | Universo |
|---|---|---|
| H1 `donchian_crypto` | Comprar al romper el máximo de 55 días, vender al perder el mínimo de 20; stop 2 ATR | BTC, ETH, LTC, BCH |
| H2 `tsmom_etf` | Cada mes, estar en los ETFs que han subido en 12 meses (máx. 3); stop de catástrofe 4 ATR | SPY, EFA, EEM, IEF, GLD, DBC, VNQ |
| H3 `rsi2_etf` | Con tendencia alcista (precio > media de 200), comprar si RSI(2) < 10, vender al superar la media de 5 | SPY, QQQ, IWM, DIA, EFA, EEM |
| H4 `donchian_etf` | La regla de H1 en los 7 ETFs de H2 | Como H2 |

### 3.2 Resultados y por qué murió cada una
**Calibración del riesgo.** Antes de nada, cada candidata debía encontrar un riesgo por
operación (1 %, 0,75 % o 0,5 %) con caída máxima en IS ≤ 10 %, para no disparar el kill switch.

| | Riesgo elegido | Caídas IS con 1 / 0,75 / 0,5 % | Fuente |
|---|---|---|---|
| H1 | ninguno | −32,6 % / −28,3 % / −22,6 % ✓ | `reports/donchian_crypto/is_20261111-1613/resumen.md` |
| H2 | 0,5 % | −17,5 % / −13,8 % / −9,5 % | `reports/tsmom_etf/is_20261111-1613/resumen.md` |
| H3 | 0,5 % | −16,4 % / −13,5 % / −9,9 % | `reports/rsi2_etf/is_20261111-1613/resumen.md` |
| H4 | 0,5 % | −12,7 % / −11,6 % / −9,4 % | `reports/donchian_etf/is_20261111-1613/resumen.md` |

**H1 — murió en IS por el kill switch.** En desarrollo (2015-10 → 2023-06, riesgo 1 %): CAGR
26,84 %, Sharpe 1,03, caída −32,62 %, 66 operaciones; comprar y mantener BTC: CAGR 87,07 %,
caída −83,40 % ✓. Con 0,5 % de riesgo el freno del 10 % habría saltado 8 veces ✓. No murió por
falta de rentabilidad sino por incompatibilidad con el freno. Su OOS (2023-07 → 2026-10)
**sigue sin tocar**.

**H2 — murió en IS por no distinguirse del azar.** Pasó walk-forward (5/8), robustez (8/8),
costes × 2 y retraso, pero contra los monos: Sharpe 0,41, percentil 40 %, **p = 0,597** ✓
(`reports/robustez/tsmom_etf_nokill/azar_is_20261111-1634/resumen.md`). Además, quitando sus
5 mejores operaciones casi no quedaba nada (54,46 $, `reports/tsmom_etf/robust_20261111-1620/resumen.md`).
Solo 43 operaciones en 13,5 años.

**H3 — murió en IS por costes.** Expectancy (ganancia media por operación) de 0,01 R con 490
operaciones; walk-forward 4/8 (50 %, pedía 60 %); con costes × 2, −0,021 R; con un día de
retraso, −0,004 R (`reports/rsi2_etf/is_20261111-1613/resumen.md`,
`reports/rsi2_etf/wf_20261111-1620/resumen.md`, `reports/rsi2_etf/robust_20261111-1624/resumen.md`).

**H4 — llegó al examen final y lo suspendió en 1 de 14 criterios.**

| Tramo | | CAGR | Sharpe | Caída máx. | Operaciones | Fuente |
|---|---|---|---|---|---|---|
| IS 2007-07 → 2020-12 | H4 (0,5 %) | 3,55 % | 0,70 | −9,4 % | 167 | `reports/donchian_etf/is_20261111-1613/resumen.md` |
| | SPY | 9,08 % | 0,52 | −55,19 % | — | ídem |
| OOS 2021-01 → 2026-10 | H4 | 3,45 % ✓ | 0,62 ✓ | −7,04 % ✓ | 89 ✓ | `reports/donchian_etf/oos_20261111-1636/resumen.md` |
| | SPY | 14,65 % ✓ | 0,91 ✓ | −24,50 % ✓ | — | ídem |
| | 60/40 (informativo) | 8,00 % ✓ | 0,78 ✓ | −21,2 % ✓ | — | ídem |
| Completo | H4 | 3,59 % ✓ | 0,69 ✓ | −9,43 % ✓ | 253 ✓ | `reports/donchian_etf/full_20261111-1636/resumen.md` |
| | SPY | 10,64 % ✓ | 0,61 ✓ | −55,19 % ✓ | — | ídem |

- El criterio 3 pedía en OOS Sharpe ≥ 0,5 **y** (Sharpe ≥ SPY, o caída ≤ 60 % de la de SPY
  **y** CAGR ≥ 50 % del de SPY). H4 tenía Sharpe 0,62 y caída 7,04 %, pero CAGR 3,45 % < 7,33 %
  → **suspenso** (`docs/veredicto.md`).
- Lo bueno: walk-forward 7/8 ✓ (`reports/donchian_etf/wf_20261111-1615/resumen.md`), robustez
  23/26, kill switch 0 veces en OOS ✓, estable en los 3 subperiodos.
- Lo malo, que también cuenta: 1.139 días seguidos por debajo de su máximo en OOS ✓; acierta solo
  el 35,96 % de las operaciones ✓; quitando las 5 mejores operaciones del OOS el resultado es
  −560,20 $ ✓; exposición media del 40,3 % ✓ (estaba casi 60 % del tiempo en efectivo al 0 %).
- **Dato que el veredicto no destaca:** en el OOS, de un beneficio total de 2.182,07 $, DBC
  (materias primas) aporta 1.590,17 $ ✓ (`reports/donchian_etf/oos_20261111-1636/resumen.md`);
  es un 73 % (cálculo mío). Sin DBC el OOS queda en 591,90 $ ✓. El examen final se apoyó mucho
  en un solo activo y un solo episodio.

**Balance de la ronda 1:** 4 hipótesis, 74 variantes anotadas, un solo OOS gastado (el de H4,
con sus 2 pruebas de estrés y la ejecución completa anunciadas antes:
`reports/oos_log.csv`, 4 filas con el mismo hash). Nadie retocó nada después de ver resultados.

---

## 4. Calidad del motor y de los datos

### 4.1 El motor
- **Auditoría de Fable (7/7)** en `docs/veredicto.md`: ejecución en la apertura siguiente, sin
  datos del futuro, stops con hueco, costes en entrada y salida, tamaño con costes, benchmark
  con el mismo trato, y estrategias implementadas como dice el pre-registro.
- **Mi relectura** de `src/tlab/backtest/portfolio_sim.py`, `risk.py`, `costs.py`,
  `metrics.py` y `runner.py`: coincido. Puntos fuertes: el orden de eventos de cada vela está
  documentado y es prudente (si el stop y el objetivo caen en la misma vela, gana el stop; se
  comprueba el stop en la propia vela de entrada; el slippage se aplica también al salir por
  stop). Hay tests de «mirar al futuro» que truncan y «envenenan» los datos futuros
  (`tests/test_lookahead.py`) y un test que compara el simulador propio con vectorbt en un caso
  simple (`tests/test_metrics_misc.py::test_engines_agree_single_asset`).
- **Limitaciones conocidas y declaradas** (`docs/veredicto.md`): el tamaño se calcula con la
  apertura real (en vivo se sabrá solo el cierre anterior); acciones enteras sobre precios
  ajustados; efectivo al 0 %; Sharpe con tipo libre de riesgo 0; sin deslizamiento extra en
  días de pánico.

### 4.2 Los datos: yfinance frente a Alpaca
- Alpaca solo tiene acciones/ETFs desde 2016 y cripto desde 2021 (`docs/hipotesis.md` §0), así
  que la historia larga sale de **yfinance** y Alpaca sirve para contrastar y para operar.
- El contraste formal dio **REVISAR en 7 ETFs** (DIA, EEM, EFA, GLD, IWM, SPY, VNQ) ✓
  (`reports/datos/contraste_20261111-1555.md`). Ejemplo: VNQ con correlación 0,9801 y un día con
  957,4 pb de diferencia el 2020-03-17 ✓.
- La investigación (`docs/INVESTIGACION_DATOS.md`, `reports/datos/verificacion_fable_20261111.md`,
  `reports/datos/diag_alpaca_vs_yf_20261111-1655.md`) concluye que no es un problema de ajuste
  por dividendos sino de **unos pocos días de marzo de 2020** con cierres distintos entre
  proveedores. En SPY, por ejemplo, hay 44 días con más de 10 pb de diferencia y solo 3
  coinciden con fechas de dividendo ✓ (`diag_alpaca_vs_yf_20261111-1655.md`). Quitando los 5
  peores días la correlación sube a ≥ 0,9995 en los siete, y las señales coinciden casi siempre
  (`docs/veredicto.md`).
- **Mi valoración:** la decisión de no bloquear es razonable. El riesgo que queda es para el
  paper: en días de pánico Alpaca no reproducirá el backtest exactamente. Para la ronda 2 hay
  un riesgo nuevo que nadie ha medido (ver §6, M6).

---

## 5. Ronda 2: H5–H7 (sin ningún resultado todavía)

### 5.1 Las tres ideas (`docs/hipotesis_ronda2.md` §2)
| | Idea | Universo | Lo que se pone a prueba |
|---|---|---|---|
| H5 `sector_mom` | Cada mes, los 3 sectores que más han subido en 6 meses (si han subido); se suelta uno si cae del puesto 5 | 9 ETFs sectoriales XL* (desde 1998) | ¿Elegir por fuerza es mejor que elegir al azar entre los aptos? |
| H6 `tom_etf` | Comprar en la última sesión del mes y vender en la apertura de la 4.ª del siguiente; en efectivo el resto | SPY, IWM, EFA | ¿El cambio de mes es mejor que 4 días cualesquiera? |
| H7 `sector_lowvol` | Como H5, pero eligiendo los 3 sectores más tranquilos | Como H5 | ¿Elegir por calma es mejor que al azar? |

Se descartó todo lo que se pareciera a H1–H4 sobre datos ya vistos (incluida cripto: queda fuera
y su OOS intacto, P9), y está prohibido rescatar H1–H4 con los criterios nuevos (enmienda 16 de
`docs/hipotesis.md`). Bien hecho: con los números de H4-OOS, H4 también suspendería el
criterio 17 nuevo (relación 3,45/7,04 = 0,49 frente a 0,60 de SPY; `docs/hipotesis_ronda2.md` §0.3).

### 5.2 Criterios nuevos (resumen de `docs/hipotesis_ronda2.md` §4)
- **Relajado solo por decisión de Jorge:** kill switch al 15 % (y la calibración del riesgo pide
  caída IS ≤ 12 %, con 3 puntos de margen); desaparece la comparación de CAGR con SPY.
- **Nuevo:** criterio 16 (batir a las letras a 3 meses + 2 puntos; en cada tramo, al menos
  batirlas) y criterio 17 (mejor relación rentabilidad/caída que SPY), más el 16d (batir a IEF en
  el tramo largo).
- **Endurecido:** p < 0,02 contra los monos (antes 0,05) y contra **dos** tipos de mono en H5/H7;
  caída máxima total ≤ 15 % (antes 20 %); Monte Carlo ≤ 22,5 % (antes 30 %); Sharpe ≥ 0,5 también
  en IS; dos tramos reservados; réplica en otros activos; 12 meses de paper como examen final.
- Unas **25 casillas** que deben cumplirse todas (secciones A–D de §4), más el paper.

### 5.3 La auditoría de la ronda 2 (`docs/auditoria_ronda2.md`)
Hecha por Fable antes de existir código: 0 críticos, 4 altos, 9 medios, 8 bajos. Lo más
importante:
- **A1:** los monos de H5/H7 rotaban mucho más que la candidata y pagaban más costes, lo que
  favorecía a la candidata → se añade un «mono persistente» (E4). Buena detección.
- **A2/A3:** la fórmula de H6 fallaba al final del calendario y no tenía salida de emergencia →
  corregido (E6).
- **A4:** H6 tiene los criterios 2 y 16 casi fuera de alcance porque pasa ~80 % del tiempo con
  el dinero al 0 % → pregunta a Jorge (P14).
- **M4:** el criterio 17 solo aprieta de verdad en 2021–2026 (en tramos con 2000–2002 o 2008
  la relación de SPY es muy baja: 0,16 en el IS, `docs/auditoria_ronda2.md` M4).
- Las enmiendas E1–E14 están fechadas antes del primer backtest y ninguna suaviza un criterio.

### 5.4 Decisiones pendientes de Jorge (todas antes del primer backtest IS de la ronda 2)
| # | Pregunta | Opción por defecto | Mi recomendación |
|---|---|---|---|
| P7 / **P14** | ¿El efectivo parado cuenta al 0 % frente a las letras? | Sí (0 %) | Mantener 0 % **pero** decidir ya si merece la pena programar H6 (ver §7) |
| P8 | Duración del paper | 12 meses | De acuerdo |
| P9 | Cripto | Fuera de la ronda 2 | De acuerdo |
| P10 | Margen de calibración | Caída IS ≤ 12 % | De acuerdo (es prudente) |
| P11 / P12 | Qué es «caja» y «claramente por encima» | Letras a 3 meses + 2 puntos | De acuerdo; es una elección razonable |
| P13 | Rama | `ronda2/hipotesis` sin fusionar | Fusionar antes la ronda 1 en `main` (ver §6, B2) |
| **P15** | Regla 5 cuando venta y compra van a la misma apertura | Exposición tras ejecutar ≤ 100 %, recorte del 3 % | De acuerdo con la opción (a) |
| P16 | ¿Los 24 ETFs son operables en Alpaca? | Lo comprueba R2-3 | Hacerlo antes del IS |

---

## 6. Mi revisión crítica (por gravedad)

Ninguno de estos puntos cambia el veredicto de la ronda 1. Los marco como **A** (alto), **M**
(medio) o **B** (bajo).

### Altos
**A1. El diseño casi garantiza «ninguna apta», y nadie ha medido cuánto.**
Con kill switch permanente, 1 % de riesgo como techo, 3 huecos, efectivo al 0 % y unas 25
casillas que hay que cumplir todas, una estrategia **buena de verdad** también tiene bastantes
papeletas de suspender alguna por mala suerte. No existe un análisis de potencia (simular con
datos inventados una estrategia con ventaja conocida y ver con qué frecuencia pasa todos los
filtros). Sin eso no sabemos si «ninguna apta» significa «no hay ventaja» o «el examen es tan
exigente que nada puede aprobarlo». El propio pre-registro lo intuye (`docs/hipotesis_ronda2.md`,
«Opinión, escrita antes de ver nada»). *Arreglo:* un test sintético de potencia antes del
primer IS. No cambia ningún criterio; solo informa.

**A2. El candado del OOS no impide mirarlo varias veces.**
`src/tlab/backtest/runner.py` (`check_oos_guard`) solo exige `--confirm-oos` y bloquea si el
hash de parámetros es **distinto** del anterior. Con los **mismos** parámetros se puede repetir
el OOS sin límite, y el hash (`params_hash`) no incluye el riesgo por operación, los costes ni
el retraso: se podría cambiar el riesgo y volver a mirar sin que salte nada. En la ronda 1 no
se abusó (`reports/oos_log.csv`: 4 filas anunciadas de antemano), pero la protección era la
disciplina, no el código. Las especificaciones de la ronda 2 ya lo corrigen sobre el papel (D4
en `docs/especificaciones_ronda2.md`: hash con `f`, sin `--force`, `frozen = true`). *Arreglo:*
que R2-5 esté hecho y probado **antes** del primer IS, no después.

**A3. El kill switch permanente y la calibración con el pasado chocan en el paper.**
Se calibra el riesgo para que la peor caída **histórica** sea ≤ 12 % y el freno salta al 15 %.
La peor caída futura suele ser mayor que la peor pasada; si salta, el experimento se para hasta
que Jorge borre el archivo a mano. Además está sin definir **sobre qué equity** se mide todo
(1 %, exposición, kill switch): la configuración razona con 10.000 $ virtuales
(`config/settings.toml`, `virtual_equity_usd`), pero la cuenta paper de Alpaca tendrá otro
saldo. *Arreglo:* dejar escrito en el paso 4/5 que todas las reglas se miden sobre el equity
virtual del experimento, y qué se hace (y quién decide) si el freno salta durante el paper.

### Medios
**M1. Trazabilidad de git: el veredicto cita un commit que no está en ninguna rama.**
`docs/veredicto.md` dice que H4 se congeló en el commit `14aed91`. Ese commit existe en el
repositorio local pero **no pertenece a ninguna rama**: hubo un rebase y su equivalente es
`79a2881` (mismo mensaje, misma hora, mismo cambio en `config/strategies/donchian_etf.toml`;
solo cambian tres ficheros de diagnóstico de datos). Si git limpia objetos sueltos,
desaparecerá. Además, el commit de congelación (16:36:43) y la ejecución del OOS (16:36 en
`reports/oos_log.csv`) son del mismo minuto, y cinco commits del paso 2 tienen la misma hora
exacta (15:53:27, señal de reescritura de historia). El orden «congelar → mirar» es creíble,
pero git no lo **prueba**. *Arreglo:* corregir el hash en el veredicto; para la ronda 2, una
etiqueta (`git tag`) en el commit de congelación, no reescribir historia después de congelar y
guardar el hash del commit en cada fila de `oos_log.csv`.

**M2. La prueba contra el azar de la ronda 1 favorecía un poco a la estrategia.**
En el informe de H4, los monos hacen menos operaciones (141,8 de media frente a 167) y están
menos invertidos (32 % frente a 43 %) ✓
(`reports/robustez/donchian_etf_nokill/azar_is_20261111-1629/resumen.md`). Con activos que
suben a largo plazo, ir menos invertido y con menos operaciones penaliza al mono. Junto con que
el p = 0,047 no está corregido por los 330 intentos previos de la familia Donchian (lo dice el
propio veredicto), el aprobado de H4 en el criterio 14 era más débil de lo que parece. En la
ronda 2 los monos a medida y el p < 0,02 lo mejoran, pero conviene **comprobar en el informe**
que operaciones y exposición de los monos se parecen a las de la candidata.
Detalle menor del mismo informe: imprime «riesgo 0% por operación» (la plantilla de
`src/tlab/backtest/robust_reports.py` formatea 0,005 sin decimales) y el texto dice «mismo
sizing al 1 %», aunque el Sharpe real (0,70) es el de la ejecución al 0,5 %.

**M3. El walk-forward no prueba la estrategia que luego se examina.**
En el walk-forward de H4 se re-elige cada año la mejor combinación de la rejilla, y casi nunca
salió la de por defecto (55/20/2,0): salieron 69/20/2,5, 55/20/1,5 y 55/20/2,5 ✓
(`reports/donchian_etf/wf_20261111-1615/resumen.md`). El OOS, en cambio, se hizo con 55/20/2,0.
Es decir, el criterio 5 valida «el procedimiento de optimizar», no los parámetros congelados.
La ronda 2 repite el diseño. No es un error grave (la robustez de vecinos cubre parte), pero
debería decirse así en los informes, o añadir un walk-forward informativo con los parámetros
congelados.

**M4. Pruebas múltiples a nivel de proyecto.**
Cada ronda controla sus variantes, pero no hay límite al número de rondas. Cada ronda que se
añade sobre los mismos años de mercado aumenta la probabilidad de que algo pase por suerte, y
el conocimiento general del modelo sobre lo que hicieron los mercados (declarado con honestidad
en `docs/hipotesis_ronda2.md` §0.4) contamina todo backtest. *Arreglo:* que Jorge fije ya un
tope (p. ej. «como mucho una ronda más de backtest; después, o paper o se cierra») y que el
paper se trate como la única prueba que decide.

**M5. Diseño y auditoría los hace el mismo modelo.**
Fable escribe el pre-registro y luego lo audita (`docs/auditoria_ronda2.md`). La auditoría es
buena, pero no es independiente. Las citas académicas son «de memoria» y no se han verificado.
Este informe es una primera revisión externa; convendría repetirla al cerrar la ronda 2.

**M6. Datos antiguos de yfinance y ejecución en la apertura.**
La ronda 2 usa yfinance desde 1998 para el tramo reservado antiguo y el simulador **compra y
vende en la apertura**. Los precios de apertura de ETFs poco negociados a principios de los 2000
son la parte menos fiable de esas series. `src/tlab/data/validate.py` comprueba coherencia de
velas, huecos y duplicados, y R2-18 añade saltos de cierre a cierre > 20 %, pero nadie mira la
calidad de las **aperturas** (por ejemplo, cuántos días la apertura es exactamente el cierre
anterior). No lo he medido. *Arreglo:* añadirlo a la verificación de datos (R2-18), sin calcular
rentabilidades.

**M7. El ejecutor diario y la parte de seguridad en vivo no existen todavía.**
`CLAUDE.md` describe `scripts/signals.py`, `scripts/run_daily.py`, `scripts/weekly_report.py`,
`STRATEGY.md` y `journal/`; ninguno existe. La guardia de paper está, pero no está conectada a
ningún código de órdenes, y la comprobación del archivo `KILL_SWITCH` al arrancar no está
implementada (`guard.py` acepta un parámetro `kill_switch_file` que no usa). Hoy no hay riesgo
porque no se envía nada; será crítico en el paso 5.

**M8. H6 cuesta mucho y probablemente muera.**
H6 necesita calendario, salida sostenida, monos de «ventana» y casos especiales
(`docs/especificaciones_ronda2.md` R2-8, R2-9, R2-15). La propia auditoría (A4) dice que, con
el efectivo al 0 %, tiene los criterios 2 y 16 casi fuera de alcance. Es trabajo de
programación con poca probabilidad de servir.

### Bajos
- **B1.** El valor por defecto del kill switch en el código sigue en 10 % en varios sitios
  (`config/settings.toml`, `risk.check_kill_switch`, `SimConfig`). Es más estricto que la
  regla, así que no es peligroso; R2-1 lo cambia.
- **B2.** `main` está todavía en el paso 1 (`fddae77`): el motor, el veredicto y la ronda 2
  solo viven en ramas (`paso2/candidatas`, `ronda2/hipotesis`). Decisión P6/P13 pendiente.
- **B3.** Las baselines usan datos hasta el 2026-11-10 (`docs/baselines.md`), más allá del fin
  pre-registrado (2026-10-31). Son 10 días del «tramo nuevo que crece solo» ya vistos en
  estrategias clásicas. Efecto despreciable, pero conviene anotarlo.
- **B4.** Sharpe con tipo libre de riesgo 0: con letras al 4–5 % en los últimos años, el
  Sharpe ≥ 0,5 es más fácil de lo que parece. El criterio 16 lo compensa en parte.
- **B5.** Las baselines comparan con estrategias que no cumplen las reglas duras (sin stop, al
  100 %). Por ejemplo, «TSMOM 12m 1/N» da CAGR 6,3 % y caída −15,8 % en 2005–2026
  (`docs/baselines.md`), mejor que H4. Recordatorio de cuánto «cuestan» las reglas duras; no es
  un error.
- **B6.** 22 avisos de pandas en los tests (`DatetimeIndex.dayofyear` obsoleto en
  `src/tlab/backtest/montecarlo3d.py`). Cosmético.

### Lo que está bien (y conviene no perder)
- Pre-registro fechado, enmiendas antes de mirar, prohibición explícita de rescatar candidatas
  muertas.
- Registro de **todas** las variantes, también las malas (`docs/registro_pruebas.md`).
- Honestidad en los documentos: «no lo he medido», avisos de contaminación, opinión escrita
  antes de ver resultados.
- Motor prudente y con tests (162 en verde), guardia de paper y CI con ruff + pytest
  (`.github/workflows/ci.yml`).

---

## 7. Siguientes pasos recomendados (en este orden)

1. **Jorge decide P14 y P15** (y confirma P7–P13, P16) antes de que Sonnet empiece a programar.
   Si P14 se queda en «efectivo al 0 %», recomiendo **aparcar H6** (no programarla en esta
   ronda) y dejarla anotada; ahorra la parte más cara de las especificaciones.
2. **Jorge fija un tope de rondas** (M4): por ejemplo, «si la ronda 2 no da nada apto, no hay
   ronda 3 de backtest».
3. **Arreglos de trazabilidad antes de cualquier IS:** corregir `14aed91` → `79a2881` en
   `docs/veredicto.md`; acordar «etiqueta de git en la congelación y nada de rebase después»;
   implementar primero R2-5 (candado de un solo uso con hash que incluya `f`, costes y retraso).
4. **Sonnet implementa en el orden de `docs/especificaciones_ronda2.md` §1** (R2-1, R2-2, datos
   R2-3/R2-18 con la comprobación de aperturas de M6, R2-4, señales de panel, sectores, monos,
   informe).
5. **Test de potencia sintético** (A1): una estrategia inventada con ventaja conocida pasa por
   todos los criterios de §4 de la ronda 2; ver con qué frecuencia aprueba. Solo informativo.
6. **Fable repite la auditoría del motor** sobre el código nuevo y comprueba que los monos se
   parecen a la candidata en operaciones y exposición (M2).
7. **IS de las candidatas vivas → un único commit de congelación con etiqueta → peldaños** en el
   orden de E2.
8. **Si alguna queda «apta para paper»:** escribir `STRATEGY.md`, definir sobre qué equity se
   miden las reglas (A3), programar el ejecutor con la comprobación de `KILL_SWITCH` (M7) y
   arrancar los 12 meses de paper. **Si ninguna queda apta:** aceptar el resultado; el proyecto
   ya ha cumplido su función educativa y la opción honesta es cerrarlo o replantear el objetivo,
   no seguir buscando hasta que algo pase.

---

## 8. Glosario corto
- **Backtest:** simular una regla con datos del pasado.
- **Paper trading:** operar con dinero ficticio en una cuenta real del broker.
- **Pre-registro:** dejar escrito qué se va a probar y cómo se aprueba, antes de mirar.
- **IS (in-sample):** datos para desarrollar. **OOS (out-of-sample) / tramo reservado:** datos
  que se guardan y se miran una sola vez al final.
- **Walk-forward:** elegir parámetros con el pasado y probarlos en el periodo siguiente, varias veces.
- **CAGR:** crecimiento anual compuesto (lo que «rinde al año» de media).
- **Caída máxima (drawdown):** lo máximo que bajó el capital desde un pico.
- **Relación rentabilidad/caída:** CAGR dividido por la caída máxima.
- **Sharpe:** rentabilidad dividida por lo que «se mueve»; más alto = más rentabilidad por
  unidad de susto.
- **R:** lo que se arriesga en una operación; ganar 2R es ganar el doble de lo arriesgado.
- **Expectancy:** ganancia media por operación, medida en R.
- **Stop:** precio al que se vende sí o sí para cortar pérdidas.
- **ATR:** tamaño medio de las velas recientes; sirve para poner el stop a una distancia
  proporcional a lo que se mueve el activo.
- **Slippage:** diferencia entre el precio esperado y el que te dan. **pb:** punto básico = 0,01 %.
- **Kill switch:** freno de emergencia que cierra todo si se cae demasiado.
- **Monos:** estrategias al azar con las mismas reglas, para ver si la ventaja es suerte.
- **p-valor:** proporción de monos que lo hacen igual o mejor; cuanto más bajo, menos probable
  que sea suerte.
- **Sobreajuste:** retocar una regla hasta que encaje con el pasado; luego no funciona.
- **Look-ahead:** usar sin querer datos del futuro en el backtest.
- **ETF:** fondo que cotiza en bolsa como una acción (p. ej. SPY replica el S&P 500).
- **Benchmark:** el rival con el que se compara (p. ej. comprar SPY y no tocarlo).
