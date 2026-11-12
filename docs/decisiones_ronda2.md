# Decisiones pendientes de la ronda 2 — 2026-11-12, 15:32 (hora de Madrid)

> **Decidido por Opus por delegación de Jorge, 2026-11-12.** Jorge me ha delegado hoy las preguntas
> abiertas P7–P16 (`docs/hipotesis_ronda2.md` §5 y «Preguntas abiertas», `docs/auditoria_ronda2.md`
> §5, `docs/informe_estudio.md` §5.4) y las recomendaciones de mi informe (`docs/informe_estudio.md`
> §6–§7).
>
> **Escrito antes de cualquier backtest IS de la ronda 2.** Comprobado ahora: no existe código de
> `sector_mom`, `tom_etf` ni `sector_lowvol`, ni informes suyos en `reports/`. No he ejecutado
> ningún backtest ni abierto datos de precios. Este documento no contiene ninguna cifra de
> rentabilidad nueva.
>
> No es asesoramiento financiero. Solo paper.

## Límites de esta delegación (qué NO he decidido)

- **Ninguna regla dura cambia.** `CLAUDE.md` dice que solo Jorge puede cambiar una regla dura; esta
  delegación no lo hace. Donde una pregunta tocaba una regla dura (P7, P15), he elegido la opción
  que **no** la cambia, o una lectura igual o más estricta que la literal.
- **No toco las dos decisiones de Jorge del 2026-11-11** (objetivo «punto medio»; kill switch al
  −15 %).
- **Ningún criterio de aceptación se suaviza.** Tres decisiones endurecen o recortan (E15, E17,
  E21); el resto confirma lo que ya estaba.
- Jorge puede revertir cualquiera de estas decisiones **él mismo**, con una enmienda fechada,
  **solo antes del primer backtest IS de la ronda 2**. La única excepción es E17 (tope de rondas):
  se puede levantar más adelante, pero solo con una decisión personal de Jorge, nunca por delegación.

Aplicadas como enmiendas **E15–E22** en `docs/hipotesis_ronda2.md`, y anotadas en `CLAUDE.md`
(«Enmiendas»), `docs/especificaciones_ronda2.md` (§0.2) y `docs/tareas_sonnet.md`.

## Preguntas P7–P16

