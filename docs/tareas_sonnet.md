# Tareas para Sonnet (trabajo mecánico pendiente)

Las deja Fable. Sonnet las hace en orden y marca cada una al terminar. Si algo choca con
`CLAUDE.md` o con `docs/hipotesis.md`, **para y pregunta**; no improvises.

## Tras el paso 1 (2026-11-11) — implementar las candidatas de `docs/hipotesis.md`

**Requisito previo (lo decide Jorge, P6 de `hipotesis.md`):** fusionar la rama
`prep/motor-backtest` en `main`, o rehacer el motor con el prompt 02. Estas tareas dan por
hecho que el motor de esa rama está disponible. `docs/registro_pruebas.md` de `main` es una copia
idéntica del de esa rama para que la fusión no dé conflicto.

**Prohibido:** ejecutar nada sobre el periodo OOS de las candidatas (`--mode oos`, `--period oos`
o fechas posteriores a `is_end`). Tampoco cambiar parámetros, universos, fechas ni criterios de
`docs/hipotesis.md`.

- [x] 1. Datos: añadir `DBC`, `VNQ`, `DIA`, `LTC/USD`, `BCH/USD` al universo de `settings.toml` y
      descargarlos. Anotar la primera fecha real de cada símbolo en yfinance (sobre todo
      `ETH-USD`, `BCH-USD`, `LTC-USD`) y avisar si alguna no permite empezar en las fechas de §3.
- [ ] 2. Datos (script hecho: `scripts/check_alpaca_vs_yf.py`; falta ejecutarlo en el PC con claves): con las claves de Alpaca, contrastar yfinance ↔ Alpaca en el tramo común (ETFs
      desde 2016, cripto desde 2021) comparando rentabilidades diarias. Documentar la tolerancia
      usada y las discrepancias. Si no cuadran, parar.
- [x] 3. `settings.toml`: `costs.crypto.slippage_bps = 20`.
- [x] 4. `risk.apply_limits`: tope por posición `max_position_fraction` (equity/3) + tests con los
      números de `hipotesis.md` §6.4.
- [x] 5. `risk_per_trade`, `start`, `is_end`, `end` configurables en el TOML de cada estrategia;
      cada activo entra al universo cuando tiene ≥ 365 velas.
- [x] 6. Estrategias: `donchian_crypto`, `donchian_etf` (reutilizan el módulo Donchian),
      `tsmom_etf`, `rsi2_etf`. Un TOML por id con `status = "preregistrada"`. Registrar en
      `SIGNAL_STRATEGIES`. Tests unitarios con los casos a mano de §6.1–6.3 y los de look-ahead.
- [x] 7. Walk-forward según §3 (entrenamiento creciente, ventanas con fechas fijas, elección por
      Sharpe en la rejilla ±25 %, ventanas sin operaciones excluidas).
- [x] 8. Informes: recuento de episodios de kill switch con reinicio del máximo; "quitar las 5
      mejores operaciones"; "quitar el mejor activo"; subperiodos con las fechas de §4;
      exposición media.
- [x] 9. Benchmarks con costes: buy & hold SPY y BTC; 60/40 SPY/IEF y 50 % BTC / 50 % caja con
      rebalanceo mensual.
- [x] 10. `ruff` y `pytest` en verde (157 pasados, 2 saltados; ver `docs/INFORME_PASO2.md`). **No** ejecutar todavía los backtests in-sample de las
      candidatas: los lanza Fable en el paso 3, después de auditar el motor (fase A).

## Para el paso 5 (anotado ahora para no olvidarlo)
- En cripto, Alpaca solo admite `stop_limit` (no stop a mercado): definir el margen del límite y
  qué hace el script si el stop no se ejecuta en un hueco.
- El tamaño se calcula antes de la apertura con el cierre anterior; si abre más arriba, el riesgo
  real puede pasar del 1 %: recalcular con el precio visible o usar orden limitada.

