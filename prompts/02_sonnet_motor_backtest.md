# Prompt 02 — Motor de backtest, datos, métricas y tests (modelo: **Sonnet**)

> Cómo lanzarlo: `cd ~/trading-lab && claude --model sonnet` → *"Lee y ejecuta prompts/02_sonnet_motor_backtest.md"*.
> Puede necesitar 1–2 sesiones. Si se corta, en la siguiente: *"Continúa prompts/02 desde donde lo dejaste; mira `git log` y `docs/progreso_paso2.md`"*.
> Al acabar: `git commit` y `/clear`.

---

## Tu papel
Eres un ingeniero de software cuidadoso. Implementas **exactamente** lo que dicen `CLAUDE.md` y `docs/hipotesis.md`. **No** diseñas estrategias, **no** cambias parámetros ni criterios, **no** optimizas nada y **no** sacas conclusiones de rentabilidad. Si algo de la especificación es ambiguo, eliges la opción **más conservadora** (la que menos favorece a la estrategia) y la apuntas en `docs/progreso_paso2.md`.

## Lee primero
`CLAUDE.md` (entero), `docs/hipotesis.md` (sobre todo la sección 6, "Especificación para implementar"), y las skills `backtesting-frameworks` y `backtest-expert` de `~/.claude/skills` como guía de buenas prácticas.

## Entregables

### 1. Proyecto
- `pyproject.toml` con Python `>=3.12,<3.13`, paquete `tlab` en `src/`, dependencias: `pandas`, `numpy`, `vectorbt>=1.2,<2`, `alpaca-py`, `yfinance`, `pyarrow`, `python-dotenv`, `tomli-w` (si hace falta escribir TOML), `jinja2` (informes). Dev: `pytest`, `ruff`. Opcional (extra `crypto`): `ccxt`.
- Configuración de `ruff` (line-length 100) y de `pytest` (marcador `network` registrado; por defecto se excluye con `-m "not network"`).
- `uv sync` funciona desde cero.

### 2. Configuración — `config/settings.toml`
Con los valores de `docs/hipotesis.md` (si faltan, estos por defecto):
```toml
[capital]
virtual_equity_usd = 10000      # capital con el que razonamos aunque la cuenta paper tenga más
[risk]
risk_per_trade = 0.01
max_positions = 3
max_gross_exposure = 1.0        # sin apalancamiento
kill_switch_drawdown = 0.10
[costs.equity]
commission_per_share = 0.0
slippage_bps = 5                # por lado; ETFs muy líquidos
[costs.crypto]
fee_rate = 0.0025               # taker tramo 1 de Alpaca, por lado
slippage_bps = 10
[costs.stress]
multiplier = 2.0
[data]
equity_start = "2016-01-01"
cache_dir = "data_cache"
```
Y `config/strategies/<id>.toml` por cada candidata de `docs/hipotesis.md` (parámetros por defecto + rango de robustez + `status = "candidata"`).

### 3. Datos — `src/tlab/data/`
- `loader.py`: `load_bars(symbols, timeframe, start, end, asset_class) -> dict[str, DataFrame]` con columnas `open, high, low, close, volume`, índice `DatetimeIndex` en **UTC**, ordenado, sin duplicados.
- **Caché** en `data_cache/` (parquet), clave = fuente + símbolo + timeframe + ajuste + feed. Actualización incremental (solo pide lo que falta). Segunda llamada idéntica = **cero** llamadas de red.
- `alpaca_source.py`: acciones con `StockHistoricalDataClient` (`adjustment="all"`, `feed` SIP con `end` de hace más de 15 min; si da error de suscripción, reintenta con IEX y lo registra). Cripto con `CryptoHistoricalDataClient` (símbolos tipo `BTC/USD`). Respeta **200 llamadas/min** (limitador simple) y pagina con `next_page_token` si hace falta. Claves desde `.env` con `python-dotenv`; nunca las registres.
- `yf_source.py`: respaldo con `yfinance` (`auto_adjust=True`), mapeando símbolos (`BTC/USD` → `BTC-USD`).
- **Validación de datos** (función `validate_bars`): sin NaN en OHLC, `high ≥ max(open, close)`, `low ≤ min(open, close)`, volumen ≥ 0, huecos de fechas detectados (informa, no rellenes inventando velas). Registra en el informe qué fuente y rango se usaron.
- `scripts/download_data.py`: baja todo el universo de `config/` a la caché y muestra un resumen (símbolo, fuente, primera/última fecha, nº de velas).

