# Prompt 05 — Ejecutor diario en paper + programación automática (modelo: **Sonnet**)

> Cómo lanzarlo: `cd ~/trading-lab && claude --model sonnet` → *"Lee y ejecuta prompts/05_sonnet_paper_diario.md"*.
> Requisitos: `STRATEGY.md` y `docs/signals_spec.md` (paso 4) existen; `.env` con claves de **paper**.
> Al acabar: `git commit` y `/clear`.

---

## Tu papel
Programas el **ejecutor diario**: Python puro, determinista, sin IA en la toma de decisiones. Implementas `STRATEGY.md` y `docs/signals_spec.md` **literalmente**. Si algo es ambiguo: la opción conservadora es **no operar** y anotarlo. No cambias parámetros ni reglas.

**La ejecución diaria NO usa a Claude.** Las órdenes las pone `alpaca-py` desde nuestro script, con la guardia de paper y las reglas duras dentro. El MCP de Alpaca queda solo para consultas manuales (y en modo lectura, ver `SETUP_ALPACA.md`).

## Lee primero
`CLAUDE.md`, `STRATEGY.md`, `docs/signals_spec.md`, `docs/tareas_sonnet.md`, `src/tlab/risk.py`, `src/tlab/broker/guard.py`, las estrategias aprobadas en `src/tlab/strategies/`.

## Horarios (razonar SIEMPRE en hora de Nueva York)
- Sesión regular EE. UU.: 9:30–16:00 Nueva York = **15:30–22:00 Madrid** la mayor parte del año, pero **14:30–21:00 Madrid** durante las semanas en que EE. UU. y Europa cambian de hora en fechas distintas (2.º domingo de marzo → último domingo de marzo; último domingo de octubre → 1.er domingo de noviembre). Por eso los temporizadores usan la zona `America/New_York` y el código consulta `get_clock()` / `get_calendar()` de Alpaca (festivos y cierres anticipados).
- Las señales se calculan con la **última vela diaria cerrada** (la sesión anterior). Así el backtest ("se ejecuta en la apertura siguiente") y la realidad coinciden.

| Sesión del script | Hora Nueva York | Madrid (habitual) | Qué hace |
|---|---|---|---|
| `pre-open` | 08:45 lun–vie | 14:45 | Señales con la vela de ayer → órdenes **`opg`** (*market on open*: se ejecutan en la subasta de apertura) de salida y de entrada, **acciones enteras**. Ventana válida: hasta las **09:25**; fuera de ella **no** envía entradas (Alpaca rechaza `opg` entre 9:28 y 19:00). |
| `post-open` | 09:50 lun–vie | 15:50 | Reconciliar ejecuciones; poner **stop `gtc`** a cada posición nueva; cancelar stops de posiciones cerradas; comprobar que **toda** posición tiene stop; escribir el diario. |
| `crypto` (si hay estrategia cripto) | 00:15 **UTC** diario | 01:15 (invierno) | Las velas `1Day` nativas de Alpaca cripto ya son días **UTC** (`t=…T00:00:00Z`; verificado nov 2026, ver `docs/VERIFICACIONES.md`). Prefiere esas barras; remuestrear velas de 1 h a días UTC debe coincidir. Si el backtest usó otra definición, usa la del backtest y documéntalo. **No** cortes a medianoche ET (los ejemplos viejos de la doc de Alpaca que muestran 05:00 UTC están desfasados). Entradas/salidas con orden de mercado `gtc`; stop como **stop-limit `gtc`** (límite = stop × (1 − 1 %)) **más** comprobación por software: si el precio está por debajo del stop y la posición sigue abierta → venta a mercado. Cripto en Alpaca solo admite `gtc`/`ioc`. |

## Entregables

### 1. `scripts/signals.py`
Implementa `docs/signals_spec.md`: entrada (fecha, config, estado) → JSON determinista. `--date`, `--dry-run`, `--json-out`. Reutiliza `tlab.strategies` y `tlab.risk` (las **mismas** funciones que el backtest; prohibido duplicar lógica).