## Tras el paso 3 (2026-11-11) — ninguna candidata aprobada (ver `docs/veredicto.md`)

No hay paso 4 que implementar. Mejoras de herramienta para la siguiente ronda (ninguna urgente,
ninguna toca fechas OOS):

- [ ] `reports/oos_log.csv`: añadir columnas `mode`, `costs` y `entry_delay` para distinguir la
      ejecución OOS que decide de las de estrés y de la `full` (hoy solo se distinguen por el
      registro de pruebas).
- [ ] `--mode full` de las candidatas: añadir al informe el Monte Carlo del periodo completo
      (criterio 10) y, en todos los modos, peor año natural y peor racha de pérdidas seguidas.
- [ ] DSR y PBO de las candidatas a partir de las ejecuciones de la rejilla ya hechas en
      `--mode robust` (sin barridos nuevos), contando los intentos heredados.
- [ ] `scripts/check_alpaca_vs_yf.py`: añadir al informe la correlación sin los N peores días y
      cuántos de los días fuera de tolerancia caen en marzo de 2020 (lo que hoy hace a mano
      `reports/datos/verificacion_fable_20261111.md`). No cambiar las tolerancias.
- [x] Tarea 2 de la lista anterior (contraste yfinance ↔ Alpaca): ejecutado
      (`reports/datos/contraste_20261111-1555.md`), investigado y verificado por Fable.

## Ronda 2 (2026-11-11) — implementar H5–H7 de `docs/hipotesis_ronda2.md`

Lee antes `CLAUDE.md` («Enmiendas») y `docs/hipotesis_ronda2.md` entero. Si algo choca, **para y
pregunta**.

**Prohibido:** ejecutar cualquier backtest de `sector_mom`, `tom_etf` o `sector_lowvol` con datos
reales (ni IS, ni réplica, ni tramos reservados, ni "solo para probar que arranca"). Solo tests
con datos sintéticos o `tests/fixtures/`. Tampoco calcular rentabilidades de los símbolos nuevos
al verificar datos (solo fechas, huecos y duplicados). No cambiar parámetros, universos, fechas ni
criterios. Sin `git push`.

- [x] R2-1. **Kill switch al 15 %** (decisión de Jorge, regla dura 6): `config/settings.toml`
      (`kill_switch_drawdown = 0.15`), valores por defecto en `risk.check_kill_switch`,
      `portfolio_sim.SimConfig`, `robustness.kill_switch_episodes`, `montecarlo.DEFAULT_KILL` y
      `targets.py`; textos de `README.md` y de `prompts/01`, `02` y `05`. Los tests que pasan
      `0.10` como argumento explícito no se tocan. Los informes de la ronda 1 **no** se regeneran.
- [x] R2-2. `robustness.calibrate_risk`: el límite sale del TOML de la estrategia
      (`calibration_dd_limit`, 0.12 en la ronda 2); las candidatas de la ronda 1 conservan 0.10.
- [ ] R2-3. **Datos:** añadir a `settings.toml` y descargar con yfinance (ajustado) desde
      1998-12-01: `XLB XLE XLF XLI XLK XLP XLU XLV XLY`, `EWJ EWG EWU EWC EWQ EWI EWA EWL EWH`,
      `MDY`; y bajar la historia de `SPY`, `IWM`, `EFA`, `EEM`, `IEF` desde su primera vela.
      Pasar `data/validate.py`. Escribir en `reports/datos/` una tabla con primera y última vela,
      nº de velas, huecos y fecha en la que cada símbolo llega a 365 velas. Comprobar con Alpaca
      (`get_asset`) que todos son operables. Aplicar la regla de §3.1 si algo no existe (retrasar
      el inicio / quitar el símbolo de la réplica) y **anotarlo para Fable, no decidirlo**.
