# PREP_NOTES — trabajo adelantado en la rama `prep/motor-backtest`

Preparado el 11 nov 2026 de madrugada (hora de Madrid) por Grok Bot, **sin usar Claude**, para
ahorrar cupo de Fable. Es el trabajo "mecánico" del **prompt 02** (motor de backtest, datos,
métricas, tests) más unos **baselines** de referencia. **No está fusionado en `main`**: Fable lo
revisa y Jorge decide si se fusiona.

> Importante para el pre-registro: Fable puede ver `docs/baselines.md`, pero **no debe usarlo
> para elegir parámetros** de sus candidatas. Son clásicos de manual, para tener vara de medir.

## Qué hay
| Pieza | Archivo | Estado |
|---|---|---|
| Proyecto uv, Python 3.12, ruff, pytest (marcador `network`) | `pyproject.toml`, `uv.lock` | ✔ |
| Configuración (riesgo, costes, universo, fechas) | `config/settings.toml` | ✔ valores por defecto del prompt 02 |
| Datos con caché parquet incremental | `src/tlab/data/loader.py` | ✔ 2.ª carga = 0 llamadas de red |
| Alpaca (SIP→IEX, 200/min, cripto 00:00 UTC) | `src/tlab/data/alpaca_source.py` | ⚠ escrito pero **sin probar** (no hay claves) |
| yfinance (respaldo, ajustado) | `src/tlab/data/yf_source.py` | ✔ fuente usada ahora |
| Validación de velas | `src/tlab/data/validate.py` | ✔ |
| Indicadores causales (SMA, EMA, ATR/RSI de Wilder, Donchian, ROC) | `src/tlab/indicators.py` | ✔ |
| Estrategias: `demo_sma` (DEMO), `donchian_atr` (baseline), mensuales (buy&hold, Faber, TSMOM, dual momentum) | `src/tlab/strategies/` | ✔ baselines, **no** candidatas |
| Riesgo: sizing 1 % con costes, límites, kill switch | `src/tlab/risk.py` | ✔ |
| Simulador de cartera vela a vela (motor del veredicto) | `src/tlab/backtest/portfolio_sim.py` | ✔ |
| Simulador por pesos (solo baselines mensuales) | `src/tlab/backtest/allocation_sim.py` | ✔ |
| vectorbt por activo | `src/tlab/backtest/vbt_engine.py` | ✔ (ver diferencias abajo) |
| Walk-forward, robustez (±25 %, costes ×2, retraso, top-5, Monte Carlo, subperiodos) | `walkforward.py`, `robustness.py` | ✔ básico |
| Métricas + informes + registro | `metrics.py`, `report.py`, `backtest/runner.py` | ✔ |
| CLI | `scripts/backtest.py`, `scripts/download_data.py` (= `fetch_data.py`), `scripts/run_baselines.py`, `scripts/montecarlo.py` | ✔ |
| Guardia solo-paper | `src/tlab/broker/guard.py`, `alpaca_paper.py` | ✔ (sin órdenes) |
| Tests | `tests/` | ✔ **111 passed** sin red (+2 de red con `-m network`; incluye Monte Carlo, mapa de parámetros, DSR/PBO, contra el azar y visor) |
| Monte Carlo (barajar, bootstrap, bloques) | `src/tlab/backtest/montecarlo.py`, `scripts/montecarlo.py`, `scripts/visor_montecarlo.py` | ✔ ver `docs/MONTECARLO.md` |
| Mapa de parámetros (rejilla 2–3 parámetros, robustez 0–100, DSR, PBO-CSCV) | `src/tlab/backtest/param_sweep.py`, `overfit.py`, `scripts/param_sweep.py` | ✔ ver `docs/ROBUSTEZ.md` |
| Contra el azar (1000 «monos» emparejados, p-valor) | `src/tlab/backtest/random_benchmark.py`, `scripts/random_benchmark.py` | ✔ ver `docs/ROBUSTEZ.md` |
| Visor único (Monte Carlo + mapa + azar) | `scripts/visor.py` (el antiguo `visor_montecarlo.py` abre lo mismo) | ✔ |

