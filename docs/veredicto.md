# Veredicto — 2026-11-11 (hora de Madrid)

> No es asesoramiento financiero. Solo paper. Todas las cifras salen de informes de `reports/`
> generados por scripts en esta sesión; la ruta va al lado de cada una.

## Resumen en 5 líneas (para Jorge, sin jerga)

1. **Ninguna de las 4 candidatas aprueba. No se opera nada en paper con ellas.** Es un resultado válido: las reglas se escribieron antes de mirar y se han aplicado tal cual.
2. El motor de backtest pasó la auditoría (7 de 7 puntos) y la discrepancia de datos entre yfinance y Alpaca no cambia los resultados (son unos pocos días sueltos de marzo de 2020).
3. Tres murieron con los datos de desarrollo, sin gastar su examen final: **H1** (cripto) porque cae más de un 10 % incluso arriesgando la mitad; **H2** (momentum mensual) porque no se distingue de entrar al azar; **H3** (RSI) porque no gana nada después de costes.
4. **H4** (ruptura de 55 días en ETFs) fue la única que llegó al examen final (datos 2021–2026) y lo suspendió en **un** criterio de 14: gana poco y de forma estable (3,45 % anual, caída máxima 7 %), pero queda por debajo de lo exigido frente a comprar SPY y no tocarlo (14,65 % anual). Según las reglas, si falla ahí, muere y no se retoca.
5. Qué hacer ahora: volver al paso 1 con ideas nuevas y, antes, que Jorge decida dos cosas de fondo (ver "PENDIENTE DE JORGE"): qué pesa más, perder poco o ganar a SPY, y si el freno de emergencia del 10 % se mantiene tal cual.

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

## Resultados por candidata

Abreviaturas de informes (todos bajo `reports/`):
`H1-IS` = `donchian_crypto/is_20261111-1613/resumen.md` ·
`H2-IS` = `tsmom_etf/is_20261111-1613/resumen.md` · `H2-WF` = `tsmom_etf/wf_20261111-1619/resumen.md` · `H2-ROB` = `tsmom_etf/robust_20261111-1620/resumen.md` · `H2-AZAR` = `robustez/tsmom_etf_nokill/azar_is_20261111-1634/resumen.md` ·
`H3-IS` = `rsi2_etf/is_20261111-1613/resumen.md` · `H3-WF` = `rsi2_etf/wf_20261111-1620/resumen.md` · `H3-ROB` = `rsi2_etf/robust_20261111-1624/resumen.md` ·
`H4-IS` = `donchian_etf/is_20261111-1613/resumen.md` · `H4-WF` = `donchian_etf/wf_20261111-1615/resumen.md` · `H4-ROB` = `donchian_etf/robust_20261111-1618/resumen.md` · `H4-AZAR` = `robustez/donchian_etf_nokill/azar_is_20261111-1629/resumen.md` · `H4-OOS` = `donchian_etf/oos_20261111-1636/resumen.md` · `H4-OOS×2` = `donchian_etf/oos_stress_20261111-1636/resumen.md` · `H4-OOS+1` = `donchian_etf/oos_delay1_20261111-1636/resumen.md` · `H4-FULL` = `donchian_etf/full_20261111-1636/resumen.md`.

"n/e" = no evaluado: la candidata ya había muerto y, por regla, no gasta su OOS.

### H1 `donchian_crypto` — RECHAZADA (muere en IS)

| Criterio | Umbral | Resultado | ✔/✘ | Informe |
|---|---|---|---|---|
| Corte rápido: expectancy IS con costes | > 0 | 3,62 R (66 operaciones) | ✔ | H1-IS |
| Calibración de riesgo (§3, P1) | DD máx. IS ≤ 10 % con 1 / 0,75 / 0,5 % | −32,6 % / −28,3 % / −22,6 % → ninguno | **✘** | H1-IS |
| Criterios 1–14 | — | n/e (OOS **no ejecutado**: sigue intacto) | — | — |

