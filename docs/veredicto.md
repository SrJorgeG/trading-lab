# Veredicto — 2026-11-11 (hora de Madrid)

> No es asesoramiento financiero. Solo paper. Todas las cifras salen de informes de `reports/`
> generados por scripts en esta sesión; la ruta va al lado de cada una.

**EN CURSO** — el resumen y los resultados se rellenan al final de la sesión.

## Auditoría del motor (checklist ✔/✘)

Tests y lint antes de empezar: `ruff check` → "All checks passed!"; `ruff format --check` →
"105 files already formatted"; `pytest -q` → **160 pasados, 2 saltados, 2 deseleccionados (red)**.

| # | Punto | ✔/✘ | Evidencia (código leído) |
|---|---|---|---|
| 1 | Ejecución a la apertura de la vela siguiente; sin datos futuros | ✔ | `portfolio_sim.py`: las señales de `t` (paso 5) quedan pendientes y se ejecutan a la apertura de `t+1` (pasos 2–3). `indicators.py`: canales con `shift(1)`, medias y Wilder solo hacia atrás; ningún `shift(-1)` ni `center=True`. `tests/test_lookahead.py` cubre las 4 candidatas (truncado y futuro "envenenado"). |
| 2 | Stops con hueco a la apertura; el stop gana al objetivo | ✔ | `portfolio_sim.py` paso 2: `open <= stop` → sale a la apertura (`stop_gap`); si no, `low <= stop` → sale al stop; el objetivo solo se mira después. No se entra si la apertura ya está en el stop o por debajo. En la vela de entrada también se comprueba el stop (prudente). |
| 3 | Costes en entrada y salida; estrés × 2 | ✔ | `costs.py`: slippage en contra en compra y en venta + comisión por lado; `cost_models(..., "stress")` multiplica todo por `costs.stress.multiplier = 2`. Los informes imprimen los costes usados. |
| 4 | Sizing 1 % con costes; redondeo abajo; máx. 3; sin apalancamiento; kill switch | ✔ | `risk.py`: `position_size` usa riesgo por unidad con slippage y comisiones de ida y vuelta; `floor_qty` redondea hacia abajo (enteros en ETFs); `apply_limits` aplica máx. posiciones, exposición ≤ 100 % del equity, caja y tope equity/3. Kill switch en `portfolio_sim` paso 4 (desactivado en las métricas por P1, episodios contados aparte). |
| 5 | Precios ajustados; fuente y fechas registradas; huecos detectados | ✔ (con nota) | `yf_source.py`: `auto_adjust=True`. Cada informe lista fuente, primera/última vela y fecha de entrada de cada activo. `data/validate.py` detecta huecos, duplicados y velas incoherentes. **Nota:** el contraste yfinance ↔ Alpaca dio REVISAR en 7 ETFs (ver abajo). |
| 6 | Benchmark en el mismo periodo y con el mismo tratamiento | ✔ | `runner.benchmark_equity`: mismo tramo `[a, b]`, mismos costes, mismo capital inicial; compra en la segunda vela. |
| 7 | Cada candidata implementada como dice `hipotesis.md` | ✔ | Comparado fórmula a fórmula: `donchian_atr.py` (H1/H4: `close > máx. de los 55 máximos anteriores`, salida `close < mín. de los 20 mínimos anteriores`, stop `close − 2·ATR(20)`, rank en ATRs), `tsmom_etf.py` (H2: `close/close.shift(252) − 1`, primera sesión del mes, `mom <= 0` sale), `rsi2_etf.py` (H3: `close > SMA200` y `RSI(2) < 10`, salida `close > SMA5`). Los 4 TOML coinciden con §2/§6 (hay un test que lo comprueba). |

Ningún ✘. Se sigue con la fase B.

### El contraste de datos yfinance ↔ Alpaca (REVISAR en DIA, EEM, EFA, GLD, IWM, SPY, VNQ)

Leída `docs/INVESTIGACION_DATOS.md` y **verificada** con las dos cachés locales
(`reports/datos/verificacion_fable_20261111.md`, script ad hoc que no simula ninguna estrategia):

- La investigación previa acertaba en lo principal (no es un "yfinance sin ajustar" y no se debe
  bloquear), pero no tenía la tabla del contraste. Con ella se ve la causa dominante: **unos pocos
  días sueltos, sobre todo de marzo de 2020** (el peor día es el 2020-03-17 en 6 de los 7 ETFs y
  el 2020-03-13 en SPY; `reports/datos/contraste_20261111-1555.md`), en los que los dos
  proveedores dan un cierre distinto. No es una deriva del ajuste por dividendos: la deriva de
  niveles en 11 años es de 0–21 pb en seis de los siete (96 pb en SPY).
- Quitando solo los 5 peores días de cada ETF, la correlación de rentabilidades diarias sube a
  ≥ 0,9995 en los siete (p. ej. VNQ de 0,9801 a 0,9997; GLD de 0,9958 a 1,0000).
- Señales: con las mismas funciones sobre una y otra fuente (tramo IS común, 2017-07 → 2020-12),
  `tsmom_etf` da **las mismas** entradas y salidas en los 7 ETFs; `rsi2_etf` y `donchian_etf`
  coinciden casi siempre (p. ej. SPY en `donchian_etf`: 121 de 125 días con señal de entrada
  coinciden; SPY en `rsi2_etf`: 44 de 46).
- **Decisión:** no afecta de forma material a los resultados; se mantienen yfinance como fuente y
  las tolerancias sin tocar (el resultado formal sigue siendo REVISAR). Queda como riesgo para
  el paper: Alpaca no reproducirá el backtest día a día, sobre todo en jornadas de pánico.
- **PENDIENTE DE JORGE (opcional):** ejecutar `uv run python scripts/diag_alpaca_vs_yf.py` para
  dejar el diagnóstico completo en `reports/datos/`. No cambia el veredicto.

### Observaciones de la auditoría (no invalidan nada, pero hay que saberlas)
- Las acciones enteras se calculan sobre precios **ajustados** (más bajos que los reales en el
  pasado): el redondeo histórico no es exactamente el que habría sido. Efecto pequeño.
- Una entrada sin hueco libre se descarta (no se guarda para otro día), como dice `hipotesis.md`.
- El stop dentro de la vela se ejecuta al precio del stop menos slippage; no se modela un
  deslizamiento extra en días de pánico.
- El efectivo no rinde nada y el Sharpe usa tipo libre de riesgo 0 (pesimista frente al benchmark).
- Los datos cripto de yfinance son precios agregados, no los del mercado de Alpaca (correlación
  0,996–0,998 en el contraste, dentro de tolerancia).