- [x] R2-4. **Caja:** serie diaria del tipo de las letras a 3 meses (`^IRX` en yfinance, en % anual)
      y benchmark "caja" = capital × ∏(1 + tipo/100)^(1/252). Si `^IRX` no está o tiene huecos
      largos, alternativa: el CSV público `DTB3` de FRED (sin clave). Documentar cuál se usa. Test
      con una serie constante del 5 % → CAGR 5 %.
- [x] R2-5. **Tramos múltiples** en el TOML y en `scripts/backtest.py`: `is`, `replica`,
      `holdout_old` (2000-07-01 → 2007-06-30), `holdout_new` (2021-01-01 → 2026-10-31), `full`
      (2000-07-01 → 2026-10-31), cada uno con su universo y su `slippage_bps` (5 / 15 / 10 / 5 /
      el del tramo que toque en `full`: 10 hasta 2007-06-30 y 5 después). Guarda de un solo uso
      por (estrategia, tramo, hash de parámetros) en `reports/oos_log.csv`, con columnas nuevas
      `tranche`, `costs`, `entry_delay` (cubre la tarea pendiente del paso 3). Orden obligado:
      `replica` → `holdout_old` → `holdout_new` → `full`; el script se niega a saltarse uno.
- [x] R2-6. **Señales de panel** (§6.1): tipo `generate_signals_panel`, registro aparte, integración
      en `runner` y en los tests de look-ahead. Test: en una misma apertura las salidas liberan
      hueco antes que las entradas.
- [x] R2-7. Estrategias `sector_mom` y `sector_lowvol` (§6.2) con los casos S1–S4 como tests; dos
      TOML con `status = "preregistrada"`.
- [ ] R2-8. Estrategia `tom_etf` (§6.3): calendario inyectado en `params["sessions"]`, casos C1–C4,
      TOML. Para el modo en vivo, función que construya el calendario con `get_calendar`.
- [x] R2-9. **Monos a medida** (§3.4) en `random_benchmark.py`: modo `rank` (sortea el orden de los
      aptos en cada revisión) y modo `window` (sortea la sesión de entrada de cada mes; salida 4
      sesiones después). Semilla 42, 1.000. Test de reproducibilidad.
- [x] R2-10. **Informe:** relación CAGR/|caída| de estrategia, SPY y 60/40; CAGR de caja e `IEF`;
      CAGR conjunto de los dos tramos reservados (fórmula del criterio 16a); criterio 16d sobre el
      trozo de `full` desde 2002-08-01; subperiodos del criterio 11; episodios de kill switch al
      15 %; variante informativa "efectivo rindiendo como la caja"; peor año y peor racha.
- [x] R2-11. **Banda para el paper** (§3.6 b): remuestreo por bloques de 21 sesiones, 10.000
      trayectorias, semilla 42, percentiles 5/50/95 a 6 y 12 meses. Solo la herramienta y su test.
- [ ] R2-12. Cartera combinada de §5.4 (sectores con 2 huecos + `tom_etf` con 1 hueco en `SPY`):
      solo dejar preparado el modo y un test sintético; no ejecutarlo.
- [ ] R2-13. `ruff` y `pytest` en verde; informe corto `docs/INFORME_RONDA2_IMPL.md` con dudas de
      interpretación para Fable (como `INFORME_PASO2.md`).

## Ronda 2 — añadidos de la auditoría (2026-11-12, `docs/auditoria_ronda2.md`)

**Antes de empezar R2-1…R2-13:** lee las «Enmiendas» del 2026-11-12 al final de
`docs/hipotesis_ronda2.md` (E1–E13). Donde choquen con el texto anterior, **manda la enmienda**.
En concreto: R2-8 se implementa con las fórmulas de E6 (no con las de §6.3), R2-9 incluye el mono
persistente de E4 y el sorteo de E5, R2-4 aplica E10, R2-5 aplica E11 y R2-3 se amplía con R2-18.
Las prohibiciones de la sección anterior siguen igual, con la precisión de E13.