- Estrategia vs benchmark, solo IS (2015-10-01 → 2023-06-30, riesgo 1 %):

  | | CAGR | Sharpe | Máx. DD | Operaciones |
  |---|---|---|---|---|
  | H1 | 26,84 % | 1,03 | −32,62 % | 66 |
  | BTC comprar y mantener | 87,07 % | 1,23 | −83,40 % | — |

  (H1-IS). Máximo tiempo bajo el agua: 779 días. Episodios de caída > 10 %: 22 con riesgo 1 %, 8 con 0,5 % (H1-IS).
- Variantes probadas: 3 (los tres niveles de riesgo; ver `registro_pruebas.md`).
- Veredicto: **RECHAZADA**. En IS los números eran buenos, pero la regla dura 6 (parar si se cae un 10 %) la habría parado 8 veces incluso arriesgando el 0,5 % por operación. No se puede operar con el kill switch actual.

### H2 `tsmom_etf` — RECHAZADA (muere en IS)

Riesgo calibrado: **0,5 %** (DD IS −17,5 % / −13,8 % / −9,5 %; H2-IS).

| Criterio | Umbral | Resultado | ✔/✘ | Informe |
|---|---|---|---|---|
| Corte rápido: expectancy IS | > 0 | 0,94 R (43 operaciones) | ✔ | H2-IS |
| 5. Walk-forward | ≥ 60 % ventanas positivas | 5/8 (62 %) | ✔ | H2-WF |
| 6. Robustez de parámetros | ≥ 70 % vecinas | 8/8 (100 %) | ✔ | H2-ROB |
| 7. Costes × 2 (IS) | expectancy > 0 | 0,892 R | ✔ | H2-ROB |
| 8. Retraso 1 vela (IS) | expectancy > 0 | 0,815 R | ✔ | H2-ROB |
| 10. Monte Carlo (IS) | p95 DD ≤ 30 % | 4,1 % | ✔ | H2-ROB |
| 14. Mejor que el azar (IS) | p < 0,05 en Sharpe | **p = 0,597** (Sharpe real 0,41; percentil 40 %) | **✘** | H2-AZAR |
| 1–4, 9, 11–13 y parte OOS de 7–8 | — | n/e (OOS **no ejecutado**) | — | — |

- Estrategia vs benchmark, solo IS (2007-07-01 → 2020-12-31, riesgo 1 %): H2 CAGR 2,44 %, Sharpe 0,39, máx. DD −17,50 %, 43 operaciones; SPY CAGR 9,08 %, Sharpe 0,52, máx. DD −55,19 % (H2-IS). Con riesgo 0,5 %: CAGR 1,38 %, Sharpe 0,41 (H2-IS, tabla de calibración).
- Aviso extra: quitando las 5 mejores operaciones del IS quedan 54,46 $ (H2-ROB): casi todo el resultado son 5 operaciones.
- Variantes probadas: 11 (3 niveles de riesgo + 8 vecinas). Heredadas de la familia: 72.
- Veredicto: **RECHAZADA**. Entrar al azar y salir con las mismas reglas da, de media, lo mismo: lo poco que gana viene de estar comprado en activos que subieron, no de la señal.

### H3 `rsi2_etf` — RECHAZADA (muere en IS)

Riesgo calibrado: **0,5 %** (DD IS −16,4 % / −13,5 % / −9,9 %; H3-IS).

| Criterio | Umbral | Resultado | ✔/✘ | Informe |
|---|---|---|---|---|
| Corte rápido: expectancy IS | > 0 | 0,01 R (490 operaciones) | ✔ (por los pelos) | H3-IS |
| 5. Walk-forward | ≥ 60 % ventanas positivas | **4/8 (50 %)** | **✘** | H3-WF |
| 6. Robustez de parámetros | ≥ 70 % vecinas | 24/26 (92 %), pero sobre un Sharpe central de 0,04 | ✔ (sin valor) | H3-ROB |
| 7. Costes × 2 (IS) | expectancy > 0 | **−0,021 R** | **✘** | H3-ROB |
| 8. Retraso 1 vela (IS) | expectancy > 0 | **−0,004 R** | **✘** | H3-ROB |
| 10. Monte Carlo (IS) | p95 DD ≤ 30 % | 8,7 % | ✔ | H3-ROB |
| 14. Mejor que el azar | p < 0,05 | no lo he medido (ya había muerto por 5, 7 y 8) | — | — |
| Resto | — | n/e (OOS **no ejecutado**) | — | — |

