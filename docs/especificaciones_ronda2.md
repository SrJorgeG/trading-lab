# Especificaciones de implementación, ronda 2 (R2-1 … R2-18) — 2026-11-12 (hora de Madrid)

> Para Sonnet. Detalla **cómo** implementar las tareas «Ronda 2» de `docs/tareas_sonnet.md`
> (R2-1 a R2-13 y los añadidos de la auditoría R2-14 a R2-18). **Qué** se prueba y con qué
> criterios lo fija `docs/hipotesis_ronda2.md` (con sus enmiendas E1–E14); si este documento
> choca con él, **manda el pre-registro** y se avisa a Fable.
> Escrito antes de que exista código, datos o resultados de H5–H7. No es asesoramiento
> financiero. Solo paper.

**Sobre los números de este documento.** No hay ninguna cifra de rentabilidad de mercado. Todos
los números son de **casos sintéticos** (precios inventados) y salen de: (a) un prototipo de
usar y tirar ejecutado en esta sesión contra el código actual del repo (`indicators.atr`,
`risk`, `portfolio_sim.simulate`, `robustness.param_grid`, `metrics`), marcado **[script]**;
o (b) aritmética directa que se puede rehacer con calculadora, marcada **[aritmética]**. El
prototipo no se guarda en el repo: los tests de Sonnet son los que fijan estos valores. No se
ha descargado ni abierto ningún dato de precios.

**Prohibiciones (siguen igual):** ningún backtest de `sector_mom`, `tom_etf` ni
`sector_lowvol` con datos reales (ni IS, ni «para ver si arranca»); ninguna rentabilidad
acumulada, media, ranking o gráfico de los símbolos nuevos (E13); no cambiar parámetros,
universos, fechas ni criterios; sin `git push`.

Glosario mínimo: **tramo** = cada periodo de la escalera (`is`, `replica`, `holdout_old`,
`holdout_new`, `full`). **Guarda** = código que se niega a ejecutar algo que no toca.
**Panel** = señales calculadas mirando varios activos a la vez. **Mono** = simulación al azar
de control. **pb** = punto básico (0,01 %). **Slippage** = diferencia entre el precio esperado
y el que te dan. **R** = resultado de una operación dividido por lo que se arriesgaba.

---

## 0. Hallazgos al leer el código (léelos antes de empezar)

Cosas que el código actual hace y que rompen o condicionan las tareas. Todas comprobadas
**[script]** o leídas en el fichero indicado.

| # | Hallazgo | Consecuencia |
|---|---|---|
| H-1 | `robustness.param_grid` con ±25 % da `lookback` ∈ {**94**, 126, 158} (Python redondea 94,5 a 94) y `entry_before_end` ∈ {**1**} (0,75 y 1,25 redondean a 1). El pre-registro fija {95, 126, 158} y {1, 2}. | Rejilla **explícita** en el TOML (`[robust_grid]`), §R2-5.3. Sin ella se probarían variantes distintas de las registradas. |
| H-2 | `tests/test_engine.py::test_kill_switch` usa el valor por defecto de `SimConfig` y una caída del 13,95 %: con el 15 % por defecto **deja de saltar**. `tests/test_candidates.py::test_calibrate_risk` usa el límite por defecto 0,10. | En R2-1/R2-2 esos dos tests pasan a dar el umbral **explícito** (0.10). No se cambia lo que comprueban. |
| H-3 | `runner.params_hash` y `report.append_registry` serializan `params`. Un `DatetimeIndex` dentro de `params` (el calendario de H6) revienta el hash y ensucia el registro. | El calendario **no** se guarda en los `params` del TOML ni en el hash: se inyecta al calcular señales (§R2-6.2). |
| H-4 | `runner.run_signals` y `Target.signals` llaman a la estrategia **activo por activo**. | Un único punto de entrada «de panel» para todas (§R2-6). |
| H-5 | `SimConfig.costs` es un coste por clase de activo para toda la simulación. | E11 exige coste por fecha: se añade un calendario de costes opcional (§R2-5.4). Es el **único** cambio de lógica en `portfolio_sim.py`, junto con los grupos de huecos de R2-12. |
| H-6 | `reports/oos_log.csv` ya existe con 4 columnas y 4 filas de la ronda 1. | Migración de cabecera idempotente (§R2-5.5); las filas viejas no se tocan. |
| H-7 | `append_registry` escribe CAGR, Sharpe y caída en `docs/registro_pruebas.md`. | En la réplica eso rompería el «a ciegas» de E3: allí la línea del registro solo lleva las cifras del criterio 15 (§R2-5.6). |
| H-8 | `settings.data.history_start = "2003-01-01"` lo usan las baselines y la ronda 1 (su «periodo completo» depende de él). | **No se toca.** La ronda 2 usa `history_start` propio en cada TOML (§R2-3.2). |
| H-9 | `yf_source` baja precios ajustados «a fecha de hoy». Alargar hacia atrás la caché de `SPY`, `IWM`, `EFA`, `EEM`, `IEF` pega dos descargas hechas en días distintos. | Comprobación de costura (§R2-18.6). |
| H-10 | `indicators.true_range` da valor en la primera vela (`high − low`), así que `ATR(n)` existe desde la vela `n`, no `n + 1`. | Los casos a mano con `atr_n = 1` tienen ATR desde la primera vela. No cambiar. |
| H-11 | En `simulate`, una entrada pendiente de un activo que **no tiene vela** al día siguiente se queda pendiente hasta su próxima vela. | Caso límite declarado en S10. No cambiar. |
| H-12 | Al final de cada tramo lo abierto se cierra al último cierre (`end_of_data`). En H6, IS acaba el 2020-12-31: la compra de ese día se cierra el mismo día. | Una operación recortada por tramo; ya pasaba en la ronda 1. Se deja y se declara en el informe. |

## 0.1 Precisiones de diseño (2026-11-12, antes del primer IS)

Decisiones que el pre-registro deja abiertas y que se fijan aquí para que no se puedan elegir
después. **Ninguna suaviza un criterio de §4.** Resumidas como enmienda **E14** en
`docs/hipotesis_ronda2.md`.

| # | Precisión | Por qué |
|---|---|---|
| D1 | Rejilla de robustez y de walk-forward = los valores **literales** de §2 del pre-registro, escritos en `[robust_grid]`. | H-1. |
| D2 | El calendario de H6 se inyecta en tiempo de ejecución; no forma parte del hash ni del registro. En backtest es el índice de `SPY` **ya recortado** en `end` (2026-10-31): octubre de 2026 no es «mes completo» y no hay entrada el 2026-10-29. | H-3. No usa nada posterior a `end`. |
| D3 | **Caja:** entre dos sesiones consecutivas el capital crece `(1 + y)^(días naturales / 365,25)`, con `y` = tipo **de la sesión anterior** (ya convertido a rentabilidad, E10). Sustituye al `^(1/252)` de la tarea R2-4. | Con `1/252` el CAGR de una serie constante no da el tipo (en un calendario de lunes a viernes sale 5,18 % para un 5 % **[script]**); con días naturales da exactamente 5,00 % **[script]** y es como se devenga el interés. En calendario real la diferencia es de centésimas y va en contra de la candidata. |
| D4 | **Guarda de tramos:** clave = (estrategia, tramo, hash, costes, retraso, tipo). El hash cubre `params` **y** `risk_per_trade`. No existe `--force` para los tramos de la ronda 2. Hace falta `frozen = true` en el TOML para pasar del IS. | E2 y §3.1. |
| D5 | En la réplica, el registro de pruebas y la salida por pantalla solo llevan expectancy, Sharpe, percentiles frente a los monos y nº de operaciones. | E3. |
| D6 | Mono de H6 (`window`): la señal de venta es **sostenida** (como la de la candidata, E6) y el «repetir el sorteo» de E5 se implementa sorteando uniformemente entre las sesiones **válidas** (da la misma distribución que repetir y siempre termina). | Sin la salida sostenida el mono no sería idéntico a la candidata cuando falta una vela. |
| D7 | p de los monos: se mantiene la fórmula del repo, `(1 + k) / (N + 1)` con `k` = nº de monos con Sharpe ≥ el real. Un mono sin Sharpe (sin operaciones) cuenta como «no supera» y **sigue contando en N**. Con N = 1.000, `p < 0,02` equivale a `k ≤ 19` tanto con esta fórmula como con la proporción simple `k / N` **[aritmética]**. | Evita que la definición de p sea elegible después. |
| D8 | El test «con ≤ 3 aptos, mono = candidata» solo se garantiza cuando la caja no limita ninguna compra (se construye así). | El orden de entrada decide quién se queda sin caja si no alcanza para todos. |
| D9 | Cartera combinada: límites de huecos por grupo (`sectores` ≤ 2, `tom` ≤ 1) y, en una misma apertura, **`SPY` entra el último** (su `rank` se fija en −∞). | Sin regla, H5 pondría a los sectores primero y H7 a `SPY` primero solo por el signo de su `rank`. |
| D10 | H5/H7 (principal y réplica): si algún símbolo del universo no tiene ≥ 365 velas al inicio del tramo, el script **se para** (no rebaraja el universo) y lo anota para Fable. H6: entrada escalonada (E8). | E8; un símbolo «a medias» ocuparía puesto en el ranking sin poder comprarse. |
| D11 | «Años» del criterio 16a = `metrics.years` de la curva de cada tramo (primera a última vela), el mismo reloj para la estrategia y para la caja. | Mismo reloj que el CAGR del repo. |
| D12 | En `full`, el benchmark `SPY`, el 60/40 y `IEF` usan el coste vigente en su fecha de compra (10 pb); el estrés × 2 multiplica todo el calendario de costes. | E11 no lo decía para los benchmarks. |
| D13 | «Efectivo rindiendo como la caja» (informativo) se calcula **a posteriori** sobre la curva ya simulada; no se vuelve a simular. | Es informativo; re-simular cambiaría tamaños y abriría otra variante. |
| D14 | `calibrate_risk` deja de tener límite por defecto; los 4 TOML de la ronda 1 ganan la clave `calibration_dd_limit = 0.10` (lo que ya se usó). | «Nada de números mágicos»; H-2. |

---

## 1. Orden recomendado y dependencias

```
Fase 0  R2-1 ──► R2-2                      (config y límites; desbloquea todo)
Fase 1  R2-3 + R2-18 ──► R2-4              (datos; necesita red y claves: PC de Jorge)
Fase 2  R2-6 ──► R2-7 (+R2-14 S5–S9)       (señales de panel y sectores)
             └─► R2-8 (+R2-15 C5–C8)       (cambio de mes)
Fase 3  R2-5 (+R2-17 guarda y coste por fecha) ──► R2-14 S10–S12, R2-15 C9
Fase 4  R2-9 (+R2-16)                      (monos; necesita R2-5, R2-6, R2-7, R2-8)
Fase 5  R2-10 (+R2-17 métricas)            (informe; necesita R2-4 y R2-5)
Fase 6  R2-11  ·  R2-12                    (banda del paper · cartera combinada)
Fase 7  R2-13                              (verde + informe para Fable)
```

- Las fases 1 y 2 no dependen entre sí: la 2 (y la 3, 4, 5, 6) se hace entera con datos
  sintéticos, **sin** esperar a los datos reales.
- Un commit por tarea (o por pareja tarea + sus tests), en español, con `ruff` y `pytest` en
  verde en cada uno.
- **Antes del primer IS (lo lanza Fable, no Sonnet):** R2-1 y R2-3/R2-18 hechos y la auditoría
  del motor repetida sobre el código nuevo.

Mapa de ficheros (nuevos en **negrita**):