| # | Pregunta | Decisión | Motivo breve | Enmienda |
|---|---|---|---|---|
| **P7** | ¿Dejar el efectivo libre en un ETF de letras (`BIL`/`SGOV`)? | **No.** El efectivo rinde 0 % y así se juzga. | Es lo que pasa de verdad en la cuenta paper. Un ETF de letras sería una 4.ª posición sin stop (choca con las reglas duras 3 y 4) y solo Jorge puede tocar eso. Además facilitaría el criterio 16 a posteriori del diseño. | E16 |
| **P8** | Duración del examen en paper | **12 meses**, revisión a los 6 solo de fidelidad y seguridad. | 6 meses casi no distinguen nada. | E16 |
| **P9** | Cripto | **Fuera de la ronda 2**; su OOS (2023-07 → 2026-10) sigue intacto. Con E17, no hay ronda propia de cripto salvo que Jorge la abra en persona. | H1 no cabía en el freno ni con 0,5 %; no hay rival ni presupuesto de caída decididos de antemano. | E16, E17 |
| **P10** | Margen de calibración | **Caída máxima IS ≤ 12 %** (3 puntos bajo el −15 %). | La peor caída futura suele superar a la pasada; calibrar al 15 % es diseñar para que el freno salte. | E16 |
| **P11** | Qué es «renta fija/caja» | **Letras a 3 meses** en cada tramo (en rentabilidad, E10); `IEF` solo en la ejecución completa (16d). | Un fondo de bonos a 7–10 años no es caja: también cae. | E16 |
| **P12** | «Claramente por encima» | **+2,0 puntos al año** (16-IS, 16a, 16d); sin margen tramo a tramo (16b). | Ya fijado así antes de ver nada; cambiarlo ahora no tiene base. | E16 |
| **P13** | Rama | Se sigue en `ronda2/hipotesis`. **Antes del primer IS**, avance rápido **local** de `main` hasta esa rama (sin push). | `main` sigue en el paso 1; el veredicto y el motor deben estar en la rama principal antes de gastar datos (informe B2). Se comprobó hoy que `main` es antecesor de `HEAD` (avance rápido posible). | E19 |
| **P14** | H6 con el efectivo al 0 % frente a las letras | **(a): se deja al 0 %.** Y además **H6 queda APARCADA**: no se implementa ni se ejecuta en la ronda 2. | Juzgarla con el efectivo rindiendo como las letras sería suavizar. Con el 0 %, la propia auditoría (A4) la da casi por muerta, y es la parte más cara de programar (calendario, salida sostenida, monos de ventana, cartera combinada). Aparcarla también reduce las pruebas múltiples (de 90 a 60 variantes como máximo). | E15 |
| **P15** | Regla dura 5 cuando venta y compra van a la misma apertura | **(a)**, con tres salvaguardas más estrictas: cuenta paper con multiplicador de margen 1; primero ventas, luego compras; compra recortada con margen del 3 % y, si el broker la rechaza, no se reintenta ese día. El backtest no cambia. | Lectura igual o más estricta que la literal: la exposición nunca pasa del 100 % y la cuenta no puede usar margen ni aunque quiera. (b) obligaría a cambiar el simulador sin ganar seguridad. | E18 |
| **P16** | ¿Los ETFs son operables en Alpaca? | **R2-3/R2-18 (`get_asset`) es requisito previo del primer IS.** Réplica no operable → se quita sin sustituir; principal no operable → se para y decide Jorge. | No verificado en ninguna sesión. Con H6 aparcada, `MDY` sale de la lista. | E16, E15 |

## Recomendaciones de mi informe