- Estrategia vs benchmark, solo IS (riesgo 1 %): H3 CAGR 0,22 %, Sharpe 0,07, máx. DD −16,42 %, 490 operaciones; SPY CAGR 9,08 %, Sharpe 0,52, máx. DD −55,19 % (H3-IS).
- Variantes probadas: 31 (3 niveles de riesgo + 26 vecinas + 2 sueltas de `trend_n`).
- Veredicto: **RECHAZADA**. Tal como avisaba el informe de estrategias: entrando a la apertura siguiente y con costes, no queda nada.

### H4 `donchian_etf` — RECHAZADA (falla en OOS; OOS gastado)

Riesgo calibrado: **0,5 %** (DD IS −12,7 % / −11,6 % / −9,4 %; H4-IS). Parámetros congelados en el commit `14aed91` antes de ejecutar el OOS.
> **Nota de trazabilidad (2026-11-12, 15:32, Opus por delegación de Jorge; enmienda E20 de
> `docs/hipotesis_ronda2.md`):** `14aed91` quedó fuera de todas las ramas tras un rebase. Su
> equivalente en la rama es **`79a2881`** (mismo mensaje y hora, mismo cambio en
> `config/strategies/donchian_etf.toml`; solo difieren `scripts/diag_alpaca_vs_yf.py`,
> `src/tlab/data/crosscheck.py` y `tests/test_crosscheck.py`, comprobado con `git diff`).
> Etiquetas locales: `ronda1/congelacion-h4` → `79a2881` y `ronda1/congelacion-h4-original` →
> `14aed91`. El veredicto no cambia.

| Criterio | Umbral | Resultado | ✔/✘ | Informe |
|---|---|---|---|---|
| 1. Muestra | ≥ 100 operaciones | 253 (89 en OOS) | ✔ | H4-FULL, H4-OOS |
| 2. Expectancy OOS | > 0,10 R | 0,49 R | ✔ | H4-OOS |
| 3. Sharpe OOS ≥ 0,5 **y** [(a) Sharpe ≥ SPY **o** (b) DD ≤ 60 % del de SPY y CAGR ≥ 50 % del de SPY] | 0,5; (a) ≥ 0,91; (b) DD ≤ 14,70 % y CAGR ≥ 7,33 % | Sharpe 0,62 ✔; (a) 0,62 < 0,91 ✘; (b) DD 7,04 % ✔ pero CAGR 3,45 % ✘ | **✘** | H4-OOS |
| 4. DD máx. periodo completo | ≤ 20 % | −9,43 % | ✔ | H4-FULL |
| 5. Walk-forward | ≥ 60 % | 7/8 (88 %) | ✔ | H4-WF |
| 6. Robustez de parámetros | ≥ 70 % vecinas | 23/26 (88 %) | ✔ | H4-ROB |
| 7. Costes × 2 | expectancy > 0 en IS y OOS | IS 0,660 R; OOS 0,42 R | ✔ | H4-ROB, H4-OOS×2 |
| 8. Retraso 1 vela | expectancy > 0 en IS y OOS | IS 0,609 R; OOS 0,13 R | ✔ | H4-ROB, H4-OOS+1 |
| 9. Sin las 5 mejores (periodo completo) | ≥ 0 | 4.581,52 $ | ✔ | H4-FULL |
| 10. Monte Carlo | p95 DD ≤ 30 % | IS: 7,6 % ✔; periodo completo: no lo he medido (ya rechazada) | ✔ (IS) | H4-ROB |
| 11. Estabilidad | ≥ 2 de 3 subperiodos y ≥ 2 activos con ≥ 10 operaciones, expectancy > 0 | 3/3 (0,992 / 0,600 / 0,508 R); 7/7 activos | ✔ | H4-FULL |
| 12. Kill switch en OOS | no salta | 0 episodios (DD máx. OOS −7,04 %) | ✔ | H4-OOS |
| 13. Sin el mejor activo (DBC) | ≥ 0 | 6.130,42 $ | ✔ | H4-FULL |
| 14. Mejor que el azar (IS) | p < 0,05 | p = 0,047 (justo) | ✔ | H4-AZAR |