| Fichero | Tareas |
|---|---|
| `config/settings.toml`, `src/tlab/config.py` | R2-1, R2-3, R2-17 |
| `src/tlab/risk.py`, `backtest/portfolio_sim.py`, `backtest/robustness.py`, `backtest/montecarlo.py`, `backtest/targets.py` | R2-1, R2-2, R2-5, R2-12 |
| `src/tlab/strategies/base.py`, `strategies/__init__.py` | R2-6 |
| **`src/tlab/strategies/sector_rank.py`**, **`config/strategies/sector_mom.toml`**, **`sector_lowvol.toml`** | R2-7 |
| **`src/tlab/strategies/tom_etf.py`**, **`src/tlab/data/calendar.py`**, **`config/strategies/tom_etf.toml`** | R2-8 |
| **`src/tlab/backtest/tranches.py`**, `backtest/costs.py`, `backtest/runner.py`, `scripts/backtest.py` | R2-5 |
| **`src/tlab/backtest/custom_monkeys.py`**, **`scripts/monkeys_r2.py`** | R2-9 |
| **`src/tlab/data/cash.py`** | R2-4 |
| `src/tlab/metrics.py`, **`src/tlab/backtest/criteria.py`** | R2-10, R2-17 |
| **`src/tlab/backtest/paper_band.py`** | R2-11 |
| **`src/tlab/backtest/combined.py`** | R2-12 |
| **`src/tlab/data/audit.py`**, **`scripts/check_data_r2.py`**, **`scripts/check_tradable.py`** | R2-3, R2-18 |
| **`tests/test_r2_*.py`** (uno por bloque), `tests/test_lookahead.py` | todas |
| **`docs/INFORME_RONDA2_IMPL.md`** | R2-13 |

Convenciones para todo lo nuevo: tipado en funciones públicas, docstring corto en español,
índices UTC, sin números mágicos (lo configurable va al TOML), funciones de señales **puras**.
Tests sin red; los que la usan llevan `@pytest.mark.network`.

---

## R2-1. Kill switch al 15 %

**Ficheros y cambios exactos** (el valor pasa de `0.10` a `0.15`):

| Sitio | Cambio |
|---|---|
| `config/settings.toml` → `[risk] kill_switch_drawdown` | `0.15` |
| `risk.check_kill_switch(..., threshold: float = 0.15)` | valor por defecto |
| `portfolio_sim.SimConfig.kill_switch_drawdown: float \| None = 0.15` | valor por defecto |
| `robustness.kill_switch_episodes(equity, threshold: float = 0.15)` | valor por defecto |
| `montecarlo.DEFAULT_KILL = 0.15` (y el texto de ayuda de `scripts/montecarlo.py`, «0.15 = 15 %») | constante |
| `targets.py`, `Target.with_kill_switch`: `self.meta.get("kill_threshold", 0.15)` | valor de reserva |
| `README.md` (línea «Kill switch… 10 %»), `prompts/01` (línea 12), `prompts/02` (tabla, `test_kill_switch`), `prompts/05` (paso 7 y `test_kill_switch_runner`) | texto «15 %» |
| `backtest/param_sweep.py` (≈ línea 492) y `scripts/run_baselines.py` (≈ línea 276) | el texto deja de llevar «10 %» fijo: se compone con `settings["risk"]["kill_switch_drawdown"]` |

**No se toca:** `reports/` (los informes de la ronda 1 no se regeneran), `docs/hipotesis.md`,
`docs/veredicto.md`, ni los tests que ya pasan `0.10` explícito.

**Tests que hay que adaptar (H-2):** en `tests/test_engine.py::test_kill_switch` pasar
`kill_switch_drawdown=0.10` a `cfg(...)`. Comprobado **[script]**: con 0.10 salta el
2020-01-06 (caída −13,95 %); con 0.15 no saltaría.

**Techo de las reglas duras (R2-17).** Nueva función en `config.py`:

```python
HARD_LIMITS = {
    "kill_switch_drawdown": 0.15,
    "risk_per_trade": 0.01,
    "max_positions": 3,
    "max_gross_exposure": 1.0,
}


class HardRuleError(ValueError): ...


def validate_settings(s: dict) -> dict:
    """Lanza HardRuleError si algún valor de [risk] supera el techo de las reglas duras
    (o es <= 0). Devuelve `s` sin cambios."""
```

`load_settings` llama siempre a `validate_settings`. El techo solo se aplica al cargar
configuración, **no** dentro de `SimConfig` (hay tests que simulan a propósito con otros
valores).

**Casos de prueba** (`tests/test_r2_config.py`):

| Caso | Entrada | Esperado |
|---|---|---|
| K1 | `check_kill_switch(10000.0, 8500.00, 0.15)` | `False` («más de un 15 %») **[script]** |
| K2 | `check_kill_switch(10000.0, 8499.99, 0.15)` | `True` **[script]** |
| K3 | `check_kill_switch(10000.0, 8499.99)` (sin umbral) | `True`; y con `8500.0` → `False` (prueba el valor por defecto) |
| K4 | `kill_switch_episodes(Series([100, 86, 84.9]))` sin umbral | solo la 3.ª fecha (84,9 < 85) **[aritmética]** |
| K5 | `load_settings()` | `s["risk"]["kill_switch_drawdown"] == 0.15` |
| K6 | `validate_settings` con `kill_switch_drawdown = 0.16` | `HardRuleError` |
| K7 | ídem con `risk_per_trade = 0.011`, `max_positions = 4`, `max_gross_exposure = 1.01` (uno cada vez) | `HardRuleError` |
| K8 | `validate_settings` con `kill_switch_drawdown = 0.10` (más estricto) | pasa |
| K9 | `SimConfig().kill_switch_drawdown` | `0.15` |

**Casos límite:** 8.500,00 exacto no salta (`10000 × (1 − 0.15)` da `8500.0` exacto en coma
flotante **[script]**; la comparación es `<` estricta). No añadir tolerancias.

**Aceptación:** `grep -rn "0\.10" src/tlab/risk.py src/tlab/backtest/portfolio_sim.py` sin
resultados en valores por defecto de kill switch; K1–K9 en verde; toda la batería anterior
sigue en verde con el único cambio de H-2.

---

## R2-2. Límite de calibración por estrategia

**Fichero:** `backtest/robustness.py`, `backtest/runner.py`, los TOML.

```python
def calibrate_risk(max_dd_by_level: dict[float, float], limit: float) -> float | None:
    """Mayor fracción de riesgo con |caída máxima IS| <= limit. None = ninguna."""
```

- `limit` pasa a ser **obligatorio** (D14).
- `runner.candidate_sections`: `limit = float(sc["calibration_dd_limit"])`; si la clave falta en
  una candidata → `KeyError` con mensaje claro. El umbral de los **episodios** de kill switch
  sigue saliendo de `settings` (son dos números distintos: 0,12 calibra, 0,15 para).
- Texto del informe: «Riesgo seleccionado (mayor con caída ≤ {limit} %; kill switch al {thr} %)».
- Añadir `calibration_dd_limit = 0.10  # ronda 1 (P1 de hipotesis.md)` a `donchian_crypto`,
  `donchian_etf`, `tsmom_etf`, `rsi2_etf`. Los tres TOML nuevos llevan `0.12`.

**Casos de prueba:**

| Caso | Entrada | Esperado |
|---|---|---|
| L1 | `{0.01: -0.13, 0.0075: -0.119, 0.005: -0.08}`, `limit=0.12` | `0.0075` |
| L2 | `{0.01: -0.12, …}`, `limit=0.12` | `0.01` (el borde entra: «≤ 12 %») |
| L3 | `{0.01: -0.20, 0.0075: -0.16, 0.005: -0.121}`, `limit=0.12` | `None` (muere en IS) |
| L4 | `calibrate_risk({...})` sin `limit` | `TypeError` |
| L5 | los 3 casos de `test_calibrate_risk` existentes con `limit=0.10` explícito | mismos resultados que hoy |
| L6 | `load_strategy_config(x)["calibration_dd_limit"]` | `0.10` en las 4 de la ronda 1; `0.12` en las 3 nuevas |

**Aceptación:** L1–L6 en verde; `test_runner_candidate_is_wf_robust` sigue en verde añadiendo
`"calibration_dd_limit": 0.10` a su `sc` sintético.

---

## R2-3. Datos nuevos

### R2-3.1 `config/settings.toml`
- Añadir a `[universe] equity`: `EWJ EWG EWU EWC EWQ EWI EWA EWL EWH MDY` (los 9 sectores ya
  están; `XLC` y `XLRE` se quedan en la lista pero ninguna estrategia de la ronda 2 los usa).
- **No** cambiar `[data] history_start` (H-8).
- Nueva tabla:

```toml
[data.round2]
history_start = "1993-01-01"     # yfinance devuelve desde la primera vela de cada símbolo
cash_symbol = "^IRX"             # letras a 3 meses, % anual
cash_fallback = "DTB3"           # CSV público de FRED
```

### R2-3.2 Carga
- Cada TOML de la ronda 2 lleva `history_start = "1993-01-01"`; `runner` y `targets` usan
  `sc.get("history_start", s["data"]["history_start"])`.
- `scripts/download_data.py`: nueva opción `--round2` que baja con yfinance, desde
  `data.round2.history_start`, la unión de `universe`, `replica_universe`, `benchmark` y
  `benchmark_info` de los tres TOML nuevos (24 símbolos + `IEF`), **sin** imprimir precios
  (solo primera/última fecha, nº de velas y avisos de `validate_bars`, como hoy).

### R2-3.3 Informe de inventario
Lo genera `scripts/check_data_r2.py` (detalle en R2-18) en
`reports/datos/r2_datos_<AAAAMMDD-HHMM>.md`.

**Regla de inicio (E8, D10), solo anotar:** el script escribe una sección «Para Fable» con:
- sectores: ¿los 9 tienen la vela 365 en o antes del 2000-07-01? Si no, primera fecha válida y
  «el inicio se retrasaría al primer día del mes siguiente» (la decisión es de Fable);
- países: lo mismo para los 9 `EW*`;
- H6: fecha de la vela 365 de `SPY`, `IWM`, `EFA`, `MDY`, `EEM`, `EWJ` (entrada escalonada).

**Aceptación:** el informe existe, no contiene ninguna rentabilidad, y la sección «Para Fable»
está rellena. Sonnet **no** edita fechas de ningún TOML.

---

## R2-4. Benchmark de caja

**Fichero nuevo:** `src/tlab/data/cash.py`.

```python
DAYS_PER_YEAR = 365.25  # el mismo reloj que metrics.years


def discount_to_yield(d: float | pd.Series) -> float | pd.Series:
    """Tipo de descuento (tanto por uno, base 360, letra a 91 días) → rentabilidad
    equivalente: y = 365·d / (360 − 91·d). E10."""


def load_tbill_rate(
    settings: dict, cache_dir: Path | None = None, source: str | None = None
) -> tuple[pd.Series, dict]:
    """Serie diaria (índice UTC) del tipo a 3 meses en tanto por uno y YA en base de
    rentabilidad. Segundo valor: {"source", "basis_original", "converted", "first", "last",
    "max_gap_days"} para el informe. Toca red (solo scripts y tests `network`)."""


def cash_equity(rate: pd.Series, index: pd.DatetimeIndex, init: float) -> pd.Series:
    """Capital en caja sobre `index`: eq[0] = init;
    eq[i] = eq[i−1] · (1 + y[i−1]) ** ((index[i] − index[i−1]).days / 365.25),
    con y = `rate` alineado a `index` rellenando hacia delante (último tipo conocido <= fecha).
    Función pura."""
```

**Reglas:**
- `^IRX` se baja con `YFinanceSource` (columna `close` = % anual → dividir entre 100). El
  símbolo se cachea como los demás.
