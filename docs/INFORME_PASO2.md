# Informe del paso 2 — implementación de las candidatas
Generado: 2026-11-11 (hora de Madrid). Rama `paso2/candidatas` (sale de `prep/motor-backtest` + `main` con el paso 1).

> No es asesoramiento financiero. Solo paper. **Este informe no contiene ningún resultado de
> rentabilidad de las candidatas**: no se ha ejecutado ningún backtest suyo (ver §4).

## 1. Qué se ha implementado (`docs/tareas_sonnet.md`)

| # | Tarea | Estado |
|---|---|---|
| 1 | `DBC`, `VNQ`, `DIA`, `LTC/USD`, `BCH/USD` en `settings.toml`, descargados; primeras fechas anotadas (§2) | hecho |
| 2 | Contraste yfinance ↔ Alpaca: `scripts/check_alpaca_vs_yf.py` + `src/tlab/data/crosscheck.py` (tolerancias documentadas en el módulo) | **programado, sin ejecutar**: en este ordenador no hay claves. Se ejecuta en el PC de Jorge (§5) |
| 3 | `costs.crypto.slippage_bps = 20` | hecho |
| 4 | Tope por posición `max_position_fraction = 0.3333` (equity/3) en `risk.apply_limits` y en el simulador, con los tests de §6.4 | hecho |
| 5 | `risk_per_trade`, `start`, `is_end`, `end` por estrategia en su TOML; cada activo entra al universo con ≥ 365 velas | hecho (runner y `targets.py`, que usan las herramientas de azar/rejilla/Monte Carlo) |
| 6 | `donchian_crypto`, `donchian_etf` (reutilizan `donchian_atr.generate_signals` tal cual), `tsmom_etf`, `rsi2_etf`; un TOML por id con `status = "preregistrada"`; registradas en `SIGNAL_STRATEGIES` (entran solas en los tests de look-ahead) | hecho |
| 7 | Walk-forward §3: entrenamiento creciente, ventanas con fechas fijas (8 × 1 año en ETFs; 6 × 9 meses en cripto), elección por Sharpe en la rejilla ±25 % (empate → la más cercana a la de por defecto), ventanas sin operaciones excluidas, ≥ 5 válidas | hecho (`--mode wf`, solo IS) |
| 8 | Informes: episodios de kill switch con reinicio del máximo, "quitar las 5 mejores", "quitar el mejor activo", subperiodos con las fechas de §4 (por fecha de entrada), por activo, exposición media, calibración de riesgo 1 / 0,75 / 0,5 % (P1) | hecho (`--mode is` de las candidatas) |
| 9 | Benchmarks con costes: buy & hold SPY y BTC; 60/40 SPY/IEF y 50 % BTC / 50 % caja con rebalanceo mensual | hecho (se añadió `always_rebalance` al simulador de pesos: antes, con pesos constantes, no rebalanceaba nunca) |
| 10 | `ruff` y `pytest` en verde | hecho (§3) |

Otras cosas hechas por seguridad:
- **Candado OOS ampliado:** en las candidatas, `--mode full` también exige `--confirm-oos` (incluye el OOS). `--mode wf` y `--mode robust` se quedan dentro del IS. Los datos se recortan a `end = 2026-10-31`.
- **Fuente de datos fija:** los TOML de las candidatas llevan `data_source = "yfinance"`. Sin esto, en el PC de Jorge (con claves en `.env`) el modo `auto` usaría Alpaca, que solo tiene datos desde 2016 (ETFs) y 2021 (cripto), y las fechas pre-registradas no se podrían cumplir.
- **P1:** los TOML llevan `kill_switch_in_backtest = false`; las métricas se miden sin kill switch y los episodios se cuentan aparte. La regla dura 6 no se toca (el ejecutor diario sigue con su kill switch).
- Acciones enteras en ETFs (P5) y cripto en fracciones de 0,000001: ya lo hacía el motor; hay tests.