- Estrategia vs benchmark (riesgo 0,5 %):

  | Tramo | | CAGR | Sharpe | Máx. DD | Operaciones | Informe |
  |---|---|---|---|---|---|---|
  | IS (2007-07 → 2020-12) | H4 | 3,55 % | 0,70 | −9,4 % | 167 | H4-IS (calibración), H4-ROB |
  | | SPY | 9,08 % | 0,52 | −55,19 % | — | H4-IS |
  | OOS (2021-01 → 2026-10) | H4 | 3,45 % | 0,62 | −7,04 % | 89 | H4-OOS |
  | | SPY | 14,65 % | 0,91 | −24,50 % | — | H4-OOS |
  | | 60/40 (informativo) | 8,00 % | 0,78 | −21,2 % | — | H4-OOS |
  | Completo | H4 | 3,59 % | 0,69 | −9,43 % | 253 | H4-FULL |
  | | SPY | 10,64 % | 0,61 | −55,19 % | — | H4-FULL |

- Lo malo, también: en el OOS estuvo **1.139 días seguidos** por debajo de su máximo (1.520 en el periodo completo); win rate OOS 35,96 %; quitando las 5 mejores operaciones **del OOS** el resultado es −560,20 $; IEF y VNQ pierden en OOS (−0,656 R y −0,171 R); exposición media 40,3 % (todo en H4-OOS / H4-FULL). Con un día de retraso el Sharpe OOS baja a 0,23 (H4-OOS+1): es sensible a entrar tarde. Peor año y peor racha de pérdidas: no los he medido.
- El p = 0,047 contra el azar es justo y **no** está corregido por los 330 intentos heredados de la familia Donchian. DSR y PBO (informativos): no los he medido (el barrido extra con `param_sweep.py` está fuera del presupuesto pre-registrado).
- Variantes probadas: 29 (3 niveles de riesgo + 26 vecinas). Heredadas: 330.
- `reports/oos_log.csv` tiene 4 filas de `donchian_etf` con el mismo hash de parámetros: **1 OOS** (la que decide), 2 de estrés en OOS (costes × 2 y retraso) y 1 de periodo completo, como se anunció en la enmienda 6 de `hipotesis.md` antes de ver nada.
- Veredicto: **RECHAZADA**. Suspende solo el criterio 3: es estable y pierde poco, pero en 2021–2026 rinde menos de la mitad que SPY y con peor Sharpe. La regla dice que si falla en OOS, muere; no se reajusta.

## Selección final y por qué

**Ninguna aprobada → no se opera.** Los cuatro TOML quedan con `status = "rechazada"` y su motivo. No hay cartera combinada ni correlaciones que calcular (fase C no aplica).

## Expectativas para paper

No aplica: no hay ninguna estrategia aprobada para paper. No se dan rangos esperados de nada.

## ¿Estaba algún criterio mal planteado? (opinión aparte; los criterios se han aplicado igual)

- **Criterio 3 frente a la calibración de riesgo.** Para cumplir el kill switch del 10 % hubo que bajar el riesgo al 0,5 % por operación, y H4 queda con una exposición media del ~40 %. Así es muy difícil llegar a la mitad de la rentabilidad de un SPY invertido al 100 % en un mercado alcista, y la vía del Sharpe exigía ≥ 0,91. El pre-registro ya lo sabía y decidió no suavizarlo ("no se suaviza nada"). Hizo bien en no retocarlo después; lo que toca es que Jorge decida, **para la siguiente ronda y antes de ver datos**, contra qué se quiere comparar.
- **H1 y el kill switch.** El criterio 4 aceptaba hasta un 30 % de caída en cripto, pero la calibración P1 exige ≤ 10 % en IS. Las dos reglas juntas hacían casi imposible que una estrategia de tendencia en cripto pasara. Es coherente con la regla dura 6, pero conviene saber que H1 no murió por falta de resultados sino por incompatibilidad con ese freno.