- **Base (E10):** Sonnet busca la fuente que diga si `^IRX` es tipo de descuento. Si es
  descuento **o no se puede confirmar** → `discount_to_yield`. Lo usado y la fuente van en el
  `dict` y en `INFORME_RONDA2_IMPL.md`.
- **Alternativa:** si `^IRX` no existe, empieza después del 2000-06-01 o tiene algún hueco de
  más de **10 días naturales** entre 2000-07-01 y 2026-10-31 → `DTB3` de FRED (CSV público sin
  clave; valores «.» = sin dato; es tipo de descuento → conversión obligatoria). La petición no
  lleva ningún dato personal.
- `rate` sin dato anterior a `index[0]` → `ValueError` (no se inventa un tipo).
- Tipos negativos se aceptan tal cual; `NaN` se rellena hacia delante.

**Casos a mano** (`tests/test_r2_cash.py`, sin red):

| Caso | Entrada | Esperado |
|---|---|---|
| CA1 | `discount_to_yield(0.05)` | `0,0513434` (5,134 %) **[script]** |
| CA2 | `rate` constante 0,05; índice de días laborables 2020-01-01 → 2025-01-01; `init` 10.000 | `metrics.cagr` = 0,0500 (tolerancia 1e-9); capital final 12.764,09 **[script]** |
| CA3 | como CA2 con `rate = discount_to_yield(0.05)` | CAGR = 0,0513434 **[script]** |
| CA4 | fechas 2024-01-02, 01-03, 01-04, 01-08; `rate` = 0,05 · 0,05 · 0,10 · 0,10 | `[10000.0, 10001.3359, 10002.6720, 10013.1180]` **[script]**: los dos primeros pasos usan el 5 % (1 día cada uno) y el tercero el 10 % de la sesión **anterior** durante 4 días naturales |
| CA5 | CA4 con `NaN` el 01-03 | mismo resultado (se arrastra el 5 %) **[script]** |
| CA6 | `rate` que empieza después de `index[0]` | `ValueError` |
| CA7 (sin mirar al futuro) | multiplicar por 10 los tipos posteriores a una fecha `t` | el capital hasta `t` **incluida** no cambia; el de `t+1` tampoco (usa el tipo de `t`) |

**Aceptación:** CA1–CA7; `load_tbill_rate` con test `network` que solo comprueba fechas, que
los valores están entre −0,01 y 0,20 y que `max_gap_days` ≤ 10.

---

## R2-5. Tramos múltiples, guarda de un solo uso y coste por fecha

### R2-5.1 Esquema del TOML (los tres nuevos)

```toml
id = "sector_mom"                 # sector_lowvol / tom_etf
kind = "panel"                    # tom_etf: "signals"
status = "preregistrada"
frozen = false                    # Fable lo pone a true en el commit de congelación (E2)
universe = ["XLB","XLE","XLF","XLI","XLK","XLP","XLU","XLV","XLY"]
replica_universe = ["EWJ","EWG","EWU","EWC","EWQ","EWI","EWA","EWL","EWH"]
benchmark = "SPY"
benchmark_info = { SPY = 0.6, IEF = 0.4 }
fixed_income = "IEF"              # criterio 16d
fixed_income_from = "2002-08-01"
robust_keys = ["lookback", "atr_mult", "keep_n"]
start = "2007-07-01"              # = tramo is (se mantiene por compatibilidad con la ronda 1)
is_end = "2020-12-31"
end = "2026-10-31"
data_source = "yfinance"
history_start = "1993-01-01"
min_history_bars = 365
require_full_universe = true      # D10 (tom_etf: false → entrada escalonada)
risk_per_trade = 0.01             # PROVISIONAL hasta la calibración IS
risk_levels = [0.01, 0.0075, 0.005]
calibration_dd_limit = 0.12
kill_switch_in_backtest = false
cash_margin = 0.02                # criterios 16-IS, 16a, 16d
monkey_p_max = 0.02               # criterio 14
subperiods = [["2000-07-01","2007-06-30"], ["2007-07-01","2013-12-31"],
              ["2014-01-01","2020-06-30"], ["2020-07-01","2026-10-31"]]

[robust_grid]                     # D1: valores literales de hipotesis_ronda2.md §2
lookback = [95, 126, 158]
atr_mult = [2.25, 3.0, 3.75]
keep_n = [4, 5, 6]

[walkforward]
first_test = "2013-01-01"
test_months = 12
n_windows = 8
min_valid_windows = 5

[tranches.is]
start = "2007-07-01"
end = "2020-12-31"
universe = "universe"
slippage_bps = 5
[tranches.replica]
start = "2000-07-01"
end = "2026-10-31"
universe = "replica_universe"
slippage_bps = 15
[tranches.holdout_old]
start = "2000-07-01"
end = "2007-06-30"
universe = "universe"
slippage_bps = 10
[tranches.holdout_new]
start = "2021-01-01"
end = "2026-10-31"
universe = "universe"
slippage_bps = 5
[tranches.full]
start = "2000-07-01"
end = "2026-10-31"
universe = "universe"
slippage_schedule = [["2000-07-01", 10], ["2007-07-01", 5]]   # E11

[params]
rank_by = "mom"
lookback = 126
top_n = 3
keep_n = 5
atr_mult = 3.0
atr_n = 20
```

`tom_etf`: `universe = ["SPY","IWM","EFA"]`, `replica_universe = ["MDY","EEM","EWJ"]`,
`robust_keys = ["entry_before_end","exit_day","atr_mult"]`,
`[robust_grid] entry_before_end = [1, 2]`, `exit_day = [2, 3, 4]`, `atr_mult = [2.25, 3.0, 3.75]`,
`[params] entry_before_end = 1, exit_day = 3, atr_mult = 3.0, atr_n = 20`.

### R2-5.2 Módulo nuevo `src/tlab/backtest/tranches.py`

```python
TRANCHE_ORDER = ("replica", "holdout_old", "holdout_new", "full")  # tras el IS
IS_MODES = ("is", "wf", "robust")
RUN_KINDS = ("candidata", "monos_rank", "monos_persist", "monos_window", "combo")
ALLOWED_STRESS = {("base", 0), ("stress", 0), ("base", 1)}  # (costes, retraso)


@dataclass(frozen=True)
class Tranche:
    name: str
    start: pd.Timestamp  # UTC
    end: pd.Timestamp  # UTC, inclusive
    universe: list[str]
    slippage_bps: float | None  # coste único…
    schedule: tuple[tuple[pd.Timestamp, float], ...] | None  # …o calendario (solo `full`)


class TrancheGuardError(OOSGuardError): ...


def is_round2(sc: dict) -> bool:
    """True si el TOML define [tranches]."""


def load_tranche(sc: dict, name: str) -> Tranche:
    """Lee [tranches.<name>]. Errores (ValueError): tramo desconocido; start > end; ni
    `slippage_bps` ni `slippage_schedule` (o los dos); calendario desordenado o cuya primera
    fecha es posterior a `start`; `is` distinto de (sc["start"], sc["is_end"]); cualquier
    tramo con `end` posterior a sc["end"]."""


def tranche_costs(
    settings: dict, tr: Tranche, costs_mode: str = "base"
) -> tuple[dict[str, CostModel], CostSchedule | None]:
    """Costes del tramo: slippage del tramo (× multiplicador si `stress`), comisión por acción
    de settings. Con calendario devuelve además el CostSchedule (y el dict = primer tramo)."""


def tranche_hash(params: dict, risk_per_trade: float) -> str:
    """runner.params_hash({**params, "risk_per_trade": risk_per_trade})."""


def check_tranche_guard(
    log_path: Path,
    strategy: str,
    tranche: str,
    h: str,
    costs_mode: str,
    entry_delay: int,
    kind: str,
    frozen: bool,
    confirm: bool,
    report: str = "",
) -> None:
    """Valida y ANOTA (antes de simular) una ejecución de los peldaños 1–3 o de `full`.
    Lanza TrancheGuardError si no procede. Ver reglas abajo."""


def assert_is_allowed(sc: dict, a: pd.Timestamp, b: pd.Timestamp) -> None:
    """Para is/wf/robust de la ronda 2: error si `frozen` es true (E2: tras congelar no hay
    más IS) o si [a, b] se sale de [start, is_end]."""
```

**Reglas de `check_tranche_guard`, en este orden** (cada una con su mensaje en español):
1. `confirm` falso → error («el tramo se mira una vez: usa `--confirm-tranche`»).
2. `frozen` falso → error («falta el commit de congelación, E2»).
3. `(costs_mode, entry_delay)` ∉ `ALLOWED_STRESS` → error.
4. Existe en el log una fila de esta estrategia y este tramo con **otro** hash → error («tramo
   ya gastado con otros parámetros»). No hay `--force`.
5. Existe ya una fila idéntica (estrategia, tramo, hash, costes, retraso, tipo) → error
   («ya ejecutado»).
6. **Orden:** para `tranche = TRANCHE_ORDER[i]` con `i > 0` debe existir la fila
   `(estrategia, TRANCHE_ORDER[i−1], hash, "base", 0, "candidata")`; si no → error.
7. Una fila que no sea la base (`stress`, retraso 1, `monos_*`) exige que exista la base
   `candidata` del **mismo** tramo.
8. `kind = "combo"`: solo en `holdout_old`, `holdout_new`, `full` (E12); se guarda con
   `strategy = "<sectores>+tom_etf"` y sigue las reglas 4–6 con su propia cadena (su primer
   tramo es `holdout_old`).
9. Si todo pasa, **se escribe la fila** y luego se simula. Si la simulación falla después, la
   fila se queda: recuperarlo es una decisión de Fable, a mano y anotada en
   `docs/registro_pruebas.md`. El script lo dice en el mensaje de error.

La guarda no sabe si la candidata «aprobó» el tramo anterior: eso lo decide Fable leyendo el
informe. La guarda solo impide saltarse o repetir.

### R2-5.3 Rejilla explícita (D1)

```python
def param_grid(
    params: dict, keys: list[str], pct: float = 0.25, explicit: dict[str, list] | None = None
) -> list[dict]:
    """Si `explicit` trae valores para una clave, se usan tal cual (deben incluir el valor por
    defecto; si no, ValueError). Las claves sin lista explícita siguen con ±pct."""
```

`runner.robust_section` y `runner.walk_forward_fixed` pasan `explicit=sc.get("robust_grid")`.
Las estrategias de la ronda 1 no tienen `[robust_grid]` y no cambian.

| Caso | Entrada | Esperado |
|---|---|---|
| G1 | `param_grid({"lookback": 126}, ["lookback"])` | `[94, 126, 158]` (lo de hoy **[script]**; documenta H-1) |
| G2 | con `explicit={"lookback": [95, 126, 158]}` | `[95, 126, 158]` |
| G3 | TOML de `sector_mom` y `sector_lowvol` | 27 combinaciones; con los 3 niveles de riesgo, ≤ 30 variantes |
| G4 | TOML de `tom_etf` | 18 combinaciones: `entry_before_end` {1, 2} × `exit_day` {2, 3, 4} × `atr_mult` {2,25, 3,0, 3,75} |
| G5 | `explicit={"lookback": [95, 158]}` (sin el 126) | `ValueError` |
| G6 | `pick_best` con la rejilla de `tom_etf` y todos los Sharpe iguales | elige la de por defecto |

### R2-5.4 Coste por fecha (E11) — `backtest/costs.py` y `portfolio_sim.py`

```python
@dataclass(frozen=True)
class CostSchedule:
    """Costes que cambian con la fecha. `steps` ordenado: (desde, {clase: CostModel})."""

    steps: tuple[tuple[pd.Timestamp, dict[str, CostModel]], ...]

    def at(self, t: pd.Timestamp) -> dict[str, CostModel]:
        """Costes vigentes en `t`: los del último paso con `desde <= t`. ValueError si `t` es
        anterior al primer paso."""

    def scaled(self, mult: float) -> CostSchedule: ...
```