**Especificación detallada (2026-11-12):** `docs/especificaciones_ronda2.md` da, para cada tarea
R2-1 … R2-18, ficheros, firmas, casos a mano con números, casos límite, criterios de aceptación
y el orden de implementación. Léela antes de escribir código (empieza por §0, «Hallazgos»). Donde
precise algo de esta lista (p. ej. la fórmula de la caja de R2-4, enmienda E14), **manda la
especificación**.

- [x] R2-14. **Casos a mano que faltaban para las señales de panel** (tabla y parámetros de S1:
      `lookback=2, top_n=2, keep_n=3, atr_mult=3, atr_n=1`):
  - **S5 (empate):** B cierra a 110 el 02-01 → `mom` de A y de B = 0,10. Con `top_n = 1`:
    `entry` solo en A (empate → alfabético). Con `top_n = 2`: A y B.
  - **S6 (menos aptos que huecos):** cierres del 02-01: A 110, B 99, C 98, D 97 → solo A es apto:
    `entry` solo A; `exit` en B, C y D. Si además A cierra a 99: ningún `entry`, cuatro `exit`.
  - **S7 (historia insuficiente):** se añade E con solo dos velas (01-31 a 50 y 02-01 a 100). E no
    es apto ni ocupa puesto: las filas de A–D son las de S1 y `entry(E) = False`.
  - **S8 (fuga entre símbolos):** multiplicar por 10 todos los precios de B posteriores al 02-01
    no cambia ninguna fila ≤ 02-01 de **ningún** símbolo. Cortar solo las velas de A en el 02-01
    no cambia las filas del 02-01 de B, C y D.
  - **S9 (sin vela el día de revisión, E7):** C no tiene vela el 02-01 → C no tiene fila ese día
    y todas las suyas son `False`; `entry` = A y B; `exit` = D.
  - **S10 (simulador, el puesto 4–5 conserva el hueco):** cartera con X, Y, Z (3 huecos). En la
    revisión, X tiene `entry = exit = False` y un cuarto activo W tiene `entry = True` → W **no**
    se compra en `t+1` ni ningún otro día de ese mes (no hay cola); X sigue.
  - **S11 (simulador, rotación en la misma apertura):** en la revisión Z tiene `exit` y W
    `entry` → en la apertura de `t+1` se vende Z y se compra W; la caja no queda negativa en
    ningún momento.
  - **S12 (simulador, señal repetida):** un activo en cartera vuelve a tener `entry = True` con
    otro `stop_price` → ni la cantidad ni el stop cambian.
- [ ] R2-15. **Casos a mano que faltaban para `tom_etf`** (fórmulas de E6; `atr_mult=3, atr_n=1`):
  - **C5 (salida sostenida):** calendario con todas las sesiones del 2024-01-02 al 2024-02-06
    (enero tiene 21; el 01-15 es festivo). `entry` solo el 01-30. `exit = True` del 01-04 al
    01-29 inclusive y el 02-05 y 02-06; `False` el 01-02, 01-03, 01-30, 01-31, 02-01 y 02-02.
  - **C6 (mes incompleto):** calendario de C1 cortado en el 01-31 → `entry = False` en todas las
    filas (no se puede saber que el 31 es la última sesión).
  - **C7 (vela ausente):** C1 sin la vela del 02-05 → no hay fila del 02-05 y la del 02-06 tiene
    `exit = True`.
  - **C8 (sin calendario):** `params` sin `sessions`, o con un `sessions` al que le falta una
    fecha de `bars` → `ValueError`.
  - **C9 (de punta a punta en el simulador):** un activo, 10.000 $, riesgo 1 %, slippage 5 pb,
    calendario de C1. Velas `(open, high, low, close)`: 01-29 `(100, 100, 100, 100)` ·
    01-30 `(100, 102, 99, 101)` · 01-31 `(101, 103, 100, 102)` · 02-01 `(102, 104, 101, 103)` ·
    02-02 `(103, 105, 102, 104)` · 02-05 `(104, 106, 103, 105)` · 02-06 `(106, 107, 105, 106)`.
    Señal el 01-30 (stop 92). Compra en la apertura del 01-31: precio 101,0505; riesgo por unidad
    101,0505 − 91,954 = 9,0965 → `floor(100 / 9,0965)` = **10 acciones** (1.010,51 $). Venta en la
    apertura del 02-06 a 105,947. Resultado: 10 × (105,947 − 101,0505) = **+48,97 $ = +0,538 R**.
    Una sola operación.
  - **Retraso de 1 vela:** con el mismo caso, la compra pasa a la apertura del 02-01 (102) y la
    venta no se mueve.