| # | Recomendación | Decisión | Motivo breve | Enmienda |
|---|---|---|---|---|
| M4 | **Tope de rondas** | **La ronda 2 es la última ronda de búsqueda con backtest sobre datos históricos.** Si ninguna queda apta: «ninguna apta», no se opera, no hay ronda 3. No se añaden candidatas a la ronda 2. Abrir otra ronda (incluido rescatar H6 o cripto) exige una decisión **personal** de Jorge, fechada, que levante este tope expresamente. | Cada ronda más sobre los mismos años aumenta la probabilidad de que algo apruebe por suerte, y el conocimiento general del modelo sobre el mercado contamina todo backtest. El paper es la única prueba limpia. | E17 |
| M8 | **Aparcar H6** | **Sí** (ver P14). Sus tramos quedan sin ejecutar; aparcada no es aprobada ni «pendiente»: retomarla es abrir una ronda nueva (E17). | Mucho trabajo con poca probabilidad de servir, y menos intentos múltiples. | E15 |
| M1 | **Trazabilidad del commit del veredicto** (`14aed91` → `79a2881`) | Corregido con nota fechada en `docs/veredicto.md`. Comprobado hoy: `14aed91` no está en ninguna rama; `79a2881` tiene el mismo mensaje, hora y cambio en `config/strategies/donchian_etf.toml`; entre los dos solo difieren `scripts/diag_alpaca_vs_yf.py`, `src/tlab/data/crosscheck.py` y `tests/test_crosscheck.py`. Etiquetas locales creadas: `ronda1/congelacion-h4` (→ `79a2881`) y `ronda1/congelacion-h4-original` (→ `14aed91`, para que git no lo borre). Para la ronda 2: etiqueta anotada en el commit de congelación (E2), nada de rebase/amend/reset/force sobre commits etiquetados, y hash del commit en cada fila de `oos_log.csv`. | Que git **demuestre** el orden «congelar → mirar», en vez de depender de la disciplina. | E20 |
| A2 | **Candado del OOS** | **R2-5 hecho y probado es requisito previo del primer IS.** Clave de un solo uso = (estrategia, tramo, hash de `params` + `f`, costes, retraso, tipo) (D4), más el commit. Sin `--force`. El script se niega a ejecutar un tramo con cambios sin commitear en `config/`, `src/` o `scripts/`. Retroactivo: cualquier modo fuera de IS sobre una estrategia con `status = "rechazada"` (H1–H4) o `"aparcada"` (H6) se rechaza. | Hoy el candado permite repetir el OOS con los mismos parámetros, y el hash no incluye el riesgo ni los costes. | E21 |
| A1 | Test de potencia sintético | **Sí, informativo**, después de R2-10 y antes del primer IS. Su resultado se escribe **antes** del IS y **no puede cambiar ningún criterio**. | Para saber, si sale «ninguna apta», si significa «no hay ventaja» o «el examen casi no se puede aprobar». | E22 |
| A3 | Sobre qué equity se miden las reglas | Equity **del experimento** (10.000 $ virtuales + resultado de sus operaciones); el tamaño usa además el mínimo entre ese equity y el de la cuenta. Si el kill switch salta durante el paper, la candidata **suspende** el criterio (c) de §3.6; borrar `KILL_SWITCH` no reinicia el examen. Se escribe en `STRATEGY.md` (paso 4). | La cuenta paper tendrá otro saldo; sin esto, «1 %» y «−15 %» serían ambiguos. | E22 |
| M2 | Monos parecidos a la candidata | El informe de monos muestra nº de operaciones y exposición media de los monos frente a la candidata. Informativo. | En la ronda 1 los monos de H4 iban menos invertidos que H4. | E22 |
| M3 | Walk-forward con parámetros congelados | Se añade como informativo (mismas 8 ventanas, parámetros por defecto, no es variante nueva). El criterio 5 no cambia. | El criterio 5 valida el procedimiento de optimizar, no los parámetros que luego se examinan. | E22 |
| M6 | Calidad de las aperturas antiguas | R2-18 cuenta, por símbolo y año, los días con apertura = cierre anterior y con apertura fuera de [mínimo, máximo]. Solo recuentos. Si en un símbolo principal pasa en > 5 % de las sesiones del tramo antiguo, se para y se decide por enmienda antes del IS. | El simulador compra en la apertura y las aperturas antiguas son la parte menos fiable de yfinance. Umbral fijado ahora para que no se elija después. | E22 |
| M5 | Revisión independiente | Al cerrar la ronda 2, revisión independiente (no Fable) del veredicto antes de darlo por cerrado. | Diseño y auditoría los hace el mismo modelo. | E22 |
| B3 | Baselines con datos hasta el 2026-11-10 | Se anota en el inventario de contaminación (10 días del tramo nuevo vistos con estrategias clásicas). | Transparencia; efecto despreciable. | E22 |

## Requisitos previos del primer IS (lista única tras estas decisiones)

1. R2-1 (kill switch al 15 % en código) y R2-2.
2. R2-3 + R2-18 (datos, operabilidad, saltos, aperturas de M6), leídos por Fable.
3. **R2-5 completo y probado** (candado de E21).
4. R2-6, R2-7, R2-9 (modos `rank` y persistente), R2-10, R2-14, R2-16, R2-17 (sin las partes de H6).
5. Test de potencia escrito (E22).
6. `main` avanzada hasta la rama de trabajo (E19) y etiqueta `ronda2/pre-is` en el commit desde el que se lanza el IS.
7. Auditoría del motor repetida por Fable sobre el código nuevo.

## Qué queda para Jorge (no delegable)

- Configurar en la cuenta paper, antes del paso 5: `max_margin_multiplier = "1"`, `no_shorting = true`,
  `max_options_trading_level = 0` (E18). No lo he hecho: es un cambio en una cuenta externa.
- Levantar el tope de rondas (E17), si algún día quiere.
- Cualquier cambio de regla dura.