`SimConfig` gana `cost_schedule: CostSchedule | None = None`. En `simulate`:
- función interna `cm_at(s, t)` = `cfg.cost_schedule.at(t)[ac[s]]` si hay calendario; si no,
  `cfg.costs[ac[s]]` (comportamiento idéntico al de hoy);
- **entrada** en `t`: precio de compra, tamaño (`position_size`, `apply_limits`) y `risk_usd`
  usan `cm_at(s, t)` para **los dos lados** (E11);
- **salida** en `t'` (cualquier motivo, incluido `end_of_data`): `cm_at(s, t')`.

**Caso a mano CF1** (5 sesiones: 2007-06-27, 06-28, 06-29, 07-02, 07-03; un activo `SPY`;
10.000 $; riesgo 1 %; tope 0,3333; calendario `[(2000-07-01, 10 pb), (2007-07-01, 5 pb)]`;
velas `(open, high, low, close)`: `(100,100,100,100)`, `(100,100,100,100)`,
`(100,105,100,105)`, `(110,111,109,110)`, `(110,110,110,110)`; señales con
`manual_signals(index, entries=[1], exits=[2], stop=94.0)`) **[script, aritmética con
`CostModel`]**:

| Paso | Valor |
|---|---|
| Compra el 2007-06-29 a la apertura 100 con 10 pb | precio 100,10 |
| Riesgo por unidad (10 pb en los dos lados) | 100,10 − 94 × 0,999 = **6,194** |
| Cantidad | `floor(100 / 6,194)` = **16** (el tope de equity/3 permitiría 33) |
| `risk_usd` | 99,104 |
| Venta el 2007-07-02 a la apertura 110 con **5 pb** | precio **109,945** |
| Resultado | 16 × (109,945 − 100,10) = **+157,52 $ = +1,589 R** |
| Control: si la venta pagara 10 pb (error) | 109,89 → +156,64 $ |

- **CF2 (estrés × 2):** mismo caso con `schedule.scaled(2)` → compra a 100,20; riesgo por
  unidad 6,388; **15** acciones; venta a 109,89; **+145,35 $** **[script]**.
- **CF3:** sin calendario (`cost_schedule=None`) todos los tests existentes del motor dan lo
  mismo que antes (no se toca ninguna aserción).
- **CF4:** `CostSchedule.at` con fecha anterior al primer paso → `ValueError`; el 2007-06-30
  (sábado, sin vela) pertenece al primer paso y el 2007-07-01 al segundo.

### R2-5.5 `reports/oos_log.csv`

Columnas nuevas, en este orden tras las cuatro actuales: `tranche`, `costs`, `entry_delay`,
`kind`, `report`.

```python
def migrate_oos_log(path: Path) -> None:
    """Si la cabecera es la antigua (4 columnas), reescribe el fichero con las 9 columnas y
    las celdas nuevas vacías en las filas viejas. Idempotente. No borra ni reordena filas."""
```

`check_oos_guard` (ronda 1) sigue funcionando: tras migrar escribe las 9 columnas con
`tranche = "oos"` o `"full"`, `costs` y `entry_delay` reales, `kind = "candidata"` (cubre la
tarea pendiente del paso 3). Las filas con `tranche` vacío se leen como «ronda 1».

### R2-5.6 `runner.run_backtest` y `scripts/backtest.py`

- `MODES = ("is", "wf", "oos", "full", "robust", "replica", "holdout_old", "holdout_new")`.
- Nuevo parámetro `confirm_tranche: bool = False` (`--confirm-tranche`).
- Rama nueva cuando `is_round2(sc)`:
  1. `oos` no existe para la ronda 2 → `ValueError`.
  2. `tr = load_tranche(sc, "is" if mode in IS_MODES else mode)`.
  3. `is`/`wf`/`robust` → `assert_is_allowed`; el resto → `check_tranche_guard`.
  4. Universo = `tr.universe`; datos desde `sc["history_start"]`, recortados en `sc["end"]`.
  5. `entry_from = asset_entry_dates(bars, 365)`; si `require_full_universe` y algún
     `entry_from[s] > tr.start` → `ValueError` con la lista de símbolos (D10).
  6. `costs, schedule = tranche_costs(s, tr, costs_mode)`;
     `cfg = replace(make_cfg(s, sc, costs), cost_schedule=schedule)`.
  7. Señales con `resolve_signal_fn` (§R2-6.2); simulación en `[tr.start, tr.end]`.
  8. Tras simular: `assert res.equity.index[-1] <= tr.end` y, en modos IS,
     `res.equity.index[-1] <= is_end`.
  9. Informe en `reports/<estrategia>/<tramo>[_stress][_delay1]_<sello>/`.
- **Réplica a ciegas (E3, D5):** en `replica` se escriben dos cosas:
  `criterio15.md` (expectancy R, Sharpe, nº de operaciones y, cuando se ejecuten los monos,
  percentiles) y `detalle/` (resumen, equity, operaciones). `run_backtest` devuelve la ruta de
  `criterio15.md`; la línea del registro lleva solo «expectancy X R, Sharpe Y, n=Z»; por
  pantalla solo sale esa ruta. `detalle/README.md` empieza con: «NO ABRIR hasta que la
  candidata termine los peldaños 2–3 o muera (E3)».
- En los demás tramos el registro sigue como hoy, con el tramo y `f` en la columna «conjunto».

**Casos de prueba** (`tests/test_r2_tranches.py`; datos sintéticos con `make_bars`, estrategia
`demo_sma` o un `sc` sintético con `[tranches]` en miniatura; `tmp_path` para el log):

| Caso | Secuencia | Esperado |
|---|---|---|
| T1 | `replica` base sin `confirm` | `TrancheGuardError` |
| T2 | `replica` base con `frozen=False` | error (congelación) |
| T3 | `replica` base, `frozen=True`, `confirm` | pasa; el log tiene 1 fila con `tranche=replica, costs=base, entry_delay=0, kind=candidata` |
| T4 | T3 dos veces | la segunda → error («ya ejecutado») |
| T5 | `holdout_old` sin haber hecho `replica` | error (orden) |
| T6 | `replica` → `holdout_new` (saltando `holdout_old`) | error |
| T7 | `replica` → `holdout_old` → `holdout_new` → `full` | pasa; 4 filas |
| T8 | `replica` base; luego `replica` con otro hash (cambiar un parámetro o `f`) | error («gastado con otros parámetros») |
| T9 | `holdout_old` con `stress` antes que su base | error; después de la base → pasa; repetido → error |
| T10 | `(stress, 1)` | error (combinación no anunciada) |
| T11 | `monos_rank` en `replica` antes de la base | error; después → pasa una vez |
| T12 | `combo` en `replica` o en `is` | error; cadena `holdout_old` → `holdout_new` → `full` → pasa |
| T13 | `tranche_hash` | cambia al cambiar `risk_per_trade`; no cambia al reordenar las claves |
| T14 | `migrate_oos_log` sobre una copia del log actual (4 columnas, 4 filas) | 9 columnas, 4 filas, celdas nuevas vacías; segunda llamada no cambia nada |
| T15 | `assert_is_allowed` con `frozen=True` | error; con `b` = 2021-01-04 → error; con `[2007-07-01, 2020-12-31]` → pasa |
| T16 | `load_tranche` | errores de la lista de su docstring (uno por caso) |
| T17 | `run_backtest(..., "is")` con datos sintéticos que llegan a 2022 | la última fecha de `equity.csv` ≤ `is_end` |
| T18 | `run_backtest(..., "replica", confirm_tranche=True)` | devuelve `…/criterio15.md`; existe `detalle/`; la línea nueva del registro no contiene «CAGR» ni «DD» |
| T19 | `run_backtest(..., "oos")` con un `sc` de la ronda 2 | `ValueError` |
| T20 | `require_full_universe=True` y un símbolo con 300 velas al inicio | `ValueError` que lo nombra |
| T21 | los tests de la ronda 1 (`test_oos_guard`, `test_runner_candidate_oos_and_full_are_locked`) | siguen en verde |

**Aceptación:** T1–T21, G1–G6, CF1–CF4; `git diff` de `portfolio_sim.py` limitado a `cm_at` y
(en R2-12) los grupos.

---

## R2-6. Señales de panel

### R2-6.1 `strategies/base.py`

```python
class PanelSignalFn(Protocol):
    def __call__(self, bars: dict[str, pd.DataFrame], params: dict) -> dict[str, pd.DataFrame]:
        """bars: OHLCV por símbolo. Devuelve, por símbolo, un DataFrame con el MISMO índice
        que sus velas y columnas entry, exit (bool), stop_price, rank (float)."""


def as_panel(fn: SignalFn) -> PanelSignalFn:
    """Envuelve una estrategia por activo: {s: fn(df, params) for s, df in bars.items()}."""
```

Contrato de toda función de panel (lo comprueban los tests):
1. **Pura:** sin E/S, red ni azar; no modifica `bars` ni `params`.
2. **Causal:** la fila `t` de cualquier símbolo solo depende de velas con fecha ≤ `t` de
   **cualquier** símbolo.
3. Salida con las mismas claves que `bars`; índice de cada salida idéntico al de sus velas.
4. Ningún símbolo tiene `entry` y `exit` verdaderos el mismo día.
5. Sin estado: `exit = True` significa «si lo tienes, véndelo».

### R2-6.2 `strategies/__init__.py`

```python
PANEL_STRATEGIES: dict[str, PanelSignalFn] = {
    "sector_mom": sector_rank.generate_signals_panel,
    "sector_lowvol": sector_rank.generate_signals_panel,
}
SIGNAL_STRATEGIES["tom_etf"] = tom_etf.generate_signals
CANDIDATES_R2 = ("sector_mom", "tom_etf", "sector_lowvol")
NEEDS_SESSIONS = ("tom_etf",)


def resolve_signal_fn(strategy: str, sessions: pd.DatetimeIndex | None = None) -> PanelSignalFn:
    """Función de panel para cualquier estrategia por señales. Las de PANEL_STRATEGIES se
    devuelven tal cual; las de SIGNAL_STRATEGIES, envueltas con as_panel. Si la estrategia
    está en NEEDS_SESSIONS, exige `sessions` (ValueError si falta) y lo añade a una COPIA de
    `params` en cada llamada: el `params` del llamador (hash, registro) nunca lo contiene."""
```

`CANDIDATES` (ronda 1) no cambia.

### R2-6.3 Integración
- `runner.run_signals(bars, params, fn, cfg, a, b, entry_from=None)`: `fn` pasa a ser
  `PanelSignalFn` y la primera línea queda `sigs = fn(bars, params)`. En `run_backtest`,
  `fn = resolve_signal_fn(strategy, sessions)`. `walk_forward_fixed` y `robust_section` no
  cambian (reciben el mismo `fn`).
- `sessions` en backtest: `calendar.sessions_from_bars(data[sc["benchmark"]])` **después** de
  recortar en `end` (D2). Para la réplica de H6, `SPY` está en `data` porque es el benchmark.
- `targets.Target.signals`: `resolve_signal_fn(self.strategy, self.meta.get("sessions"))(self.bars, params)`.
  `build_target` acepta las estrategias de `PANEL_STRATEGIES` como `kind = "signals"`, gana
  `tranche: str = "is"` (universo, fechas y costes del tramo, igual que el runner) y guarda
  el calendario en `meta["sessions"]` cuando la estrategia lo necesita.
- Las señales se calculan con **toda** la historia del universo del tramo y luego se recortan
  (como hoy).

### R2-6.4 Tests (`tests/test_lookahead.py` y `tests/test_r2_panel.py`)
- `test_no_lookahead_truncation` / `_poison` existentes: añadir `tom_etf` a `SIG_PARAMS` con
  `sessions` = el índice completo de `make_bars` alargado con 30 días laborables (el
  calendario **no** se trunca ni se envenena).