- [x] R2-16. **Tests de los monos** (además del de reproducibilidad):
  - "Mono con el orden verdadero": si al modo `rank` se le inyecta el orden real, y al modo
    `window` la sesión de compra real, las operaciones son **idénticas** a las de la candidata.
  - Si en todas las revisiones hay ≤ 3 aptos, cualquier mono (de los dos tipos) da las mismas
    operaciones que la candidata.
  - Mono persistente (E4): la permutación no tiene puntos fijos, es la misma durante toda la
    simulación y el filtro `apto` no cambia respecto a la candidata.
  - Modo `window` (E5): una ventana por mes, misma sesión de compra para los 3 activos, venta en
    la apertura de la 4.ª sesión posterior, sin solapes entre meses.
- [x] R2-17. **Tests de métricas, límites y tramos:**
  - Relación (E9): CAGR 6 % y caída −12 % → 0,5. CAGR −1 % → criterio 17 "no" sea cual sea el
    resto. Caída 0 con operaciones → infinita. SPY con relación ≤ 0 y estrategia con CAGR > 0 → "sí".
  - CAGR conjunto (16a): `G_antiguo = 1,5` en 7 años y `G_reciente = 1,2` en 5 años →
    `1,8^(1/12) − 1` = **5,02 %**.
  - Caja (E10): tipo de descuento del 5 % → rentabilidad **5,134 %**; serie constante → ese CAGR.
  - Kill switch: con máximo 10.000 $, equity 8.500,00 **no** salta (la regla dice "más de un
    15 %") y 8.499,99 sí. Cargar una configuración con `kill_switch_drawdown > 0.15` debe dar
    error (techo de la regla dura 6).
  - Guarda de tramos: segunda ejecución del mismo (estrategia, tramo, hash) → error; saltarse el
    orden → error; el modo `is` se niega si alguna fecha cae fuera del IS.
  - Coste por fecha (E11): compra el 2007-06-29 y venta el 2007-07-02 en `full` → 10 pb al
    entrar, 5 pb al salir.
  - Informativo (hallazgo B4): Monte Carlo de `tom_etf` barajando **meses** (la suma de las
    operaciones abiertas el mismo día) además del de operaciones sueltas. No es criterio.
- [ ] R2-18. **Datos (amplía R2-3, enmienda E13):**
  - Tabla de primera vela por símbolo, comparada con las fechas de `docs/auditoria_ronda2.md` §6
    (en especial los 8 ETFs de países cuya fecha individual no se pudo confirmar en la web).
  - Lista de fechas con variación de cierre a cierre mayor del ±20 % (solo fecha y símbolo), y
    comprobación expresa de que **no** hay salto en: `XLK XLY XLE XLU XLB` el 2025-12-05;
    `EWJ`, `EWU`, `EWI` el 2016-11-07.
  - `scripts/check_alpaca_vs_yf.py` sobre los símbolos nuevos (tramo común desde 2016), con las
    tolerancias de la ronda 1 sin tocar.
  - Nº de días de revisión (primera sesión del mes) en los que falta la vela de algún sector o
    país, y nº de días de señal de `tom_etf` en los que falta la de `SPY`, `IWM`, `EFA`, `MDY`,
    `EEM` o `EWJ`. Solo recuentos y fechas.
  - `get_asset` de Alpaca para los 24 símbolos: campos `tradable` y `fractionable`. Si un símbolo
    de réplica no es operable se anota para quitarlo; si no lo es uno principal, **parar y avisar**.
  - Base de cotización de la serie de caja (descuento o rentabilidad), con la fuente.

## Ronda 2 — decisiones del 2026-11-12, 15:32 (enmiendas E15–E22)

**Decidido por Opus por delegación de Jorge, 2026-11-12** (`docs/decisiones_ronda2.md`). Donde
choque con las secciones anteriores, **manda esta**. Las prohibiciones siguen igual.

**No se hacen (H6 aparcada, E15):** R2-8 entero · el modo `window` de R2-9 · R2-12 · R2-15 · el
Monte Carlo por meses de R2-17 · los recuentos de días de `tom_etf` de R2-18 · la descarga de
`MDY` en R2-3. No borres nada de lo que ya exista; si algo de H6 llegara a estar escrito, se deja
sin registrar en `SIGNAL_STRATEGIES`.

**Orden nuevo de requisitos previos del primer IS:** R2-1, R2-2, R2-3 + R2-18, **R2-5 completo y
probado** (E21), R2-6, R2-7, R2-9 (`rank` + persistente), R2-10, R2-14, R2-16, R2-17, R2-19, R2-13.

- [x] R2-5 (ampliado, E20/E21): columna `commit` (hash completo de `HEAD`) en `oos_log.csv` y en
      las líneas de IS de `docs/registro_pruebas.md`; abortar si
      `git status --porcelain -- config src scripts` no está vacío (cualquier tramo, IS incluido);
      rechazar cualquier modo distinto de IS sobre estrategias `rechazada` o `aparcada` (también
      `--mode oos`/`full` del runner de la ronda 1); `status = "aparcada"` válido. Tests: árbol
      sucio → error; `donchian_etf` y `donchian_crypto` en `--mode oos` → error.
- [x] R2-10 (ampliado, E22): nº de operaciones y exposición media de cada tipo de mono frente a la
      candidata; walk-forward informativo con los parámetros por defecto en las 8 ventanas (no
      decide el criterio 5).
- [ ] R2-18 (ampliado, E22/M6): por símbolo y año, nº de días con apertura = cierre anterior y con
      apertura fuera de [mínimo, máximo]. Solo recuentos. Si en un sector supera el 5 % de las
      sesiones de `holdout_old`, **parar y avisar**.
- [x] R2-19 (nuevo, E22/A1). **Test de potencia sintético**, sin datos reales: series inventadas
      de 9 activos donde la fuerza de 6 meses tiene una ventaja conocida (y otra versión sin
      ventaja), pasadas por los criterios de §4 A que se puedan calcular en sintético; frecuencia
      de aprobado en N series (semilla 42). Herramienta + informe `reports/potencia/`. Se ejecuta y
      se escribe **antes** del primer IS. Informativo: no cambia ningún criterio.
- [ ] E19: antes del primer IS, avance rápido **local** de `main` hasta `ronda2/hipotesis`
      (`git checkout main && git merge --ff-only ronda2/hipotesis`), solo con el visto bueno de
      Jorge. Sin push.
- [ ] E20: etiqueta anotada `ronda2/pre-is` en el commit desde el que Fable lance el IS (la pone
      Fable). Prohibido rebase/amend/reset/force sobre commits etiquetados o anteriores.
- Para el paso 5 (solo anotado, E18 y E22): el ejecutor comprueba al arrancar
  `max_margin_multiplier == "1"`, `no_shorting == true` y `max_options_trading_level == 0` en la
  cuenta paper y se niega a arrancar si no; ventas antes que compras; recorte de la compra con
  margen del 3 %; sin reintento si se rechaza; reglas medidas sobre el equity del experimento y
  tamaño con `min(equity del experimento, equity de la cuenta)`.