### 4. Estrategias — `src/tlab/strategies/`
- `base.py`: protocolo `generate_signals(bars: DataFrame, params: dict) -> DataFrame` con columnas `entry` (bool), `exit` (bool), `stop_price` (float, para la entrada de esa vela), opcional `rank` (float, mayor = mejor). Funciones **puras**.
- Un módulo por candidata de `docs/hipotesis.md`, implementado **al pie de la letra**, más `demo_sma.py` (cruce de medias simple) marcado como **DEMO**, solo para probar la tubería.
- `indicators.py`: SMA, EMA, ATR (de Wilder), RSI (de Wilder), Donchian, momentum/ROC, etc., todos causales (solo datos pasados).

### 5. Riesgo — `src/tlab/risk.py` (lo usarán el backtest **y** el ejecutor diario)
- `position_size(equity, entry_price, stop_price, risk_pct, costs, asset_class, allow_fractional) -> qty`: cantidad tal que la pérdida si salta el stop, **incluyendo costes de entrada y salida**, ≤ `risk_pct × equity`. Redondea **hacia abajo** (acciones enteras para ETFs; cripto a la precisión permitida). Si sale 0, no se opera.
- `apply_limits(...)`: máx. posiciones, exposición bruta ≤ 100 % del equity, caja disponible.
- `check_kill_switch(equity_series_or_peak, equity_now, threshold) -> bool`.

### 6. Motores — `src/tlab/backtest/`
- `costs.py`: comisión + slippage por lado según clase de activo; multiplicador de estrés.
- `portfolio_sim.py` (**motor de referencia para el veredicto**): bucle vela a vela, multiactivo, caja compartida. Reglas:
  - señal en la vela `t` → orden a la **apertura de `t+1`** (precio de apertura ± slippage en contra);
  - stop: si `low ≤ stop` en una vela, sale **al stop**; si la vela **abre ya por debajo del stop (gap)**, sale **a la apertura** (peor caso realista);
  - si en la misma vela se tocan stop y objetivo, se asume **el stop** (pesimista);
  - salida por señal a la apertura de la vela siguiente;
  - más de 3 señales → ordena por `rank` (empate: orden alfabético, determinista);
  - sizing con `risk.position_size` sobre el **equity actual**; kill switch aplicado a nivel cartera;
  - registro de operaciones con: símbolo, fechas, precios, cantidad, stop inicial, R inicial (riesgo en $), P&L en $ y en R, costes, motivo de salida.
- `vbt_engine.py`: envoltorio de `vectorbt.Portfolio.from_signals` para análisis rápido **por activo** y para las rejillas de parámetros (señales desplazadas 1 vela, `price` = apertura de la vela de ejecución, `sl_stop` a partir de `stop_price`, `fees` y `slippage` desde `costs.py`). Compruébalo contra la doc de la versión instalada (en vectorbt 1.2 `SizeType` es `Amount, Value, Percent, TargetAmount, TargetValue, TargetPercent`).
- `walkforward.py`: genera ventanas cronológicas (entreno/prueba) sin solaparse en la parte de prueba, según `docs/hipotesis.md`.
- `robustness.py`: rejilla ±25 % por parámetro (y combinaciones vecinas), costes × 2, retraso de 1 vela, quitar las N mejores operaciones, Monte Carlo (barajar operaciones, semilla fija), subperiodos.

### 7. Métricas — `src/tlab/metrics.py`
Funciones puras sobre la curva de equity y la lista de operaciones: rentabilidad total, **CAGR**, volatilidad anualizada, **Sharpe** y **Sortino** (anualizados; factor 252 para acciones, 365 para cripto; tipo libre de riesgo 0), **máximo drawdown** (caída máxima desde un máximo) y su duración, **Calmar**, nº de operaciones, **win rate** (% de operaciones ganadoras), **expectancy** en $ y en **R**, profit factor, exposición media, duración media de las operaciones. Las mismas métricas para el **benchmark** (buy & hold) en el mismo periodo.

### 8. Informes — `src/tlab/report.py` y `scripts/backtest.py`
- `scripts/backtest.py --strategy <id> --mode {is,wf,oos,full,robust} [--costs {base,stress}] [--params archivo.toml]`.
- **El modo `oos` exige `--confirm-oos`** y escribe un registro en `reports/oos_log.csv` (fecha, estrategia, hash de parámetros). Si ya existe una ejecución OOS con otros parámetros para esa estrategia, se niega salvo `--force` (y lo deja anotado). Así evitamos mirar el OOS muchas veces.
- Salida en `reports/<id>/<modo>_<AAAAMMDD-HHMM>/`: `resumen.md` (tabla de métricas estrategia vs benchmark, fuente y fechas de datos, costes usados, parámetros, nº de variantes probadas hasta la fecha), `trades.csv`, `equity.csv`, y opcional `informe.html`.
- Cada ejecución añade una línea a `docs/registro_pruebas.md`.

### 9. Guardia de seguridad — `src/tlab/broker/guard.py`
`assert_paper_only()` que lanza excepción si `ALPACA_PAPER_TRADE` no es exactamente `true`, si aparece una URL base que no sea la de paper, o si alguien intenta crear un `TradingClient` con `paper=False`. Debe llamarse en cualquier código que hable con el broker.