- Nuevos, parametrizados sobre `PANEL_STRATEGIES` con 5 símbolos sintéticos
  (`make_bars(600, seed=i)`) y `lookback=126`:
  - **truncar todos** en `t` ∈ {150, 300, 451, 599} → filas `< t` idénticas;
  - **truncar uno** (los demás completos) → las filas ≤ fecha de corte de **todos** idénticas;
  - **envenenar uno** (× 10 y `NaN` desde `t`) → las filas `< t` de **todos** idénticas;
  - contrato 3 y 4 de §R2-6.1 sobre la salida completa;
  - `as_panel(tsmom_etf.generate_signals)` da lo mismo que llamar símbolo a símbolo.
- **Salidas antes que entradas** en la misma apertura: caso S11 (R2-14).

**Aceptación:** los tests anteriores de la ronda 1 no cambian de resultado; `run_backtest` de
`donchian_etf` con el `sc` sintético de `test_candidates.py` produce exactamente las mismas
operaciones antes y después del cambio (comparar `trades.csv` en un test).

---

## R2-7. `sector_mom` (H5) y `sector_lowvol` (H7)

**Fichero nuevo:** `src/tlab/strategies/sector_rank.py`. Tres funciones públicas; las dos
primeras existen para que los monos (R2-9) reutilicen **el mismo código** y solo cambien el
orden.

```python
@dataclass(frozen=True)
class PanelFeatures:
    review: pd.DatetimeIndex  # días de revisión (unión de índices, E7)
    eligible: pd.DataFrame  # bool, filas = review, columnas = símbolos ordenados
    key: pd.DataFrame  # float: clave verdadera (mom o −vol); NaN si no hay fila
    stop: dict[str, pd.Series]  # close − atr_mult·ATR, por símbolo, índice propio


def review_days_union(bars: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Primera fecha de cada mes en la UNIÓN de índices; la primera fecha de la unión no cuenta."""


def panel_features(bars: dict[str, pd.DataFrame], params: dict) -> PanelFeatures: ...


def signals_from_order(
    bars: dict[str, pd.DataFrame], feats: PanelFeatures, order_key: pd.DataFrame, params: dict
) -> dict[str, pd.DataFrame]:
    """Señales a partir de una clave de orden (mismas filas y columnas que feats.key)."""


def generate_signals_panel(bars: dict[str, pd.DataFrame], params: dict) -> dict[str, pd.DataFrame]:
    """= signals_from_order(bars, f, f.key, params) con f = panel_features(bars, params)."""
```

**Fórmulas (por símbolo `s`, sobre su propio índice):**
- `mom = close / close.shift(lookback) − 1`.
- `vol = ln(close / close.shift(1)).rolling(lookback, min_periods=lookback).std(ddof=1)`.
- `atr = indicators.atr(bars, atr_n)`.
- `key = mom` si `rank_by == "mom"`; `−vol` si `"lowvol"`; otro valor → `ValueError`.
- `apto = (mom > 0) & atr.notna() & key.notna()`.
- En cada día de revisión `t`, entre los símbolos **con vela en `t`**:
  - orden de los aptos por `(order_key es NaN, −order_key, símbolo)` → `puesto` 1, 2, 3…
    (los NaN van al final; solo ocurre con los monos);
  - `entry = apto & (puesto ≤ top_n)`; `exit = ~apto | (puesto > keep_n)`.
- Símbolo **sin** vela en `t`: no tiene fila ese día, no ocupa puesto.
- Todos los días: `stop_price = close − atr_mult·atr`. `rank` = `order_key` en los días de
  revisión (NaN el resto).
- Validación: `top_n ≥ 1`, `keep_n ≥ top_n`, `lookback ≥ 1`; si no, `ValueError`.

**Casos a mano** (`tests/test_r2_panel.py`). Tabla base (fechas 2024-01-30, 01-31, **02-01**
revisión, 02-02; `open` = cierre anterior, `high` = máximo y `low` = mínimo de los dos, salvo
la vela de A del 02-01 = `(101, 111, 101, 110)`); parámetros
`lookback=2, top_n=2, keep_n=3, atr_mult=3, atr_n=1`:

| | 01-30 | 01-31 | 02-01 | 02-02 |
|---|---|---|---|---|
| A | 100 | 101 | 110 | 111 |
| B | 100 | 100 | 105 | 106 |
| C | 100 | 100 | 102 | 103 |
| D | 100 | 99 | 97 | 96 |

Resultados del **02-01** **[script]** (`entry`, `exit`, `stop_price`, `rank`); el resto de
días todo `False`:

| Caso | A | B | C | D |
|---|---|---|---|---|
| **S1** (H5) | sí, no, 80, 0,10 | sí, no, 90, 0,05 | no, no, 96, 0,02 | no, **sí**, 91, −0,03 |
| **S2** (C cierra a 99) | sí, no, 80 | sí, no, 90 | no, **sí**, 96, −0,01 | no, sí, 91 |
| **S3** (H7) | no, no, 80, −0,05332 | sí, no, 90, −0,03450 | sí, no, 96, −0,01400 | no, sí, 91, −0,00732 |
| S3 con `keep_n=2` | no, **sí** | sí, no | sí, no | no, sí |
| **S5** (B cierra a 110), `top_n=1` | sí, no, 80, 0,10 | no, no, **80**, 0,10 | no, no | no, sí |
| S5 con `top_n=2` | sí | sí | no, no | no, sí |
| **S6** (B 99, C 98) | sí, no | no, sí | no, sí | no, sí |
| S6 con A a 99 | no, sí, **93** | no, sí | no, sí | no, sí |

- En S3, D tiene la menor volatilidad (0,733 %) pero **no es apto** y no ocupa puesto: por eso
  A queda 3.º y no 4.º.
- En S5, el stop de B es 80 porque su vela pasa a `(100, 110, 100, 110)` → TR = 10.
- En «S6 con A a 99» la vela de A es `(101, 101, 99, 99)` → TR = 2 → stop 93.
- **S4:** con las velas hasta el 02-01, las filas del 02-01 son las de S1.
- **S7:** se añade E con dos velas (01-31 a 50, 02-01 a 100): filas de A–D = S1;
  `entry(E) = False`, `exit(E) = True` (no apto; inocuo), `rank(E)` = NaN **[script]**.
- **S8:** × 10 en los precios de B posteriores al 02-01 → ninguna fila ≤ 02-01 cambia en
  ningún símbolo; cortar solo A en el 02-01 → filas del 02-01 de B, C, D iguales.
- **S9:** C sin vela el 02-01 → la salida de C tiene 3 filas, todas `False`; `entry` = A y B;
  `exit` = D **[script]**.
- **S13 (de punta a punta, nuevo):** tabla base con una 5.ª fecha, 02-05 (cierres A 112,
  B 107, C 104, D 95), parámetros de S1, 10.000 $, riesgo 1 %, 5 pb, tope 0,3333, sin kill
  switch **[script]**:

  | | A | B |
  |---|---|---|
  | Compra en la apertura del 02-02 | 110 → 110,055 | 105 → 105,0525 |
  | Stop | 80 | 90 |
  | Riesgo por unidad | 30,095 | 15,0975 |
  | Cantidad | **3** | **6** |
  | `risk_usd` | 90,285 | 90,585 |
  | Cierre contable el 02-05 (`end_of_data`) | 111,944 | 106,9465 |
  | Resultado | **+5,667 $** (+0,063 R) | **+11,364 $** (+0,125 R) |

  Equity diaria: `[10000, 10000, 10000, 10008,52, 10017,031]`; posiciones abiertas
  `[0, 0, 0, 2, 2]`. C no entra (puesto 3 > `top_n`); D nunca se compra.

**TOML:** los dos de §R2-5.1 (cambia `id` y `rank_by`). Test nuevo
`test_r2_toml_matches_preregistro` (parametrizado sobre `CANDIDATES_R2`): universo, réplica,
benchmark, fechas de los 5 tramos, costes (5 / 15 / 10 / 5 / calendario 10→5), `params`,
`[robust_grid]`, `risk_levels`, `calibration_dd_limit = 0.12`, `subperiods` (los 4 del
criterio 11), `status = "preregistrada"`, `frozen is False`, `min_history_bars = 365`,
`kill_switch_in_backtest is False`, y nº de variantes ≤ 30.

**Casos límite a cubrir:** universo de un solo símbolo; todos los símbolos sin historia
(salida toda `False`, sin excepción); `bars` vacío → `ValueError`; índices sin tz →
`ValueError` (el repo exige UTC).

**Aceptación:** S1–S9 y S13 con los valores de las tablas (tolerancia 1e-9 en precios, 1e-5
en `rank` de H7); tests de look-ahead de R2-6.4; test del TOML.

---

## R2-8. `tom_etf` (H6) y calendario

### R2-8.1 `src/tlab/data/calendar.py`

```python
def sessions_from_bars(bars: pd.DataFrame) -> pd.DatetimeIndex:
    """Calendario de backtest: el índice (UTC, único, ordenado) de las velas de referencia."""


def sessions_from_alpaca(client, start: date, end: date) -> pd.DatetimeIndex:
    """Calendario en vivo con `client.get_calendar`. Fechas de sesión a las 00:00 UTC (misma
    convención que las velas diarias de acciones del repo)."""


def live_sessions(client, today: date, history: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """`history` (sesiones pasadas) + calendario de Alpaca desde `today` hasta el ÚLTIMO DÍA
    DEL MES SIGUIENTE (E6). Sin duplicados."""
```

`client` es el de `broker.alpaca_paper.make_trading_client()` (pasa por la guardia de paper).
Tests con un cliente falso que devuelve objetos con atributo `date`; un test `network`
opcional.

### R2-8.2 `src/tlab/strategies/tom_etf.py`

```python
def session_table(sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Por sesión: `ordinal` (posición en su mes, desde 1), `quedan` (sesiones posteriores en
    su mes) y `completo` (hay alguna sesión de un mes posterior en el calendario)."""


def generate_signals(bars: pd.DataFrame, params: dict) -> pd.DataFrame: ...
```

Fórmulas (E6; **mandan sobre §6.3**), con `x = session_table(sessions).reindex(bars.index)`:
- `entry = completo & (quedan == entry_before_end) & atr.notna()`
- `exit = (ordinal >= exit_day) & ~(completo & (quedan <= entry_before_end))`
- `stop_price = close − atr_mult × ATR(atr_n)`; `rank = 0.0`.
- `ValueError` si: falta `params["sessions"]`; `sessions` tiene duplicados, no está ordenado o
  no tiene tz; alguna fecha de `bars` no está en `sessions`.
- No deduce nunca el calendario de las propias velas.

**Casos a mano** (`tests/test_r2_tom.py`; `atr_mult=3, atr_n=1`; calendario C1 = 2024-01-29,
01-30, 01-31, 02-01, 02-02, 02-05, 02-06; velas de C9 salvo que se diga otra cosa)
**[script]**:

| Caso | Configuración | `entry` verdadero | `exit` verdadero |
|---|---|---|---|
| **C1** | por defecto | 01-30 (stop 92) | 02-05, 02-06 |
| **C2a** | `entry_before_end=2` | 01-29 | 02-05, 02-06 |
| **C2b** | `exit_day=2` | 01-30 | 02-02, 02-05, 02-06 |
| **C3** | sesiones 2024-12-27, 12-30, 12-31, 2025-01-02, 01-03, 01-06, 01-07 | 12-30 | 01-06, 01-07 |
| **C4** | `bars` cortado en 01-30, mismo calendario | filas iguales a las de C1 | — |
| **C5** | todas las sesiones 2024-01-02 → 02-06 (enero tiene 21; el 01-15 no es sesión) | solo 01-30 | del 01-04 al 01-29 (17 sesiones), 02-05 y 02-06: 19 en total. `False` el 01-02, 01-03, 01-30, 01-31, 02-01, 02-02 |
| **C6** | calendario y velas cortados en 01-31 | ninguno | 01-31 (3.ª sesión de un mes no completo; inocuo) |
| **C7** | C1 sin la vela del 02-05 | 01-30 | 02-06 (y no existe fila del 02-05) |
| **C8** | sin `sessions`, o con `sessions` sin el 02-01 | `ValueError` | |