## 2. Datos (yfinance, descargados hoy)

Primera vela real en yfinance de los símbolos nuevos o a verificar: `DBC` 2006-02-06 · `VNQ` 2004-09-29 · `DIA` 2003-01-02 · `BTC-USD` 2014-09-17 · `LTC-USD` 2014-09-17 · `ETH-USD` **2017-11-09** · `BCH-USD` **2017-11-09**. Las fechas que §2 daba "a verificar" se confirman.

Con la regla de ≥ 365 velas, estos activos entran al universo después del inicio de la simulación (todos los demás ya están al empezar):
- H1: `ETH/USD` y `BCH/USD` el **2018-11-08** (inicio 2015-10-01).
- H2 y H4: `DBC` el **2007-07-19** (inicio 2007-07-01).
- H3: ninguno.

Ninguna fecha impide empezar en las de §3. Última vela común antes del fin pre-registrado: 2026-10-30 (ETFs) y 2026-10-31 (cripto).

## 3. Tests

`uv run ruff check . && uv run ruff format --check . && uv run pytest -q -m 'not network'` → `All checks passed!` · `102 files already formatted` → **157 pasados, 2 saltados, 2 deseleccionados (los de red)**.
Antes de este paso: 109 pasados, 2 saltados. Tests nuevos:
- `tests/test_candidates.py`: casos a mano D1, D2, D3 (para `donchian_crypto` y `donchian_etf`), T1, T2, T3, R1, R2, R3 de §6; sizing y tope de §6.4 (IEF 52 → 35, SPY 4 / 7 → 5, BTC 0,012708, GLD 5, QQQ 4); el tope en el simulador; riesgo ≤ 1 % y coste ≤ equity/3 en 200 casos al azar; episodios de kill switch con reinicio; calibración P1; quitar el mejor activo; subperiodos por fecha de entrada; ventanas WF con las fechas de §3; desempate del WF; que los 4 TOML coinciden con `hipotesis.md` (universo, fechas, parámetros, rejilla, presupuesto ≤ 40); `settings.toml`; el runner de candidatas en IS / WF / robust con datos sintéticos; que `oos` y `full` están bloqueados sin `--confirm-oos`; benchmark 50/50 con rebalanceo mensual; y que `targets.py` sigue el TOML.
- `tests/test_crosscheck.py`: comparación idéntica, desfase de un día, ruido dentro y fuera de tolerancia, días que faltan, y que el script sale con código 0 sin claves.
- `tests/test_lookahead.py`: las 4 candidatas entran solas (truncado y "envenenado" del futuro).

## 4. Backtests in-sample: NO ejecutados (conflicto con el pre-registro)

Se pidió ejecutar los backtests in-sample de las 4 candidatas, pero **`docs/tareas_sonnet.md` (tarea 10, escrita por Fable en el paso 1) lo prohíbe expresamente**: *"No ejecutar todavía los backtests in-sample de las candidatas: los lanza Fable en el paso 3, después de auditar el motor (fase A)"*, y el mismo archivo dice que ante un choque con el pre-registro hay que parar y preguntar. Además, cada ejecución gasta presupuesto de variantes (§3, máximo 40 por candidata) y ver resultados IS antes de la auditoría del motor contamina el proceso.

Por eso **no hay tabla de métricas in-sample** en este informe: no hay ningún número que no haya salido de un script, y no se ha añadido ninguna fila a `docs/registro_pruebas.md` (no hubo pruebas). Lo único ejecutado sobre datos reales es la descarga y la comprobación de fechas de §2 (sin simular nada).