### 2. `scripts/run_daily.py --session {pre-open,post-open,crypto} [--dry-run]`
Orden exacto (igual que el checklist de `STRATEGY.md`):
1. `assert_paper_only()`; crear `TradingClient(key, secret, paper=True)`. Si algo no cuadra → salir con error.
2. Si existe `KILL_SWITCH` → no operar, anotar en el diario y salir (código 3).
3. Bloqueo para no ejecutar dos veces a la vez (`state/run.lock`, o `flock` desde el temporizador).
4. Comprobar calendario/reloj de Alpaca: ¿día hábil? ¿estamos en la ventana de esta sesión? Si no → salir sin operar (y anotarlo).
5. **Sincronizar con el broker** (la verdad es el broker): posiciones, órdenes abiertas, equity. Comparar con `state/positions.json`. Si hay discrepancias → **no abrir nada nuevo**, anotar "DESCUADRE" y seguir solo con salidas/stops.
6. **Equity del experimento** = `virtual_equity_usd` (10.000 $) + P&L realizado y no realizado de nuestras operaciones desde el inicio (guardado en `state/`). Se usa para el sizing y el kill switch, aunque la cuenta paper tenga 100.000 $. Actualizar el máximo en `state/peak.json`.
7. **Kill switch:** si el drawdown del experimento > 15 % → cerrar todas las posiciones, cancelar órdenes, crear `KILL_SWITCH`, anotar y salir (código 2).
8. Datos: cargar velas (caché + actualización) y validar. Datos insuficientes → `SKIP` para ese símbolo.
9. Señales (`signals.py`) → plan de órdenes: **primero salidas**, luego stops, luego entradas por `rank`; respetar máx. 3 posiciones, 1 % de riesgo, exposición ≤ 100 %, caja disponible; cantidad 0 → `SKIP`.
   - **Ojo con las órdenes que reservan acciones:** Alpaca bloquea la cantidad de una posición que ya tiene una orden de venta abierta (el stop `gtc`). Antes de enviar una salida por señal, **cancela primero el stop** de esa posición y confirma la cancelación; si después la salida no se ejecuta, `post-open` debe volver a poner el stop. Lo mismo al mover un stop (usa `replace_order` o cancelar + crear) y en cripto antes de una venta por software.
10. Enviar órdenes (salvo `--dry-run`) con **`client_order_id` determinista** = `<estrategia>-<símbolo>-<AAAAMMDD>-<acción>` para que re-ejecutar no duplique órdenes (Alpaca rechaza ids repetidos: trátalo como "ya enviada").
11. Verificar estado de cada orden (aceptada, rechazada, parcial). En `post-open`, poner stops y comprobar que toda posición tiene stop; si una no lo tiene y no se puede poner → cerrarla a mercado y anotarlo.
12. **Diario** (siempre, también en `--dry-run` y cuando no hay nada que hacer):
    - `journal/trades.csv` (añadir filas): `ts_utc, ts_madrid, session, strategy, strategy_version, symbol, action, side, qty, order_type, time_in_force, client_order_id, broker_order_id, status, fill_price, stop_price, risk_usd, r_planned, reason, dry_run`.
    - `journal/AAAA-MM-DD.md` (hora de Madrid): equity del experimento, drawdown, posiciones con su stop, acciones con su **motivo** (la `reason` de la regla), incidencias.
13. Códigos de salida: 0 ok, 1 error, 2 kill switch disparado, 3 kill switch ya activo, 4 descuadre con el broker, 5 fuera de ventana.

### 3. `src/tlab/broker/alpaca_paper.py`
Envoltorio fino sobre `alpaca-py` (órdenes `opg`/`day`/`gtc`, stops, cancelar, posiciones, cuenta, reloj, calendario) que **siempre** pasa por la guardia. Interfaz abstracta para poder usar un **broker falso** en los tests.

### 4. Tests (sin red)
| Test | Qué demuestra |
|---|---|
| `test_signals_golden` | Los ejemplos a mano de `docs/signals_spec.md` producen el JSON esperado byte a byte. |
| `test_signals_match_backtest` | Para un periodo histórico, las decisiones de `signals.py` día a día coinciden con las entradas/salidas del backtest (`portfolio_sim`). |
| `test_dry_run_sends_nothing` | En `--dry-run` el broker falso no recibe ninguna orden, pero el diario se escribe. |
| `test_idempotent_rerun` | Ejecutar dos veces la misma sesión no duplica órdenes. |
| `test_opg_window` | Fuera de la ventana `pre-open` no se envían entradas. |
| `test_kill_switch_runner` | Drawdown > 15 % → cierra todo, crea `KILL_SWITCH`; con `KILL_SWITCH` presente no opera. |
| `test_reconcile_mismatch` | Descuadre broker/estado → no hay entradas nuevas, código 4. |
| `test_exit_cancels_stop_first` | Una salida por señal cancela antes el stop de esa posición; si la salida no se ejecuta, `post-open` repone el stop. |
| `test_every_position_has_stop` | Tras `post-open`, toda posición tiene stop o se ha cerrado. |
| `test_limits_runner` | Nunca > 3 posiciones, riesgo ≤ 1 %, exposición ≤ 100 %, sin cortos. |
| `test_guard_in_runner` | Con `ALPACA_PAPER_TRADE=false` el runner no arranca. |

### 5. Programación automática en CachyOS (systemd de usuario, **recomendado**)
Crea en el repo `deploy/systemd/` los archivos y en `docs/operacion.md` los comandos. Ejemplo para `pre-open` (crea igual `post-open` y, si aplica, `crypto`):