- **C9 (de punta a punta):** velas `(open, high, low, close)`: 01-29 `(100,100,100,100)` ·
  01-30 `(100,102,99,101)` · 01-31 `(101,103,100,102)` · 02-01 `(102,104,101,103)` ·
  02-02 `(103,105,102,104)` · 02-05 `(104,106,103,105)` · 02-06 `(106,107,105,106)`;
  10.000 $, 1 %, 5 pb, tope 0,3333. **[script]**: compra el 01-31 a 101,0505; `risk_usd`
  90,965; **10 acciones**; venta el 02-06 a 105,947 (motivo `signal`); **+48,965 $ = +0,538 R**;
  una sola operación.
- **C9 con retraso de 1 vela** (`entry_delay=1`): compra el 02-01 a 102,051; **9 acciones**;
  misma venta; **+35,064 $ = +0,386 R** **[script]**.
- **C10 (nuevo, nunca `entry` y `exit` a la vez):** sobre un calendario de días laborables
  2023-01-02 → 2024-12-31 y la rejilla completa de `tom_etf` (18 combinaciones), ninguna fila
  tiene los dos a `True`, y en cada mes completo hay exactamente un `entry`.
- **C11 (nuevo, equivalencia con la regla original):** con velas completas en ese mismo
  calendario, simular con E6 y con una señal de venta de un solo día (`ordinal == exit_day`,
  construida en el test) da **las mismas operaciones**.

**Casos límite:** mes con menos sesiones que `exit_day` (no ocurre en la realidad; no debe
lanzar excepción); `bars` vacío → DataFrame vacío con las 4 columnas; símbolo cuya primera
vela es posterior al inicio del calendario (normal: `EFA`, `EEM`).

**TOML:** el de §R2-5.1. **Aceptación:** C1–C11, look-ahead de R2-6.4, test del TOML.

---

## R2-9. Monos a medida

**Fichero nuevo:** `src/tlab/backtest/custom_monkeys.py` (el `random_benchmark.py` actual no
se modifica: sus monos de «entrada al azar» siguen siendo el informativo de §3.4; de él se
reutilizan `DEFAULT_N` y `DEFAULT_SEED`. **No** se reutiliza `empirical_p`: descarta los monos
sin Sharpe y aquí deben seguir contando en N, D7). Script: `scripts/monkeys_r2.py`.

```python
MODES = ("rank", "persist", "window")


def derangement(symbols: list[str], rng: np.random.Generator) -> dict[str, str]:
    """Permutación sin puntos fijos: baraja y repite hasta que ningún símbolo quede en su
    sitio. Con un solo símbolo → ValueError."""


def rank_order_key(feats: PanelFeatures, rng: np.random.Generator) -> pd.DataFrame:
    """Mono de sorteo mensual: un uniforme [0, 1) por (revisión, símbolo)."""


def persist_order_key(feats: PanelFeatures, perm: dict[str, str]) -> pd.DataFrame:
    """Mono persistente (E4): la columna de `s` es feats.key[perm[s]]."""


def draw_purchase_sessions(
    sessions: pd.DatetimeIndex,
    start: pd.Timestamp,
    end: pd.Timestamp,
    hold: int,
    rng: np.random.Generator,
) -> list[pd.Timestamp]:
    """Una sesión de compra por mes de [start, end] (E5, D6)."""


def window_signals(
    bars: dict[str, pd.DataFrame],
    sessions: pd.DatetimeIndex,
    params: dict,
    purchases: list[pd.Timestamp],
) -> dict[str, pd.DataFrame]:
    """Señales del mono de H6 para unas sesiones de compra dadas."""


@dataclass
class MonkeyResult:
    strategy: str
    mode: str
    tranche: str
    n: int
    seed: int
    real: dict  # métricas de la candidata (extract_metrics)
    table: pd.DataFrame  # una fila por mono
    k_ge: int  # monos con Sharpe >= el real (NaN no cuenta)
    p_value: float  # (1 + k_ge) / (n + 1)
    percentile: float  # monos con Sharpe <= el real, sobre n (NaN cuenta como <=)


def run_custom_monkeys(
    target: Target, mode: str, n: int = 1000, seed: int = 42, tranche: str = "is", n_jobs: int = -1
) -> MonkeyResult: ...
```

**Reglas comunes:**
- El mono `i` usa `np.random.default_rng(np.random.SeedSequence([seed, i]))` (como el código
  actual): el resultado no depende del nº de procesos.
- El mono se ejecuta con `target.run_with_signals(...)`: mismo motor, costes, `f`, tope,
  huecos y fechas que la candidata. `target.cfg.entry_delay` debe ser 0.
- Para `rank` y `persist`: `feats = panel_features(target.bars, target.params)` una sola vez;
  señales = `signals_from_order(target.bars, feats, order_key, target.params)`. El filtro
  `apto` es el de `feats`: **no cambia**.
- `persist`: una sola `derangement` por mono, la misma en todas las revisiones.
- `window`: `hold = entry_before_end + exit_day` (4 con los parámetros por defecto).
  - **Sorteo** (mes a mes, en orden): candidatas del mes `m` = sus sesiones que cumplan
    (i) tienen sesión anterior en el calendario (para la señal), (ii) son ≥ la sesión de venta
    del mes anterior, (iii) su sesión de venta (`hold` sesiones después) existe en el
    calendario y es ≤ `end`. Se elige una uniformemente. Mes sin candidatas → sin ventana.
  - **Señales** por activo: `entry = True` en la sesión **anterior** a la de compra (si el
    activo tiene vela y ATR ese día); `exit = True` desde la sesión `compra + hold − 1` hasta
    la víspera de la siguiente señal de entrada (sostenida, D6); `stop_price` y `rank` como en
    `tom_etf`.
  - Las tres series usan las **mismas** sesiones de compra.
- En la réplica (criterio 15) se ejecutan los mismos modos sobre el universo de réplica;
  la guarda lo anota (`monos_*`).
- Salidas: `reports/robustez/<estrategia>/monos_<modo>_<tramo>_<sello>/` con `monos.csv`
  (una fila por mono) y `resumen.md` (Sharpe real, `k_ge`, p, percentil, y la comparación de
  nº de operaciones y exposición media candidata/monos). En la réplica solo se añade el
  percentil a `criterio15.md`.
- Registro: una línea «[monos, no es variante]» por ejecución.

**Casos de prueba** (`tests/test_r2_monkeys.py`):

| Caso | Qué | Esperado |
|---|---|---|
| M1 (identidad `rank`) | `signals_from_order(bars, feats, feats.key, params)` | iguales a `generate_signals_panel(bars, params)`; mismas operaciones en el simulador |
| M2 (identidad `window`) | `window_signals` con `purchases` = última sesión de cada mes completo | mismas **operaciones** que `tom_etf` en el simulador (3 activos sintéticos, 2 años de días laborables) |
| M3 (orden inyectado, tabla S1) | `order_key` del 02-01 = A 0,1 · B 0,9 · C 0,5 · D 0,99 | `entry` = B y C; A nada (puesto 3 ≤ `keep_n`); D `exit` (no apto aunque su clave sea la mayor) **[aritmética]** |
| M4 (persistente, tabla S1) | `perm = {A→D, B→A, C→B, D→C}` | claves: A −0,03 · B 0,10 · C 0,05 → `entry` = B y C; A nada; D `exit` **[aritmética]** |
| M5 (`derangement`) | 9 símbolos, 200 semillas | nunca un punto fijo; es biyección; con 3 símbolos solo salen `B,C,A` y `C,A,B` **[script]**; con 1 → `ValueError` |
| M6 (persistente estable) | un mono `persist` | la permutación es la misma en la primera y en la última revisión; `eligible` idéntico al de la candidata |
| M7 (≤ 3 aptos) | datos sintéticos con, como mucho, 3 aptos en cada revisión y ATR grande (posiciones pequeñas: la caja no limita, D8) | 20 monos `rank` y 20 `persist` dan las mismas operaciones que la candidata |
| M8 (`window`, una por mes) | calendario 2024-01-02 → 2024-03-08 sin el 01-15 ni el 02-19 (47 sesiones: enero 21, febrero 20), `hold=4`, 200 semillas | una compra por mes como máximo; misma compra para los 3 activos; venta = 4.ª sesión posterior; compra de cada mes ≥ venta del mes anterior |
| M9 (`window`, números) | mismo calendario | compra 01-30 → señal 01-29, venta 02-05 (señal de venta 02-02); entonces febrero tiene **18** sesiones válidas de 20 (desde el 02-05). Compra 01-31 (la real) → señal 01-30, venta 02-06 **[script]** |
| M10 (`window`, fin de tramo) | mismo calendario con `end` = 2024-02-29 | en febrero solo son sorteables **16** sesiones (hasta el 02-23) **[script]**; el 01-02 (primera del calendario) nunca sale |
| M11 (reproducible) | `run_custom_monkeys` con `n=30`, dos veces, y con `n_jobs` 1 y 2 | tablas idénticas |
| M12 (p y percentil) | Sharpe de monos `[0.1, 0.5, NaN, 0.9]`, real 0,5 | `k_ge = 2`, `p = 3/5 = 0,6`, `percentile = 3/4 = 0,75` **[aritmética]** |
| M13 (umbral) | `n = 1000` | `k_ge = 19` → p = 0,01998 (< 0,02); `k_ge = 20` → 0,02098 (no) **[aritmética]** |
| M14 (ventaja conocida) | datos sintéticos donde el símbolo con más `mom` sube después por construcción | la candidata queda por encima del percentil 90 de los monos `rank`; con datos sin ventaja (ruido), no se exige nada: solo que termine |

**Aceptación:** M1–M14. `scripts/monkeys_r2.py --strategy X --mode M --tranche T` se niega a
ejecutarse sobre `replica` sin `--confirm-tranche` y nunca acepta `holdout_*` ni `full` (los
monos solo se usan en IS y réplica).

---

## R2-10. Informe: métricas nuevas y criterios

### R2-10.1 `src/tlab/metrics.py` (funciones puras nuevas)

```python
def return_dd_ratio(cagr: float, max_dd: float, n_trades: int | None = None) -> float:
    """CAGR / |caída máxima|. Caída 0: +inf si n_trades es None o > 0 y cagr > 0; si no, NaN."""


def joint_cagr(g_old: float, years_old: float, g_new: float, years_new: float) -> float:
    """(g_old · g_new) ** (1 / (years_old + years_new)) − 1. Criterio 16a."""


def worst_calendar_year(eq: pd.Series) -> tuple[int, float]:
    """(año, rentabilidad) del peor año natural. Rentabilidad de un año = último valor del
    año / último valor del año anterior − 1 (el primer año, contra el primer valor)."""


def losing_streaks(trades: pd.DataFrame) -> dict:
    """Operaciones ordenadas por (exit_date, entry_date, symbol). Devuelve `longest_n` (más
    pérdidas seguidas), `longest_usd` (su suma; a igual longitud, la peor) y `deepest_usd`
    (la racha de pérdidas seguidas con peor suma). pnl == 0 corta la racha."""


def cash_adjusted_equity(eq: pd.Series, exposure: pd.Series, cash_eq: pd.Series) -> pd.Series:
    """Informativo (D13): adj[0] = eq[0];
    adj[t] = adj[t−1] · (eq[t]/eq[t−1] + (1 − exposure[t−1]) · (cash[t]/cash[t−1] − 1))."""
```