## Cómo se usa
```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest -q -m 'not network'     # 111 tests, sin red
uv run pytest -q -m network            # 2 tests que descargan 5 días de SPY y BTC
uv run python scripts/fetch_data.py    # regenera data_cache/ (yfinance si no hay claves)
uv run python scripts/backtest.py --strategy demo_sma --mode full
uv run python scripts/backtest.py --strategy donchian_atr --mode is     # también wf, robust
uv run python scripts/backtest.py --strategy <id> --mode oos --confirm-oos   # SOLO Fable, paso 3
uv run python scripts/run_baselines.py # reescribe docs/baselines.md
uv run python scripts/montecarlo.py --list
uv run python scripts/montecarlo.py --run reports/donchian_atr/is_20261111-0140 --method shuffle
uv run python scripts/montecarlo.py --prepare-baselines
uv run python scripts/montecarlo.py --run reports/baselines/20261111-0141/donchian_nokill --method bootstrap
uv run python scripts/montecarlo.py --run reports/baselines/20261111-0141/faber_sma_spy --method block
uv run python scripts/param_sweep.py --preset donchian        # mapa 330 combinaciones, solo IS
uv run python scripts/param_sweep.py --preset tsmom_spy
uv run python scripts/random_benchmark.py --preset donchian   # 1000 monos, semilla 42, solo IS
uv run python scripts/random_benchmark.py --preset tsmom_spy
uv sync --extra visor && uv run streamlit run scripts/visor.py   # (visor_montecarlo.py sigue valiendo)
```
Monte Carlo: baraja o remuestrea las operaciones (o bloques de rentabilidades
diarias) para ver si el camino del backtest fue típico o afortunado. Detalle,
cómo leer los gráficos y advertencias en `docs/MONTECARLO.md`. Los informes de
las baselines de referencia están en `reports/baselines/20261111-0141/<slug>/`.

Robustez: el **mapa de parámetros** dice si el resultado aguanta al mover los parámetros
(meseta) o es un pico; el **contra el azar** compara con 1000 estrategias que entran al azar con
las mismas reglas y costes. Los dos son **solo in-sample** por defecto (OOS exige
`--confirm-oos`) y cada barrido se anota en `docs/registro_pruebas.md` con su nº de
configuraciones. Detalle, cómo leerlos y resultados de Donchian/TSMOM en `docs/ROBUSTEZ.md`;
informes en `reports/robustez/<slug>/`.

Para una candidata nueva: un módulo en `src/tlab/strategies/<id>.py` con
`generate_signals(bars, params) -> DataFrame[entry, exit, stop_price, rank, (target_price)]`,
registrarlo en `src/tlab/strategies/__init__.py`, `config/strategies/<id>.toml` (copiar
`donchian_atr.toml`, opcional `is_end = "AAAA-MM-DD"`), y añadir su id a los tests
parametrizados de `tests/test_lookahead.py` + `test_strategy_<id>_cases`.

## Decisiones tomadas (la opción más conservadora cuando había duda)
- **Ejecución**: señal al cierre de `t` → apertura de `t+1` con slippage en contra. Si la
  apertura ya está por debajo del stop, **no se entra**. Tras entrar se mira el stop en la misma
  vela.
- **Sizing**: se calcula con la apertura de ejecución y el equity a esa apertura (el ejecutor
  real tendrá que recalcularlo con el precio que vea; ver limitaciones).
- **Stops**: gap → sale a la apertura; toque → al stop; ambos con slippage. Stop + objetivo en la
  misma vela → stop. Stop fijo (no se mueve) salvo que la estrategia lo cambie.
- **Kill switch**: se evalúa con el **cierre**; liquida en la **apertura siguiente** y bloquea
  entradas para siempre. Por eso el DD real puede pasar algo del 10 % (gap de la mañana).
- **Fin de datos**: lo abierto se cierra al último cierre (motivo `end_of_data`) para contarlo.
- **Calendarios mezclados** (ETF L–V, cripto 7 días): unión de fechas; cada activo solo actúa en
  sus velas; las órdenes pendientes de un ETF del viernes esperan al lunes (test incluido).
