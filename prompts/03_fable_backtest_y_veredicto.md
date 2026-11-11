# Prompt 03 — Backtests, pruebas de estrés y veredicto (modelo: **Fable**)

> Cómo lanzarlo: `cd ~/trading-lab && claude --model fable` → *"Lee y ejecuta prompts/03_fable_backtest_y_veredicto.md"*.
> Ideal: al empezar la **Tanda 2** (jueves 12 nov a partir de las 15:00, hora de Madrid). Puede ocupar 1–2 sesiones; si se corta, retómalo leyendo `docs/veredicto.md` (que se va rellenando) y `docs/registro_pruebas.md`.
> Al acabar: `git commit` y `/clear`.

---

## Tu papel
Eres el **auditor escéptico**. Tu trabajo no es encontrar una estrategia que "funcione", sino **intentar romper** cada candidata con honestidad. Un "ninguna pasa" bien argumentado es un resultado excelente. Lo único inaceptable es un número inventado o un criterio retocado para que algo apruebe.

## Lee primero
`CLAUDE.md`, `docs/hipotesis.md` (los criterios pre-registrados mandan), `docs/progreso_paso2.md` (limitaciones del motor, preguntas pendientes), y la skill `backtest-expert`.

## Ahorro de cupo (importante)
- Tú **lees informes** (`reports/**/resumen.md`, CSV pequeños) y **ejecutas scripts**; no leas datos crudos ni archivos enormes.
- Si hace falta **código nuevo o cambios de más de ~20 líneas**, no lo escribas tú: descríbelo en `docs/tareas_sonnet.md` y **para** esa línea de trabajo (Jorge lo lanzará con Sonnet y volverás).
- Arreglos pequeños y evidentes (≤ 20 líneas, con su test) sí puedes hacerlos.

## Fase A — Auditoría del motor (antes de creerte ningún número)
1. `uv run pytest -q` y `uv run ruff check .` → deben estar en verde. Si no, **para** y anota en `docs/tareas_sonnet.md`.
2. Revisa (leyendo el código, no todo el repo) estos puntos y deja una checklist con ✔/✘ en `docs/veredicto.md`:
   - [ ] Ejecución a la apertura de la vela siguiente; ningún `shift(-1)` ni indicador con datos futuros.
   - [ ] Stops con gap a la apertura; stop gana si stop y objetivo coinciden.
   - [ ] Costes aplicados en entrada y salida; estrés × 2 funciona.
   - [ ] Sizing del 1 % con costes; redondeo hacia abajo; máx. 3 posiciones; sin apalancamiento; kill switch.
   - [ ] Precios ajustados en acciones; fuente y fechas de datos registradas; huecos detectados.
   - [ ] Benchmark calculado en el mismo periodo y con el mismo tratamiento.
   - [ ] Cada candidata implementada como dice `docs/hipotesis.md` (compara fórmula a fórmula).
3. Si algo sale ✘ y afecta a los resultados: **para**. Escribe la tarea en `docs/tareas_sonnet.md` y termina la sesión explicándolo. No sigas con números contaminados.

## Fase B — Pipeline por candidata (en este orden, sin saltarse pasos)
Para cada candidata H1…Hn:

1. **In-sample** (`--mode is`, costes base). Primera foto. Si ya aquí la expectancy es ≤ 0 con costes, **descartada** (anótalo y pasa a la siguiente).
2. **Ajuste limitado** (opcional): solo dentro del presupuesto de variantes pre-registrado y solo con datos in-sample. Registra **todas** las variantes en `docs/registro_pruebas.md`. Prefiere los parámetros por defecto; cambia solo si hay un motivo que no sea "da más rentabilidad".
3. **Walk-forward** (`--mode wf`). % de ventanas positivas.
4. **Robustez** (`--mode robust`): rejilla ±25 %, costes × 2, retraso de 1 vela, quitar las 5 mejores operaciones, Monte Carlo, subperiodos, otros activos del universo. Mira si el rendimiento es una **meseta** (bien) o un **pico aislado** (sobreajuste).
5. **Out-of-sample**, **una sola vez** y solo si ha superado 1–4: congela los parámetros en `config/strategies/<id>.toml`, haz commit, y ejecuta `--mode oos --confirm-oos`. Lo que salga, sale. **Si falla, muere**: prohibido reajustar y volver a mirar el OOS.
6. Aplica la **checklist de aceptación de `docs/hipotesis.md` §4 de forma mecánica**: cada casilla ✔ o ✘ con el número exacto y el archivo de informe del que sale.

## Fase C — Selección
- Si pasan varias: aplica el criterio de selección pre-registrado (simplicidad, robustez, correlación < 0,5 si eliges 2). Calcula la correlación de retornos diarios con un script, no a ojo.
- Elige **como máximo 2**. Cambia `status = "aprobada_paper"` en su `config/strategies/<id>.toml`; las demás, `status = "rechazada"` con el motivo.
- Si no pasa ninguna: `status = "rechazada"` en todas y una sección "Qué aprendimos y qué probaría después" (ideas nuevas, **no** las mismas con otros números).

## Entregable: `docs/veredicto.md`
```markdown
# Veredicto — <fecha, hora de Madrid>
## Resumen en 5 líneas (para Jorge, sin jerga)
## Auditoría del motor (checklist ✔/✘)
## Resultados por candidata
### H1 <id>
| Criterio | Umbral | Resultado | ✔/✘ | Informe |
|---|---|---|---|---|
(una fila por criterio de la checklist)
- Estrategia vs benchmark (IS / OOS): tabla con CAGR, Sharpe, máx. DD, nº operaciones
- Variantes probadas: N (ver registro_pruebas.md)
- Veredicto: APROBADA PARA PAPER / RECHAZADA (motivo)
## Selección final y por qué
## Expectativas para paper (rangos, no promesas)
- Operaciones por mes esperadas, win rate, expectancy en R, peor racha de pérdidas en el backtest, drawdown típico
## Limitaciones y riesgos (lo que el backtest NO modela)
## Pendiente para Sonnet
```

## Reglas de honestidad (obligatorias)
- **Cada cifra** del veredicto lleva al lado la ruta del informe de `reports/` del que sale. Si no hay informe, la cifra no se pone.
- Reporta también lo malo: peor año, peor racha, máximo tiempo bajo el agua (en drawdown).
- No uses palabras como "garantizado", "seguro" o "rentable" sin matiz. Habla de "en el backtest, con estos supuestos…".
- **No modifiques los criterios de `docs/hipotesis.md`.** Si crees que un criterio estaba mal planteado, dilo en una sección aparte, pero aplícalo igual.

## Criterios de "hecho"
- `docs/veredicto.md` completo con la plantilla, todas las cifras con su informe.
- `config/strategies/*.toml` con el `status` actualizado y parámetros congelados de las aprobadas.
- `reports/oos_log.csv` con **una** ejecución OOS por estrategia que llegó a esa fase.
- `docs/registro_pruebas.md` al día.

## Condiciones de parada
- Tests en rojo o auditoría con ✘ relevante → parar y dejar tareas para Sonnet.
- Si llevas consumido mucho cupo (mira `/usage`; si Fable va por encima del ~40 % del límite semanal), cierra la candidata en curso, guarda el estado en `docs/veredicto.md` ("EN CURSO: siguiente paso = …") y termina.
- Nunca ejecutes órdenes en Alpaca en este paso (ni paper). Solo backtests.
- Al terminar, resume en 10 líneas: qué pasa, qué no y qué hacer ahora (paso 4 si hay aprobadas; volver al paso 1 si no).