### R2-10.2 `src/tlab/backtest/criteria.py` (nuevo)

```python
def criterion_16(strat_cagr: float, cash_cagr: float, margin: float) -> bool:
    """margin > 0: strat >= cash + margin (16-IS, 16a, 16d). margin == 0: strat > cash (16b)."""


def criterion_17(
    strat_cagr: float, strat_dd: float, n_trades: int, bench_cagr: float, bench_dd: float
) -> bool:
    """E9: False si n_trades == 0 o strat_cagr <= 0; True si la relación del benchmark es
    <= 0; si no, relación de la estrategia > relación del benchmark (estricto)."""


def monte_carlo_dd_grouped(
    trades: pd.DataFrame, initial_equity: float, n: int = 1000, seed: int = 42
) -> np.ndarray:
    """Como robustness.monte_carlo_dd, pero barajando la SUMA de las operaciones abiertas el
    mismo día (hallazgo B4). Informativo."""


def checklist(tranche: str, **medidas) -> list[tuple[str, str, bool | None]]:
    """Filas (criterio, texto con las cifras, sí/no) que tocan en ese tramo. None = «no
    aplica aquí». Solo ordena y formatea: no decide nada que no esté en hipotesis_ronda2 §4."""
```

### R2-10.3 Secciones del informe (en `runner`, solo para `is_round2`)

| Tramo | Secciones nuevas |
|---|---|
| todos | Benchmarks: `SPY`, 60/40, **caja** (CAGR de `cash_equity` sobre el índice de la curva), y sus relaciones. Peor año y peor racha. Exposición media. «Efectivo rindiendo como la caja» (informativo). Episodios de kill switch al 15 %. |
| `is` | Calibración con el límite 0,12. Casillas 0, 3-IS, 16-IS, 17-IS (5, 6, 7-IS, 8-IS, 10-IS salen de `wf` y `robust`, como en la ronda 1; 14 sale de los monos). |
| `replica` | Solo `criterio15.md` (E3). |
| `holdout_old`, `holdout_new` | Casillas 2, 3, 12 (kill switch literal: `kill_switch_episodes(eq, 0.15)` vacío), 16b, 17. En `holdout_new`, además **16a**: lee `equity.csv` del informe base de `holdout_old` (ruta en la columna `report` del log) y calcula `joint_cagr` de la estrategia y de la caja. |
| `full` | Casillas 1, 4, 9, 10 (Monte Carlo; y, para `tom_etf`, el agrupado por meses como informativo), 11 (4 subperiodos y por activo), 13, **16d** (trozo desde `fixed_income_from`: CAGR de la estrategia, de `IEF` comprar y mantener y de la caja en ese trozo), 17d. |

El informe **muestra** las casillas; el veredicto lo escribe Fable. Ningún texto del informe
dice «apta» o «aprobada».

**Casos a mano** (`tests/test_r2_metrics.py`):

| Caso | Entrada | Esperado |
|---|---|---|
| ME1 | `return_dd_ratio(0.06, -0.12)` | `0,5` |
| ME2 | `criterion_17(0.06, -0.12, 50, 0.09, -0.55)` | `True` (0,5 > 0,1636) |
| ME3 | `criterion_17(-0.01, -0.02, 50, …)` con cualquier benchmark | `False` (E9 a) |
| ME4 | `return_dd_ratio(0.03, 0.0, 5)` → `inf`; `criterion_17(0.03, 0.0, 5, 0.10, -0.20)` | `True` (E9 c) |
| ME5 | `criterion_17(0.01, -0.05, 10, -0.02, -0.40)` | `True` (E9 b) |
| ME6 | `criterion_17(0.05, -0.05, 0, 0.10, -0.50)` | `False` (E9 d: sin operaciones) |
| ME7 | `criterion_17(0.06, -0.12, 50, 0.10, -0.20)` | `False` (0,5 no es **mayor** que 0,5) |
| ME8 | `joint_cagr(1.5, 7, 1.2, 5)` | `0,0502017` (5,02 %) **[script]** |
| ME9 | `criterion_16(0.0501, 0.03, 0.02)` → `True`; `(0.0499, 0.03, 0.02)` → `False`; `(0.0300, 0.03, 0.0)` → `False`; `(0.0301, 0.03, 0.0)` → `True` | |
| ME10 | equity `[100, 120, 110, 99, 108.9]` en 2020-12-31, 2021-06-30, 2021-12-31, 2022-12-30, 2023-12-29 | años: 2020 0 %, 2021 +10 %, 2022 −10 %, 2023 +10 % → `(2022, -0.10)` **[script]** |
| ME11 | `pnl_usd` (por orden de salida) `[10, -20, -30, 5, -5, -5, -5]` | `longest_n = 3`, `longest_usd = -15`, `deepest_usd = -50` **[script]** |
| ME12 | `eq = [10000, 10100, 9898]`, `exposure = [0.5, 0.0, 1.0]`, `cash = [10000, 10002, 10004.0004]` | `[10000, 10101.0, 9901.0002]` **[script]**: el primer día suma medio 0,02 % y el segundo el 0,02 % entero |
| ME13 | ME12 con `exposure` todo 1 → igual a `eq`; con `eq` plano y `exposure` todo 0 → igual a `cash` | |
| ME14 | 6 operaciones: tres de −100 $ con `entry_date` 2024-01-31 y tres de +50 $ con 2024-02-29; 10.000 $ | `monte_carlo_dd_grouped`: todos los valores ∈ {0,030000, 0,029557} **[script]** (frente a los varios valores posibles barajando las 6 sueltas) |
| ME15 | 16d con curvas sintéticas: estrategia 6 %, `IEF` 5 %, caja 3 % | sí; con estrategia 4,9 % e `IEF` 4 % → no (falla caja + 2); con estrategia 6 % e `IEF` 7 % → no |
| ME16 | informe sintético de `holdout_new` sin fila base de `holdout_old` en el log | 16a = «no calculable» (y la guarda ya habría impedido llegar aquí) |

**Aceptación:** ME1–ME16; `test_r2_report_sections` (datos sintéticos, `tmp_path`) comprueba
que cada tramo contiene las secciones de la tabla y que `replica` no contiene «CAGR».

---

## R2-11. Banda de resultados para el paper

**Fichero nuevo:** `src/tlab/backtest/paper_band.py`. No reutiliza
`montecarlo.block_bootstrap_returns` (genera trayectorias tan largas como toda la historia:
con 10.000 trayectorias no cabe en memoria).

```python
HORIZONS = {"6m": 126, "12m": 252}  # sesiones


def paper_band(
    daily_returns: np.ndarray,
    horizons: dict[str, int] = HORIZONS,
    block: int = 21,
    n: int = 10_000,
    seed: int = 42,
    percentiles: tuple[int, ...] = (5, 50, 95),
) -> pd.DataFrame:
    """Remuestreo por bloques contiguos (sin envolver) de las rentabilidades diarias. Cada
    trayectoria tiene max(horizons) sesiones: ceil(max/block) bloques con inicio uniforme en
    [0, T − block]. La rentabilidad a `h` sesiones es el producto de las `h` primeras.
    Devuelve filas = horizontes, columnas = p5, p50, p95 (rentabilidad acumulada).
    ValueError si T < block o si hay NaN."""


def band_markdown(band: pd.DataFrame, source: str) -> str:
    """Tabla para STRATEGY.md, con la procedencia (informe de la ejecución completa)."""
```

Entrada prevista (paso 3, no ahora): `metrics.daily_returns` de la curva de `full`.

| Caso | Entrada | Esperado |
|---|---|---|
| B1 | rentabilidad constante 0,001 (500 valores) | 6 m: 0,134211 en los tres percentiles; 12 m: 0,286434 **[script]** |
| B2 | dos llamadas con la misma semilla | DataFrames idénticos; con otra semilla, distintos (datos con ruido) |
| B3 (bloques enteros) | exponer una función interna que devuelva los índices; `returns = arange(T)` | dentro de cada bloque de 21 los índices son consecutivos; ningún índice ≥ T |
| B4 | `T = 20`, `block = 21` | `ValueError` |
| B5 | ruido normal (media 0) | p5 < p50 < p95 en los dos horizontes y el ancho a 12 m > a 6 m |
| B6 | las 126 primeras sesiones de cada trayectoria son las del horizonte de 6 m | la banda de 6 m calculada sola (`horizons={"6m": 126}`) coincide con la fila 6 m de la conjunta |

**Aceptación:** B1–B6. No se genera ninguna banda real (no hay ejecución completa todavía).

---

## R2-12. Cartera combinada (solo preparar)

**Ficheros:** `portfolio_sim.py` (grupos de huecos), `src/tlab/backtest/combined.py` (nuevo).

`SimConfig` gana dos campos opcionales:

```python
group_of: dict[str, str] | None = None  # símbolo → grupo
group_max_positions: dict[str, int] | None = None
```

En el bucle de entradas de `simulate`, antes de dimensionar: si el grupo del símbolo ya tiene
`group_max_positions[grupo]` posiciones abiertas → se salta (como cuando no hay hueco). El
límite global `max_positions` sigue aplicando. Con los dos campos a `None`, nada cambia.

```python
def combined_signals(
    sector_signals: dict[str, pd.DataFrame],
    tom_signals: dict[str, pd.DataFrame],
    tom_symbol: str = "SPY",
) -> dict[str, pd.DataFrame]:
    """Une las señales de sectores con las de `tom_symbol`. El `rank` de `tom_symbol` se pone
    a −inf (D9). ValueError si `tom_symbol` está también entre los sectores."""


def combined_config(
    cfg_sector: SimConfig, cfg_tom: SimConfig, sector_symbols: list[str], tom_symbol: str = "SPY"
) -> SimConfig:
    """Copia de cfg_sector con risk_per_trade = min de las dos f (§5.4), group_of
    ({sector: "sectores", tom_symbol: "tom"}) y group_max_positions
    ({"sectores": 2, "tom": 1})."""


def run_combined(sector_id: str, tranche: str, *, confirm_tranche: bool = False, **kw) -> Path:
    """Solo tramos holdout_old, holdout_new y full (E12); guarda con kind="combo"."""
```

`top_n` y `keep_n` **no cambian** (E12): las señales de sectores son las de siempre; el límite
de 2 lo impone el simulador.

**Caso a mano CB1** (sintético; 4 «sectores» X, Y, Z, W y `SPY`; velas planas a 100; stop 90
con `manual_signals`; 10.000 $, 1 %, 5 pb, tope 0,3333) **[aritmética]**: riesgo por unidad
100,05 − 89,955 = 10,095 → `floor(100 / 10,095)` = 9 acciones por posición.
- Día 0: `entry` en X, Y, Z (ranks 3, 2, 1) y en `SPY`. Día 1: se compran **X e Y** (los dos
  primeros por `rank`), **Z no** (grupo lleno), y `SPY` sí. 3 posiciones.
- Día 5: `entry` en W → no entra (grupo `sectores` lleno) aunque el límite global lo impidiera
  igualmente.
- Día 8: `exit` en `SPY`; día 9: `SPY` se vende. Día 10: `entry` en W → sigue sin entrar
  (hay 2 sectores y un hueco global libre: **el hueco de `tom` no lo puede usar un sector**).
- Comprobaciones: nº de posiciones de sectores ≤ 2 y de `tom` ≤ 1 en todas las velas;
  exposición ≤ 100 %; en la salida de `combined_signals` el `rank` de `SPY` es −inf en todas
  las filas.