`deploy/systemd/tlab-preopen.service`
```ini
[Unit]
Description=trading-lab: sesion pre-open (paper)
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=%h/trading-lab
ExecStart=/usr/bin/flock -n %h/trading-lab/state/run.lock %h/.local/bin/uv run python scripts/run_daily.py --session pre-open
```
`deploy/systemd/tlab-preopen.timer`
```ini
[Unit]
Description=trading-lab pre-open, lun-vie 08:45 hora de Nueva York

[Timer]
OnCalendar=Mon..Fri *-*-* 08:45:00 America/New_York
Persistent=true

[Install]
WantedBy=timers.target
```
- `post-open`: `OnCalendar=Mon..Fri *-*-* 09:50:00 America/New_York`.
- `crypto`: `OnCalendar=*-*-* 00:15:00 UTC`.
- `Persistent=true` hace que, si el PC estaba apagado, se ejecute al encender: por eso el script **comprueba la ventana horaria** y no envía `opg` tarde.
- Ruta de `uv`: compruébala con `command -v uv` (puede ser `/usr/bin/uv` si se instaló con pacman) y ajústala.
- Comandos (en `docs/operacion.md`):
```bash
mkdir -p ~/.config/systemd/user ~/trading-lab/state ~/trading-lab/logs
cp ~/trading-lab/deploy/systemd/tlab-*.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now tlab-preopen.timer tlab-postopen.timer   # (+ tlab-crypto.timer)
loginctl enable-linger "$USER"          # que funcione aunque no tengas sesión abierta
systemctl --user list-timers            # ver próximas ejecuciones
journalctl --user -u tlab-preopen.service -n 50   # ver la última ejecución
```
- Recordatorio: **el PC tiene que estar encendido** a esas horas (14:45 y 15:50 de Madrid, lun–vie). Si no, se pierde ese día (y el script lo anota).

**Alternativa con cron** (en CachyOS cron no viene siempre instalado: `sudo pacman -S cronie && sudo systemctl enable --now cronie`). `crontab -e`:
```cron
CRON_TZ=America/New_York
45 8 * * 1-5 cd $HOME/trading-lab && /usr/bin/flock -n state/run.lock $HOME/.local/bin/uv run python scripts/run_daily.py --session pre-open >> logs/cron.log 2>&1
50 9 * * 1-5 cd $HOME/trading-lab && /usr/bin/flock -n state/run.lock $HOME/.local/bin/uv run python scripts/run_daily.py --session post-open >> logs/cron.log 2>&1
```
(Si tu cron no soporta `CRON_TZ`, usa systemd: poner horas de Madrid a mano falla dos veces al año.)

### 6. (Opcional) Nota diaria con Sonnet vía `claude -p`
Solo si Jorge quiere un comentario en lenguaje natural; **no toma decisiones** y gasta un poco de cupo. Crea `scripts/nota_diaria.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/trading-lab"
claude -p "Lee CLAUDE.md, STRATEGY.md y journal/$(date +%F).md. Añade al final de ese archivo una sección '## Nota de Sonnet' de máximo 8 líneas: qué se hizo hoy, si se cumplieron todas las reglas duras (sí/no y por qué) y cualquier anomalía. No inventes cifras: usa solo las del diario. No cambies nada más." \
  --model sonnet --max-turns 6 --permission-mode dontAsk --strict-mcp-config \
  --allowedTools "Read" "Edit(./journal/**)"
```
- `--model sonnet` explícito (si no, usaría el último modelo elegido con `/model`, quizá Fable).
- `--permission-mode dontAsk` + `--allowedTools`: solo puede leer y editar `journal/`. `--strict-mcp-config` sin `--mcp-config` = **sin** MCP (no puede tocar Alpaca).
- Comprueba la sintaxis con `claude --help` en la versión instalada antes de programarlo; lánzalo con un timer a las 10:05 Nueva York si Jorge lo quiere.

## Criterios de aceptación
1. `uv run pytest -q` y `uv run ruff check .` en verde (pega el resumen real).
2. `uv run python scripts/run_daily.py --session pre-open --dry-run` y `--session post-open --dry-run` funcionan contra la cuenta **paper** real (lee cuenta, calendario y datos; no envía nada) y escriben el diario. Pega la salida.
3. `deploy/systemd/*` y `docs/operacion.md` creados. **No actives** los temporizadores tú: deja los comandos para que Jorge los ejecute.
4. `docs/operacion.md` incluye: cómo arrancar/parar, cómo ver logs, qué hacer si salta el kill switch (y que solo Jorge borra `KILL_SWITCH`), cómo pausar (`systemctl --user stop tlab-*.timer`).

## Condiciones de parada
- **Nunca** `paper=False`, nunca URL real, nunca desactivar la guardia "para probar".
- No envíes órdenes reales a la cuenta paper en esta sesión salvo **una** orden de prueba si Jorge lo pide explícitamente; por defecto, todo en `--dry-run`.
- Si `STRATEGY.md` y el código de la estrategia discrepan, **para** y anótalo en `docs/tareas_sonnet.md` como "PREGUNTA PARA FABLE".
- 3 intentos fallidos con el mismo error → para y documenta.
- Al terminar, explica en 8 líneas qué pasará cada día, a qué horas (Nueva York y Madrid) y qué comandos tiene que ejecutar Jorge.
