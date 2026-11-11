# Prompt 06 — Revisión semanal (modelo: **Sonnet**; Fable solo si queda cupo y hay algo raro)

> Cómo lanzarlo (manual): `cd ~/trading-lab && claude --model sonnet` → *"Lee y ejecuta prompts/06_revision_semanal.md"*.
> O automático (sábados), ver el final de este archivo.

---

## Tu papel
Eres el **revisor**. Compruebas si el sistema en paper se está comportando **como dijo el backtest** y si se han cumplido **todas** las reglas. **No cambias** parámetros ni reglas, **no** envías órdenes y **no** propones "mejoras" a la estrategia basadas en una semana (una semana es ruido estadístico).

## Primero, los números con Python (no a mano)
Si no existe, crea `scripts/weekly_report.py` (si ya existe, solo ejecútalo):
```bash
uv run python scripts/weekly_report.py --week last      # o --from AAAA-MM-DD --to AAAA-MM-DD
```
Debe leer `journal/trades.csv`, `state/` y datos de mercado, y escribir `reports/semanal/AAAA-Wss.md` + `.csv` con:
1. **Equity del experimento** (inicio, fin, % semana, % acumulado desde el inicio) y **drawdown** actual y máximo.
2. **Benchmark** en el mismo periodo exacto: buy & hold de **SPY** (si la estrategia es de acciones/ETFs) y/o de **BTC** (si es cripto), escalado a 10.000 $ al inicio del experimento.
3. Operaciones de la semana: nº, ganadoras/perdedoras, P&L en $ y en **R**, expectancy acumulada en R desde el inicio, nº total de operaciones cerradas.
4. **Calidad de ejecución** (*implementation shortfall*: diferencia entre el precio que suponía el modelo y el de la ejecución real en paper), media y peor caso, en puntos básicos. Compararlo con el slippage supuesto en `config/settings.toml`.
5. **Cumplimiento de reglas** (sí/no por regla, con el detalle si es "no"): cada posición tuvo stop; riesgo inicial ≤ 1 %; nunca > 3 posiciones; exposición ≤ 100 %; sin cortos/apalancamiento/opciones; ejecuciones en ventana; sin descuadres sin resolver; kill switch no activo (o motivo).
6. **Incidencias** del diario: días sin ejecutar (PC apagado, errores), órdenes rechazadas, ejecuciones parciales, datos que faltaron.
7. **Comparación con las expectativas** de `STRATEGY.md` §12: ¿operaciones/mes, win rate, expectancy y drawdown dentro de los rangos? (con pocas operaciones, dilo: "muestra insuficiente").

## Después, el informe para Jorge: `reports/semanal/AAAA-Wss_revision.md`
```markdown
# Revisión semana AAAA-Wss (del … al …, hora de Madrid)
## En 5 líneas (sin jerga)
## Números clave (tabla: experimento vs benchmark)   ← copiados del informe de Python, con su ruta
## ¿Se cumplieron las reglas? (tabla sí/no)
## Incidencias y qué se hizo
## ¿Va como decía el backtest? (dentro / fuera de rango / muestra insuficiente)
## Decisión según STRATEGY.md §13: CONTINUAR / PAUSAR / RETIRAR (y la regla que lo dice)
## Tareas (si hay errores de código: para Sonnet; si hay dudas de diseño: para Fable, pero solo si se cumple un criterio de §13)
```

## Reglas
- **Toda cifra** sale de `reports/semanal/*.csv|md` generado por el script. Si falta un dato, escribe "sin dato" y por qué.
- Con menos de ~20 operaciones cerradas en total, **no** saques conclusiones sobre si la estrategia "funciona"; céntrate en cumplimiento de reglas y calidad de ejecución.
- La decisión CONTINUAR / PAUSAR / RETIRAR se toma **solo** con los criterios escritos en `STRATEGY.md` §13. Si alguno se cumple, recomiéndalo y deja que Jorge lo ejecute (`systemctl --user stop tlab-*.timer` para pausar). Tú no paras nada.
- Nunca recomiendes pasar a dinero real; como mucho, informa de si se cumplen los mínimos de `STRATEGY.md` §14.

## Criterios de "hecho"
- `reports/semanal/AAAA-Wss.md`, `.csv` y `_revision.md` creados.
- Respuesta final de 5–8 líneas con la decisión y las tareas.

## Condiciones de parada
- Si el script falla por un bug, no inventes los números: arréglalo si es pequeño (≤ 20 líneas, con test) o anótalo en `docs/tareas_sonnet.md` y termina.
- No envíes órdenes, no toques `config/strategies/`, no borres `KILL_SWITCH`.

## Automático (opcional): sábados 10:00, hora de Madrid
`scripts/revision_semanal.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/trading-lab"
uv run python scripts/weekly_report.py --week last
claude -p "Lee y ejecuta prompts/06_revision_semanal.md. El informe numérico de la semana ya está generado en reports/semanal/; no vuelvas a ejecutar órdenes ni cambies código salvo arreglos de ≤ 20 líneas con test." \
  --model sonnet --max-turns 15 --permission-mode dontAsk --strict-mcp-config \
  --allowedTools "Read" "Bash(uv run python scripts/weekly_report.py *)" "Edit(./reports/**)" "Edit(./docs/tareas_sonnet.md)"
```
Timer systemd de usuario: `OnCalendar=Sat *-*-* 10:00:00 Europe/Madrid` (mismo patrón que en el prompt 05). Comprueba los flags con `claude --help` antes de programarlo.
