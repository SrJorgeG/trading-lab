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