- **Periodo de cada backtest** (`runner.py`): desde 1 año después de que el activo MÁS joven de
  la estrategia tenga datos. Si hay BTC, los ETFs también empiezan en 2015-09. Split IS/OOS
  provisional = 70 % / 30 % (`settings.toml [validation]`) hasta que `docs/hipotesis.md` fije
  fechas (`is_end` en el TOML de la estrategia).
- **Walk-forward**: 50 % inicial de entreno + 5 ventanas de prueba contiguas (sin solape) con
  parámetros por defecto (sin re-optimizar). Ajustar a lo que pre-registre Fable.
- **Anualización**: 252 si solo ETFs, 365 si hay cripto.
- **Velas diarias**: índice UTC a las 00:00 de la fecha de sesión. Cripto: 00:00 UTC, igual que
  Alpaca v1beta3 (ver `docs/VERIFICACIONES.md`). yfinance: se descarta la vela de hoy (UTC), que
  puede estar sin cerrar.

## Limitaciones conocidas
1. **Alpaca no probado**: `alpaca_source.py` está escrito según la doc de alpaca-py pero no se ha
   ejecutado. Mañana, con claves: `uv run python scripts/download_data.py --source alpaca` y
   comparar contra yfinance (deberían cuadrar los cierres ajustados de SPY a ±0,1 %).
2. **Diferencias vectorbt vs portfolio_sim** (test `test_engines_agree_single_asset`): con stop
   lejano coinciden en nº de operaciones y < 0,5 pp. Con stops cercanos coinciden en nº de
   operaciones pero la rentabilidad difiere ~1–2 pp porque (a) vectorbt no aplica slippage a la
   salida por stop y (b) si en la misma vela hay salida por señal a la apertura y el low toca el
   stop, vectorbt da prioridad al stop. portfolio_sim es el más pesimista/realista en ambos.
   **Usar vectorbt solo para rejillas rápidas; el veredicto con portfolio_sim.**
3. **No se modela**: dividendos en paper (yfinance los mete en el precio ajustado), subastas de
   apertura, liquidez/impacto de mercado, horarios exactos del calendario de Alpaca (los huecos se
   detectan con una heurística: >4 días naturales en ETFs, >1 en cripto; marca el cierre por el
   funeral de Ford en 2007 y el huracán Sandy en 2012, que son reales), impuestos, fracciones de
   cripto distintas de 1e-6.
4. **El sizing usa la apertura de `t+1`**; el ejecutor diario decidirá la cantidad antes de la
   apertura (con el cierre de `t`). Si abre más arriba, el riesgo real puede pasar algo del 1 %.
   El paso 5 debe recalcular o usar órdenes limitadas.
5. `robust` es básico: rejilla ±25 % sobre `robust_keys` (3^k combinaciones), costes ×2, retraso
   1 vela, sin top-5, Monte Carlo corto (1000, semilla 42, solo DD al barajar) y 3 subperiodos.
   El módulo completo (`scripts/montecarlo.py`, 5000 sims, abanico, P(kill switch), block
   bootstrap) se corre aparte; ver `docs/MONTECARLO.md`. No calcula automáticamente los
   criterios ✔/✘ de `hipotesis.md` §4: eso lo hace Fable leyendo la tabla.
6. `docs/registro_pruebas.md` ya existe con 6 filas: demo, baseline Donchian IS, 2 barridos
   (Donchian N=330, TSMOM N=72; cuentan como intentos para el DSR) y 2 benchmarks contra el azar
   (marcados «[benchmark azar, no es variante]», no cuentan como intentos).
7. Las herramientas de robustez usan yfinance y van sin kill switch en las corridas de
   referencia de Donchian; en el «contra el azar» de Donchian los monos quedan algo menos
   expuestos que la real (40 % frente a 46 %). Ver advertencias en `docs/ROBUSTEZ.md`.