## Tests obligatorios (`tests/`, sin red por defecto)
Usa datos sintéticos deterministas (`tests/conftest.py`) y, si hace falta, pequeños CSV en `tests/fixtures/`.

| Test | Qué demuestra |
|---|---|
| `test_no_lookahead_truncation` | Para **cada** estrategia: las señales calculadas con datos hasta `t` son idénticas a las calculadas con toda la serie, para todo instante ≤ `t` (probar varios `t`). |
| `test_no_lookahead_poison` | Cambiar los datos posteriores a `t` (p. ej. multiplicarlos por 10 o poner NaN) no cambia ninguna señal ≤ `t`. |
| `test_execution_next_open` | Una señal en `t` se ejecuta al precio de apertura de `t+1` más slippage en contra. |
| `test_stop_intrabar_and_gap` | Stop tocado dentro de la vela → sale al stop; apertura por debajo del stop → sale a la apertura. Stop y objetivo en la misma vela → gana el stop. |
| `test_costs_applied_both_sides` | Con costes = 0 y con costes > 0, la diferencia de P&L coincide con lo calculado a mano; el estrés × 2 lo duplica. |
| `test_position_size_risk_cap` | La pérdida al stop (con costes) nunca supera el 1 % del equity; redondeo hacia abajo; cantidad 0 → no hay operación. |
| `test_max_positions` | Nunca hay más de 3 posiciones abiertas aunque haya 10 señales; el desempate es determinista. |
| `test_no_leverage` | La exposición bruta nunca supera el equity; nunca hay cantidades negativas (cortos). |
| `test_kill_switch` | Una caída > 10 % desde el máximo cierra todo y bloquea entradas posteriores. |
| `test_metrics_known_values` | Sharpe, máx. drawdown, CAGR, expectancy calculados sobre series pequeñas con resultado conocido a mano. |
| `test_engines_agree_single_asset` | En un caso de 1 activo sin límites de cartera, `portfolio_sim` y `vbt_engine` dan nº de operaciones idéntico y rentabilidad total con diferencia < 0,5 puntos porcentuales (explica cualquier diferencia). |
| `test_walkforward_windows` | Ventanas cronológicas, sin solape en la parte de prueba, cubren el periodo pedido. |
| `test_oos_guard` | `--mode oos` sin `--confirm-oos` falla; segunda ejecución con otros parámetros falla sin `--force`. |
| `test_cache_no_network` | Segunda carga idéntica no llama a la red (mock del cliente). |
| `test_validate_bars` | Detecta OHLC incoherente y huecos. |
| `test_guard_paper_only` | La guardia rechaza `ALPACA_PAPER_TRADE=false`, URL real y `paper=False`. |
| `test_strategy_<id>_cases` | Los casos a mano de `docs/hipotesis.md` §6 para cada candidata dan la señal esperada. |
| `test_report_sections` | El `resumen.md` contiene las secciones obligatorias y la tabla vs benchmark. |

Opcionales con `@pytest.mark.network`: descarga real de SPY y BTC/USD de 5 días.

## Criterios de aceptación (todos)
1. `uv sync` desde cero sin errores.
2. `uv run ruff check . && uv run ruff format --check .` sin errores.
3. `uv run pytest -q` en **verde**, con todos los tests de la tabla presentes. Pega en tu respuesta el resumen real de pytest (nº de tests pasados).
4. `uv run python scripts/download_data.py` descarga y cachea el universo (si no hay claves, usa yfinance y lo dice).
5. `uv run python scripts/backtest.py --strategy demo_sma --mode full` termina y genera `reports/demo_sma/.../resumen.md`.
6. Para cada candidata, `--mode is` funciona (genera informe). **No** ejecutes `--mode oos` (eso lo hace Fable en el paso 3).
7. `docs/progreso_paso2.md` con: qué está hecho, decisiones tomadas ante ambigüedades, limitaciones conocidas (p. ej. qué no modela el simulador: dividendos en paper, subastas, liquidez).

## Condiciones de parada
- **No interpretes resultados** ni digas si una estrategia "es buena". Eso es el paso 3.
- **No toques** `docs/hipotesis.md` ni los criterios. Si encuentras un error en la especificación, apúntalo en `docs/progreso_paso2.md` como "PREGUNTA PARA FABLE".
- Si un test de look-ahead falla, **no lo desactives**: arregla el código. Si no sabes, para y documenta.
- Si llevas 3 intentos fallidos con el mismo error de dependencias, para y documenta el error exacto.
- Nada de red en los tests por defecto. Nada de claves en el código ni en los logs.
- Al terminar, resume en 10 líneas qué hay, cómo se usa y qué queda pendiente.