| Caso | Esperado |
|---|---|
| CB1 | lo de arriba |
| CB2 | `combined_signals` con `SPY` en los sectores → `ValueError` |
| CB3 | `combined_config` con `f` 0,01 y 0,0075 → 0,0075 |
| CB4 | `run_combined(..., "is")` y `"replica"` → `TrancheGuardError` |
| CB5 | `simulate` sin grupos: todos los tests existentes iguales |

**Aceptación:** CB1–CB5. **No se ejecuta** sobre datos reales en ningún caso.

---

## R2-13. Verde e informe para Fable

1. `uv run ruff check . && uv run ruff format --check .` y `uv run pytest -q` en verde; pegar
   el resumen real de la salida.
2. `docs/INFORME_RONDA2_IMPL.md` (formato de `docs/INFORME_PASO2.md`), con:
   - tabla tarea → commit → tests;
   - **dudas de interpretación** (una por línea, con la opción tomada);
   - desviaciones respecto a este documento, si las hay, con su motivo;
   - resultados de la verificación de datos: solo rutas a `reports/datos/…` (ninguna cifra
     copiada a mano);
   - base de la serie de caja y fuente;
   - lo que **no** se ha hecho.
3. Marcar las casillas R2-1 … R2-18 en `docs/tareas_sonnet.md`.
4. Comprobación final de prohibiciones: `git status` sin ningún directorio
   `reports/sector_mom`, `reports/sector_lowvol` ni `reports/tom_etf`; `reports/oos_log.csv`
   sin filas nuevas (solo la migración de cabecera).

---

## R2-14 a R2-17. Dónde está cada caso añadido por la auditoría

| Añadido | Caso | Especificado en |
|---|---|---|
| R2-14 | S5–S9 | §R2-7 |
| R2-14 | S10–S12 (simulador) | abajo |
| R2-15 | C5–C8, C9 y retraso | §R2-8 |
| R2-16 | identidad, ≤ 3 aptos, persistente, `window` | §R2-9 (M1–M10) |
| R2-17 | relación, 16a, caja, kill switch, guarda, coste por fecha, Monte Carlo por meses | §R2-10 (ME1–ME8, ME14), §R2-4 (CA1–CA3), §R2-1 (K1–K7), §R2-5 (T1–T15, CF1–CF2) |

**S10–S12** (`tests/test_r2_sim.py`; velas planas `(100, 101, 99, 100)` salvo indicación; stop
90; 10.000 $, 1 %, 5 pb, tope 0,3333, sin kill switch). Con esos números cada compra es de
**9 acciones** a 100,05 (900,45 $) **[aritmética]**:

- **S10 (el puesto 4–5 conserva el hueco; no hay cola):** día 0 `entry` en X, Y, Z → día 1
  compradas (caja 7.298,65 $). Día 5: X con `entry = exit = False`; W con `entry = True`.
  Esperado: W no se compra el día 6 **ni ningún día posterior**; X sigue abierta hasta el
  final; solo 3 operaciones (todas `end_of_data`). Variante del límite H-11: si W **no tiene
  vela** el día 6, la entrada sigue pendiente y tampoco se ejecuta el día 7 porque no hay
  hueco (comprobarlo).
- **S11 (rotación en la misma apertura):** como S10, pero el día 5 Z tiene `exit = True` y W
  `entry = True`. Día 6: se vende Z a 99,95 (899,55 $) y se compra W (900,45 $); caja tras la
  apertura 7.297,75 $ **[aritmética]**. Comprobaciones: la operación de Z tiene
  `exit_date` = día 6 y la de W `entry_date` = día 6; `n_open` es 3 el día 5 y el día 6;
  exposición ≤ 1 todas las velas; la caja reconstruida (`equity × (1 − exposure)`) nunca es
  negativa.
- **S12 (señal repetida):** X en cartera desde el día 1 (stop 90, 9 acciones). Día 5: X vuelve
  a tener `entry = True` con `stop_price = 95`. Día 7: vela `(100, 101, 94, 100)`. Esperado:
  X **no** sale el día 7 (su stop sigue en 90; si se hubiera movido a 95 saltaría);
  `qty = 9` y `stop_initial = 90` en su operación final.

---

## R2-18. Verificación de datos (amplía R2-3, enmienda E13)

**Ficheros nuevos:** `src/tlab/data/audit.py` (funciones puras, con tests sintéticos) y
`scripts/check_data_r2.py`, `scripts/check_tradable.py` (tocan red; se ejecutan en el PC de
Jorge con el `.env`; nunca imprimen claves).

```python
def bar_inventory(bars: dict[str, pd.DataFrame], min_bars: int = 365) -> pd.DataFrame:
    """Por símbolo: first, last, n_bars, n_gaps (huecos > 4 días naturales, como
    validate_bars), date_min_bars (fecha de la vela nº `min_bars`; NaT si no llega)."""


def big_jumps(
    bars: dict[str, pd.DataFrame],
    threshold: float = 0.20,
    known: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Filas (symbol, date, known_split) con |cierre_t / cierre_{t−1} − 1| > threshold.
    NO devuelve la magnitud (E13: solo fecha y símbolo)."""


def missing_on_review_days(bars: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Filas (date, missing) por cada día de revisión (review_days_union) en el que falta la
    vela de algún símbolo que ya había empezado a cotizar y no ha terminado."""


def missing_on_tom_days(
    bars: dict[str, pd.DataFrame],
    sessions: pd.DatetimeIndex,
    entry_before_end: int = 1,
    exit_day: int = 3,
) -> pd.DataFrame:
    """Filas (symbol, date, kind) con kind ∈ {"entry_signal", "exit_signal", "buy", "sell"}:
    sesiones de señal o de ejecución de tom_etf en las que el símbolo (ya cotizando) no tiene
    vela."""


def dates_outside_calendar(
    bars: dict[str, pd.DataFrame], sessions: pd.DatetimeIndex
) -> pd.DataFrame:
    """Filas (symbol, date): velas en fechas que no están en el calendario (harían saltar el
    ValueError de tom_etf)."""


def seam_check(merged: pd.DataFrame, fresh: pd.DataFrame, rel_tol: float = 1e-6) -> pd.DataFrame:
    """Fechas en las que el cierre de la caché alargada y el de una descarga nueva completa
    difieren más de rel_tol (H-9). Solo fechas y símbolo."""
```

`known` para `big_jumps` (de `docs/auditoria_ronda2.md` §6):
`XLK XLY XLE XLU XLB` → 2025-12-05; `EWJ EWU EWI` → 2016-11-07.

**Contenido de `reports/datos/r2_datos_<sello>.md`** (lo escribe `check_data_r2.py`):
1. Inventario (`bar_inventory`) de los 24 símbolos + `IEF` + la serie de caja, con una columna
   «fecha esperada» (auditoría §6) y «¿coincide (± 5 sesiones)?».
2. Saltos > ±20 %: lista (símbolo, fecha, ¿split conocido?). Y, expresamente, una línea por
   cada split conocido: «sin salto en esa fecha: sí/no».
3. Días de revisión con velas ausentes: recuento y fechas, por universo (sectores / países).
4. Días de señal o ejecución de `tom_etf` sin vela: recuento y fechas por símbolo (`SPY`,
   `IWM`, `EFA`, `MDY`, `EEM`, `EWJ`); y velas fuera del calendario de `SPY`.
5. Costura (H-9) de `SPY`, `IWM`, `EFA`, `EEM`, `IEF`: descarga nueva completa en un
   directorio temporal (`load_bars(..., cache_dir=tmp)`), comparación con la caché; nº de
   fechas discrepantes.
6. Caja: fuente, base (descuento o rentabilidad) con su cita, primera/última fecha, mayor hueco.
7. «Para Fable» (R2-3.3) y **«PARAR»** si se da alguno de estos: un salto no explicado en un
   símbolo principal; velas ausentes en días de revisión del universo **principal** de H5/H7
   (E7); discrepancias de costura; un símbolo principal no operable.

**Contraste yfinance ↔ Alpaca:** `scripts/check_alpaca_vs_yf.py --symbols <los 24 + IEF>` (el
script ya admite `--symbols`), tramo común desde 2016, **tolerancias de la ronda 1 sin
tocar**. Informe en `reports/datos/` con el nombre habitual.

**Operabilidad:** `scripts/check_tradable.py` usa `make_trading_client()` (guardia de paper) y
`get_asset(symbol)`; escribe `reports/datos/r2_operables_<sello>.md` con `symbol`, `tradable`,
`fractionable`, `status`. Símbolo de réplica no operable → se **anota** (lo quita Fable por
enmienda); principal no operable → código de salida 2 y «PARAR».

**Casos de prueba** (`tests/test_r2_data.py`, sintéticos):

| Caso | Entrada | Esperado |
|---|---|---|
| DA1 | 400 días laborables desde 2020-01-01 | `n_bars = 400`, `date_min_bars = index[364]`, `n_gaps = 0` |
| DA2 | 300 velas | `date_min_bars` = `NaT` |
| DA3 | cierres `[100, 100, 130, 130, 100]` | saltos en la 3.ª (+30 %) y la 5.ª (−23,1 %) fecha; el DataFrame **no** tiene columna de magnitud |
| DA4 | cierres `[100, 120, 100]` | ninguno (+20 % exacto no es «mayor»; −16,7 % tampoco) |
| DA5 | DA3 con `known` en la 3.ª fecha | `known_split` = sí / no |
| DA6 | tabla S9 (C sin vela el 02-01) | `missing_on_review_days` → una fila: 2024-02-01, `["C"]` |
| DA7 | símbolo que empieza a cotizar después de un día de revisión | ese día no cuenta como ausente |
| DA8 | calendario C1 y velas sin el 02-05 | `missing_on_tom_days` → (`SPY`, 02-05, `exit_signal`) |
| DA9 | vela en una fecha fuera del calendario | `dates_outside_calendar` la lista |
| DA10 | `seam_check` con un cierre movido un 0,1 % | lo lista; con 1e-9 de diferencia, no |

**Aceptación:** DA1–DA10 en verde sin red; los tres informes de `reports/datos/` generados en
el PC de Jorge; ninguna rentabilidad, media ni gráfico en ellos.

---

## 2. Lista de comprobación global (para dar la ronda de implementación por terminada)

- [ ] `ruff` y `pytest` en verde; los 162 tests que pasan hoy (2 saltados, medido el 2026-11-12)
      siguen pasando, más los de este documento.
- [ ] Ningún test de la ronda 1 cambia lo que comprueba (solo H-2: umbral explícito).
- [ ] `git diff` de `portfolio_sim.py`: únicamente `cm_at`, los grupos y el valor por defecto.
- [ ] `reports/`: nada de H5–H7; `oos_log.csv` con cabecera nueva y las 4 filas viejas intactas.
- [ ] Los tres TOML nuevos con `status = "preregistrada"`, `frozen = false` y
      `risk_per_trade = 0.01` marcado como provisional.
- [ ] `docs/INFORME_RONDA2_IMPL.md` escrito; dudas listadas; casillas de `tareas_sonnet.md`
      marcadas.
- [ ] Sin `git push`.

## 3. Qué no cubre este documento (y quién lo hace)

- Lanzar los IS, congelar (`frozen = true`), recorrer la escalera y escribir el veredicto:
  **Fable**, paso 3, tras auditar el código nuevo.
- Decisiones P14–P16 de `docs/auditoria_ronda2.md`: **Jorge**. Mientras no diga otra cosa
  valen las opciones tomadas; P15 (b) obligaría a cambiar el simulador **antes** del primer IS.
- El ejecutor diario (paso 5): solo se deja preparada `calendar.live_sessions`.
- No se ha verificado en esta sesión la operabilidad en Alpaca, ni la base de `^IRX`, ni la
  dirección exacta del CSV de FRED: lo hace Sonnet en R2-4 y R2-18 y lo documenta.
