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

- [ ] R2-1. **Kill switch al 15 %** (decisión de Jorge, regla dura 6): `config/settings.toml`
      (`kill_switch_drawdown = 0.15`), valores por defecto en `risk.check_kill_switch`,
      `portfolio_sim.SimConfig`, `robustness.kill_switch_episodes`, `montecarlo.DEFAULT_KILL` y
      `targets.py`; textos de `README.md` y de `prompts/01`, `02` y `05`. Los tests que pasan
      `0.10` como argumento explícito no se tocan. Los informes de la ronda 1 **no** se regeneran.
- [ ] R2-2. `robustness.calibrate_risk`: el límite sale del TOML de la estrategia
      (`calibration_dd_limit`, 0.12 en la ronda 2); las candidatas de la ronda 1 conservan 0.10.
- [ ] R2-3. **Datos:** añadir a `settings.toml` y descargar con yfinance (ajustado) desde
      1998-12-01: `XLB XLE XLF XLI XLK XLP XLU XLV XLY`, `EWJ EWG EWU EWC EWQ EWI EWA EWL EWH`,
      `MDY`; y bajar la historia de `SPY`, `IWM`, `EFA`, `EEM`, `IEF` desde su primera vela.
      Pasar `data/validate.py`. Escribir en `reports/datos/` una tabla con primera y última vela,
      nº de velas, huecos y fecha en la que cada símbolo llega a 365 velas. Comprobar con Alpaca
      (`get_asset`) que todos son operables. Aplicar la regla de §3.1 si algo no existe (retrasar
      el inicio / quitar el símbolo de la réplica) y **anotarlo para Fable, no decidirlo**.
- [ ] R2-4. **Caja:** serie diaria del tipo de las letras a 3 meses (`^IRX` en yfinance, en % anual)
      y benchmark "caja" = capital × ∏(1 + tipo/100)^(1/252). Si `^IRX` no está o tiene huecos
      largos, alternativa: el CSV público `DTB3` de FRED (sin clave). Documentar cuál se usa. Test
      con una serie constante del 5 % → CAGR 5 %.
- [ ] R2-5. **Tramos múltiples** en el TOML y en `scripts/backtest.py`: `is`, `replica`,
      `holdout_old` (2000-07-01 → 2007-06-30), `holdout_new` (2021-01-01 → 2026-10-31), `full`
      (2000-07-01 → 2026-10-31), cada uno con su universo y su `slippage_bps` (5 / 15 / 10 / 5 /
      el del tramo que toque en `full`: 10 hasta 2007-06-30 y 5 después). Guarda de un solo uso
      por (estrategia, tramo, hash de parámetros) en `reports/oos_log.csv`, con columnas nuevas
      `tranche`, `costs`, `entry_delay` (cubre la tarea pendiente del paso 3). Orden obligado:
      `replica` → `holdout_old` → `holdout_new` → `full`; el script se niega a saltarse uno.
- [ ] R2-6. **Señales de panel** (§6.1): tipo `generate_signals_panel`, registro aparte, integración
      en `runner` y en los tests de look-ahead. Test: en una misma apertura las salidas liberan
      hueco antes que las entradas.
- [ ] R2-7. Estrategias `sector_mom` y `sector_lowvol` (§6.2) con los casos S1–S4 como tests; dos
      TOML con `status = "preregistrada"`.
- [ ] R2-8. Estrategia `tom_etf` (§6.3): calendario inyectado en `params["sessions"]`, casos C1–C4,
      TOML. Para el modo en vivo, función que construya el calendario con `get_calendar`.
- [ ] R2-9. **Monos a medida** (§3.4) en `random_benchmark.py`: modo `rank` (sortea el orden de los
      aptos en cada revisión) y modo `window` (sortea la sesión de entrada de cada mes; salida 4
      sesiones después). Semilla 42, 1.000. Test de reproducibilidad.
- [ ] R2-10. **Informe:** relación CAGR/|caída| de estrategia, SPY y 60/40; CAGR de caja e `IEF`;
      CAGR conjunto de los dos tramos reservados (fórmula del criterio 16a); criterio 16d sobre el
      trozo de `full` desde 2002-08-01; subperiodos del criterio 11; episodios de kill switch al
      15 %; variante informativa "efectivo rindiendo como la caja"; peor año y peor racha.
- [ ] R2-11. **Banda para el paper** (§3.6 b): remuestreo por bloques de 21 sesiones, 10.000
      trayectorias, semilla 42, percentiles 5/50/95 a 6 y 12 meses. Solo la herramienta y su test.
- [ ] R2-12. Cartera combinada de §5.4 (sectores con 2 huecos + `tom_etf` con 1 hueco en `SPY`):
      solo dejar preparado el modo y un test sintético; no ejecutarlo.
- [ ] R2-13. `ruff` y `pytest` en verde; informe corto `docs/INFORME_RONDA2_IMPL.md` con dudas de
      interpretación para Fable (como `INFORME_PASO2.md`).