## Qué aprendimos y qué probaría después

Aprendido:
1. El proceso funciona: 4 hipótesis, 74 variantes anotadas, un solo OOS gastado, y ninguna cifra retocada.
2. La restricción que más manda no es la señal sino el **kill switch del 10 %**: obliga a arriesgar tan poco que la cartera va medio vacía.
3. Las señales lentas con pocas operaciones (H2) no se pueden distinguir del azar con 43 operaciones; la reversión rápida (H3) no sobrevive a costes ni a entrar un día tarde.
4. La tendencia diversificada en ETFs (H4) sí muestra algo estable (13 de 14 criterios), con un perfil de "ganar poco, perder poco". No es lo que el criterio 3 pedía.

Qué probaría (ideas nuevas, cada una con su pre-registro nuevo; **no** las mismas reglas con otros números):
- **Decidir primero el objetivo** (ver PENDIENTE DE JORGE). Si el objetivo es "perder poco", el rival justo es una cartera prudente, no SPY al 100 %; si es "ganar a SPY", hacen falta estrategias que estén casi siempre invertidas.
- **Rotación siempre invertida** entre clases de activo (mantener los 2–3 ETFs más fuertes, incluido uno refugio), que ataca el problema de la exposición baja en vez del de la señal.
- **Marco semanal** (velas semanales) para tendencia: menos rupturas falsas y menos operaciones; es otra hipótesis, no un cambio de parámetro.
- **Cripto:** el OOS de H1 (2023-07 → 2026-10) **no se ha tocado**. Una ronda nueva podría plantear tendencia en cripto con otro presupuesto de riesgo (por ejemplo, un solo hueco para cripto), pero habiendo visto ya su IS: tendría que declararlo y tratar ese IS como contaminado.
- Aviso: el OOS de ETFs 2021–2026 ya se ha mirado una vez con H4. Cualquier candidata nueva sobre esos ETFs debe declararlo; la prueba limpia de verdad será el paper.

## Limitaciones y riesgos (lo que el backtest NO modela)

- Datos de yfinance (ajustados), no de Alpaca; en días de pánico los cierres difieren (ver auditoría).
- Slippage fijo (5 pb ETFs, 20 pb cripto); sin deslizamiento extra en huecos intradía ni órdenes rechazadas.
- Acciones enteras calculadas sobre precios ajustados; efectivo al 0 %; sin impuestos ni cambio EUR/USD.
- Solo 4 hipótesis y un OOS: "ninguna pasa" tampoco demuestra que estas ideas no sirvan en otras condiciones.
- OOS no del todo virgen (aviso de contaminación de `hipotesis.md` §0).

## PENDIENTE DE JORGE

1. **Objetivo y benchmark para la siguiente ronda:** ¿ganar a SPY o perder poco con rentabilidad positiva? De eso depende el criterio 3 del próximo pre-registro. Opción prudente tomada ahora: no cambiar nada y no operar.
2. **P1 (kill switch del 10 %):** se mantiene tal cual (regla dura 6). Es lo que mató a H1 y lo que obligó a bajar el riesgo en las demás. Cambiarlo (umbral, o rearmarlo tras una pausa) solo puede hacerlo Jorge, y en un pre-registro nuevo.
3. **Datos (opcional):** `uv run python scripts/diag_alpaca_vs_yf.py` para archivar el diagnóstico completo. No cambia el veredicto.
4. **Git:** en esta sesión git no tenía identidad configurada; los commits se han hecho con el mismo autor que los anteriores del repo (`SrJorgeG`) sin tocar la configuración. Sin `git push`.
5. P2–P6 de `hipotesis.md` siguen como estaban (ninguna estrategia llega a paper, así que no se activan).

## Pendiente para Sonnet

Ver `docs/tareas_sonnet.md` ("Tras el paso 3"). Nada bloqueante: no hay estrategia aprobada que implementar en el paso 4.