Cuando Jorge o Fable lo decidan, los comandos (solo IS; cada ejecución se anota sola en el registro) son:
```bash
uv run python scripts/backtest.py --strategy donchian_crypto --mode is   # métricas + calibración P1 + episodios kill switch
uv run python scripts/backtest.py --strategy donchian_crypto --mode wf   # walk-forward §3 (criterio 5)
uv run python scripts/backtest.py --strategy donchian_crypto --mode robust  # rejilla ±25 %, costes ×2, retraso, Monte Carlo (6–10)
# igual con tsmom_etf, rsi2_etf y donchian_etf
```
El informe de `--mode is` ya trae la tabla que se pedía: operaciones, CAGR, DD máx., Sharpe, expectancy en R, episodios de kill switch y el riesgo que seleccionaría P1.

## 5. PENDIENTE PARA FABLE (ambigüedades y cómo se han resuelto)

Se ha elegido siempre la opción más literal o más conservadora. Fable puede cambiarlas antes del primer OOS.

1. **IS ahora o en el paso 3** (§4 de este informe). No se ha ejecutado. Decide Jorge o Fable.
2. **"≥ 365 velas"** se cuenta en velas del propio activo (en ETFs son unos 17 meses, no un año natural). Por eso `DBC` entra el 2007-07-19 y no el 2007-07-01. La alternativa sería contar 365 días naturales.
3. **Tope equity/3** = `0.3333 × equity` (el valor de §6.4), aplicado al coste con slippage y comisión de entrada, sobre el equity a la apertura. Cuadra con todos los ejemplos de §2 y §6.4.
4. **Reinicio del máximo en los episodios de kill switch:** el máximo pasa a ser el equity del día en que salta el episodio y el siguiente episodio se mide desde ahí. La alternativa sería esperar a recuperar el máximo anterior. Se mide sobre la equity al cierre diario.
5. **Calibración P1:** DD máximo sobre la equity al cierre diario del IS, con el kill switch desactivado. Las ejecuciones al 0,75 % y al 0,5 % se anotan en el registro como "calibración de riesgo" (cuentan para el presupuesto de 40).
6. **Subperiodos que cruzan IS y OOS** (ETFs 2020-07-01 → 2026-10-31; cripto 2023-03-01 → 2026-10-31): en `--mode is` solo se informa de la parte IS. El criterio 11 completo necesita las operaciones del periodo entero, así que se evaluará después del OOS.
7. **Walk-forward:**
   - cada ventana de prueba arranca sin posiciones y con 10.000 $, así que una señal del último día de entrenamiento no se ejecuta;
   - lo que queda abierto al final de la ventana se cierra al último cierre, con costes, y cuenta en el neto;
   - "positiva" = equity final − 10.000 $ > 0;
   - el Sharpe de entrenamiento se anualiza con 365 en cripto y 252 en ETFs, y un Sharpe NaN cuenta como el peor;
   - las ejecuciones de entrenamiento no se anotan una a una en el registro: son las mismas combinaciones de la rejilla y solo se anota la fila del WF.
8. **Criterio 6:** una vecina sin operaciones cuenta como fallo. "Vecinas" = las 26 combinaciones de la rejilla distintas de la central (8 en H2).
9. **Benchmarks:** buy & hold en fracciones; el benchmark informativo compra en la segunda vela y luego rebalancea en la primera sesión de cada mes, con costes.
10. **Contraste yfinance ↔ Alpaca, tolerancias** (fijadas antes de ver datos reales):
    - ETFs: |Δ rentabilidad diaria| ≤ 10 pb en ≥ 99 % de los días y correlación ≥ 0,999;
    - cripto: ≤ 100 pb en ≥ 95 % de los días y correlación ≥ 0,99;
    - en los dos: ≤ 2 % de días que falten en una de las fuentes, y desfase de calendario 0.
    Si algo falla, el script sale con código 1 y hay que parar e investigar.
11. **No tocado:** el ejecutor diario y el paper (paso 5). La ejecución de `random_benchmark.py`, `param_sweep.py` y `montecarlo.py` sobre las candidatas es del paso 3; ya leen el periodo, la entrada por activo, el riesgo y el tope del TOML.
