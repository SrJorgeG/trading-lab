# Prompt 04 — Manual de operación `STRATEGY.md` + especificación de señales (modelo: **Fable**)

> Cómo lanzarlo: `cd ~/trading-lab && claude --model fable` → *"Lee y ejecuta prompts/04_fable_manual_operacion.md"*.
> Requisito: `docs/veredicto.md` con al menos una estrategia **APROBADA PARA PAPER**. Si no hay ninguna, **no ejecutes este prompt**: vuelve al paso 1.
> Al acabar: `git commit` y `/clear`.

---

## Tu papel
Vas a escribir el **manual que ejecutarán otros**: un script de Python sin IA cada día y, si hace falta, un modelo menos capaz (Sonnet u Opus) o una persona. La prueba de calidad: **dos ejecutores distintos, leyendo tu manual con los mismos datos, toman exactamente las mismas decisiones**. Nada de "según el contexto", "si parece", "valorar".

## Lee primero
`CLAUDE.md`, `docs/veredicto.md`, `docs/hipotesis.md` (solo las estrategias aprobadas), `config/strategies/<id>.toml` de las aprobadas, y el código de esas estrategias en `src/tlab/strategies/` (para que el manual y el código digan lo mismo).

## Hechos de Alpaca que el manual debe respetar (verificados en su documentación)
- **Acciones/ETFs:** las órdenes `opg` (*market on open*, se ejecutan en la subasta de apertura) solo se aceptan **antes de las 9:28** o **después de las 19:00, hora de Nueva York**; entre 9:28 y 19:00 se rechazan. Las fracciones de acción **no** se permiten con `opg` ni `gtc` (solo `day`). → Usaremos **acciones enteras**.
- **Cripto:** solo `time_in_force` `gtc` o `ioc`; tipos de orden market, limit y stop-limit (no hay stop "a mercado"). Comisión taker del 0,25 % en el tramo inicial.
- **Paper:** simula ejecuciones con precios reales, a veces con ejecuciones parciales (≈ 10 % de las veces); **no simula dividendos**.
- **Horario:** sesión de EE. UU. de 9:30 a 16:00 (hora de Nueva York) = 15:30–22:00 en Madrid casi todo el año, pero **14:30–21:00** durante las ~2–3 semanas en que EE. UU. y Europa cambian de hora en fechas distintas (marzo y finales de octubre). Por eso el código **siempre** razona en hora de Nueva York y usa el calendario de Alpaca (festivos, cierres anticipados).

Si alguno de estos hechos choca con la estrategia aprobada, **dilo** y propone la adaptación mínima (y si cambia la lógica, la estrategia debe volver al paso 3).

## Entregable 1: `STRATEGY.md` (raíz del repo)
Estructura obligatoria:

1. **Resumen en 5 líneas** (para Jorge).
2. **Parámetros congelados** (tabla) y versión: `strategy_version = <id>-v1`, hash del `.toml`.
3. **Universo** (lista cerrada de símbolos) y **datos** (fuente principal y de respaldo, timeframe, ajuste, qué vela se considera "cerrada" y a qué hora está disponible).
4. **Indicadores** con fórmula exacta y nº mínimo de velas necesario (calentamiento).
5. **Reglas** en pseudocódigo numerado: entrada, salida, stop inicial, ¿se mueve el stop? (cuándo y cómo, solo en dirección favorable), ranking y desempate.
6. **Sizing** con 2 ejemplos numéricos completos (uno ETF, uno cripto si aplica), incluidos costes y redondeo.
7. **Horario de ejecución** (hora de Nueva York y equivalente en Madrid) y **tipo de orden** para cada acción (entrada, salida por señal, stop), con `time_in_force`.
8. **Checklist diario** (numerado, de 10–20 pasos, en el orden exacto en que el script lo hace): guardia de paper → `KILL_SWITCH` → mercado abierto/festivo → sincronizar estado con el broker → kill switch por drawdown → datos → señales → plan de órdenes (salidas primero, luego stops, luego entradas) → límites → enviar → verificar → diario.
9. **Tabla de decisiones**: filas = estado (sin posición / con posición / con orden pendiente / kill switch activo), columnas = señal (entrada / salida / nada / stop tocado), celdas = acción exacta.
10. **Casos borde** (qué hacer en cada uno, acción por defecto = no operar y anotar): festivo o cierre anticipado; datos que faltan o llegan tarde; vela incoherente; gap por debajo del stop; orden rechazada; ejecución parcial; posición en el broker que no está en el estado local (o al revés); posición sin stop; split o cambio de símbolo; activo suspendido (halt) o no negociable; el PC estaba apagado y la ejecución llega tarde (pasada la ventana de `opg` → **no** enviar entradas ese día); cantidad calculada = 0; más señales que huecos; dos estrategias quieren el mismo símbolo; kill switch.
11. **Qué NO hacer nunca** (lista corta, incluye las reglas duras).
12. **Expectativas del backtest** (rangos sacados de `docs/veredicto.md`, con su informe): operaciones/mes, win rate, expectancy en R, peor racha, drawdown típico y máximo.
13. **Criterios para pausar o retirar la estrategia en paper** (objetivos y medibles), por ejemplo: drawdown en paper > 1,5 × el máximo del backtest; tras ≥ 20 operaciones, expectancy en R por debajo del percentil 5 de la distribución Monte Carlo del backtest; ≥ 3 incumplimientos de reglas por errores de ejecución en un mes.
14. **Criterios mínimos antes de plantear dinero real** (solo plantear, la decisión es de Jorge): p. ej. ≥ 3 meses y ≥ 30 operaciones en paper, comportamiento dentro de los rangos esperados, cero incumplimientos de reglas el último mes.

## Entregable 2: `docs/signals_spec.md` (especificación de `scripts/signals.py`)
- **Entrada:** fecha de decisión (hora de Nueva York), ruta de config, estado actual (posiciones del broker).
- **Salida:** JSON (y su esquema) con, por estrategia y símbolo: `action` (`ENTER`, `EXIT`, `HOLD`, `UPDATE_STOP`, `SKIP`), `qty`, `order_type`, `time_in_force`, `stop_price`, `reason` (frase en español que cite la regla, p. ej. "R3: cierre > máx. 20 velas y precio > SMA200"), `strategy_version`, `bar_timestamp` (UTC) de la vela usada.
- Determinista: mismos datos → mismo JSON byte a byte (orden de claves y de símbolos fijo).
- **3–5 ejemplos resueltos a mano** (velas pequeñas inventadas → JSON esperado), que Sonnet convertirá en tests "golden" (de referencia).
- Lista de **errores** y su código de salida (datos insuficientes, guardia de paper, kill switch…).

## Entregable 3: `docs/tareas_sonnet.md`
Añade la lista concreta de lo que Sonnet debe programar en el paso 5 que no esté ya en `prompts/05_sonnet_paper_diario.md` (si hay algo específico de esta estrategia).

## Criterios de "hecho"
- `STRATEGY.md` con las 14 secciones, sin ambigüedades ("si…, entonces…" en todo).
- `docs/signals_spec.md` con esquema JSON y 3–5 ejemplos a mano.
- Coherencia comprobada: cada regla de `STRATEGY.md` corresponde a una línea concreta del código de la estrategia (cita archivo y función). Si hay discrepancia, gana lo validado en el paso 3 y lo anotas para Sonnet.

## Condiciones de parada
- No cambies parámetros ni lógica de la estrategia aprobada. Si crees que hay que cambiar algo, escríbelo como propuesta para una futura ronda (vuelve al paso 3).
- No escribas el código del ejecutor (eso es el paso 5, Sonnet).
- No envíes órdenes.
- Al terminar, resume en 8 líneas qué hará el sistema cada día y qué tiene que hacer Jorge.