## PREGUNTAS PARA FABLE (decidir en el paso 1)
1. **Kill switch en backtest**: con la regla literal, la cartera Donchian de baseline se para en
   2015-09 y pasa 11 años en efectivo (ver `docs/baselines.md`). ¿El criterio de aprobado se mide
   con kill switch permanente (como en real), o se mide sin él y el kill switch se evalúa como
   "¿cuántas veces habría saltado?"? Recomendación: pre-registrar ambos números.
2. **Estrategias mensuales sin stop** (Faber, TSMOM, dual momentum) chocan con "stop obligatorio
   + 1 % de riesgo". Opciones: (a) añadir un stop de catástrofe (p. ej. entrada − 3×ATR o −15 %)
   y dimensionar al 1 % (exposición pequeña), (b) dimensionar por volatilidad con tope 100 %, o
   (c) cambiar la regla para estas estrategias. Hay que decidirlo y escribirlo **antes** de
   probar. Hoy solo existen como baselines en `allocation_sim` (100 % invertidas, sin stop).
3. Con 1 % de riesgo y stops de 2×ATR en ETFs, la exposición media sale baja (~14–40 %): es
   normal, pero afecta a CAGR frente a buy & hold. Conviene que los criterios lo tengan en cuenta
   (p. ej. comparar Sharpe/DD más que CAGR).

## Qué debería auditar Fable primero en el prompt 03 (Fase A)
1. `portfolio_sim.py`, bloque de entradas: sizing con apertura de `t+1` y equity a la apertura;
   comprobación de stop en la vela de entrada; desempate por rank y símbolo.
2. `runner.run_signals`: las señales se calculan con TODA la historia y luego se recorta el
   periodo (correcto solo porque las estrategias son causales; lo vigilan los tests de
   look-ahead truncación/envenenamiento, que cubren todas las estrategias registradas).
3. `allocation.monthly_closes` + `allocation_sim`: decisión con el último cierre del mes y
   ejecución en la apertura siguiente.
4. `risk.risk_per_unit`: costes de entrada y salida incluidos en el 1 %.
5. Kill switch al cierre y liquidación a la apertura siguiente.
6. Que cada candidata nueva que se implemente pase por `tests/test_lookahead.py` (es automático
   si se registra en `SIGNAL_STRATEGIES`).

## Cambios sugeridos a los prompts (no aplicados; que decida Jorge/Fable)
- **Prompt 01**: añadir "Ya existe el motor (rama `prep/motor-backtest`, ver `docs/PREP_NOTES.md`)
  y unos baselines; no los uses para elegir parámetros. `docs/registro_pruebas.md` ya existe:
  añade, no lo recrees. Responde a las PREGUNTAS PARA FABLE de `PREP_NOTES.md`." En §6, pedir las
  candidatas con la firma exacta de `generate_signals` del repo.
- **Prompt 02**: ya no hace falta entero. Convertirlo en **"02b — implementar candidatas"** (para
  Sonnet): por cada candidata de `docs/hipotesis.md`, módulo en `strategies/`, TOML en
  `config/strategies/`, registro en `__init__.py`, casos a mano de §6 como tests,
  `--mode is` para cada una, y cerrar los puntos 1–2 de "Limitaciones" (probar Alpaca y ajustar
  walk-forward/fechas a lo pre-registrado). Aproximadamente 1 sesión de Sonnet en vez de 2.
- **Prompt 03**: en "Lee primero" cambiar `docs/progreso_paso2.md` por `docs/PREP_NOTES.md`
  (o leer ambos); en la Fase A, empezar por la lista "Qué debería auditar Fable primero".
  Añadir en la Fase B, paso 4 «Robustez» (además de `--mode robust`; **solo in-sample y con los parámetros ya pre-registrados**):
  por cada candidata, `scripts/param_sweep.py --strategy <id> --grid ... ` (2–3 parámetros,
  meseta ≥ 70 y PBO < 50 % como señales a favor, sin elegir la mejor celda) y
  `scripts/random_benchmark.py --strategy <id> --n 1000 --seed 42` (umbral fijado antes:
  p < 0,05). Cada barrido suma su nº de configuraciones al registro y al N del DSR: anotarlo
  en el veredicto. Nunca `--period oos` con estas herramientas. Ver `docs/ROBUSTEZ.md`.
