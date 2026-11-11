# Trading Lab Kit — Fable diseña, Sonnet ejecuta (solo PAPER)

Kit listo para usar en **jorge-cachy** con Claude Code. Objetivo de la semana:

1. **Fable** (el modelo más listo, incluido en tu plan Pro hasta el **lun 17 nov 08:59, hora de Madrid**, con un tope del 50 % del límite semanal; hace falta Claude Code **v2.1.321+**) investiga, propone y **valida con backtest** 1–2 estrategias **basadas en reglas escritas**.
2. Las deja documentadas en un `STRATEGY.md` tan claro que luego las pueda ejecutar **Sonnet o un script de Python sin IA**.
3. Se ejecutan a diario en **paper trading** (dinero ficticio) en **Alpaca**. **Cero dinero real.**

> Aviso honesto: esto es un experimento educativo. Ningún backtest garantiza nada y una semana de paper no demuestra nada estadísticamente. Lo que sí podemos conseguir esta semana: un sistema bien hecho, reglas claras y un historial que vaya creciendo.

---

## Qué hay en el kit

| Archivo | Para qué sirve | Quién lo usa |
|---|---|---|
| `README.md` | Este documento: orden de uso y plan por tandas | Tú |
| `SETUP_ALPACA.md` | Crear la cuenta paper, sacar las claves, conectar Alpaca a Claude Code | Tú (15 min) |
| `CLAUDE.md` | Reglas duras y convenciones del repo. Claude Code lo lee solo en cada sesión | Claude |
| `prompts/01_fable_investigacion.md` | Elegir 3–5 estrategias candidatas y fijar los criterios de aprobado **antes** de probar | **Fable** |
| `prompts/02_sonnet_motor_backtest.md` | Programar el motor de backtest, los datos, las métricas y los tests | **Sonnet** |
| `prompts/03_fable_backtest_y_veredicto.md` | Correr y auditar los backtests, pruebas de estrés y veredicto | **Fable** |
| `prompts/04_fable_manual_operacion.md` | Escribir `STRATEGY.md` (el manual) y la especificación de `signals.py` | **Fable** |
| `prompts/05_sonnet_paper_diario.md` | Programar el ejecutor diario en paper + cron/systemd | **Sonnet** |
| `prompts/06_revision_semanal.md` | Revisión semanal contra el benchmark | **Sonnet** (Fable si queda cupo) |
| `docs/estrategias.md` | Informe de 15–20 estrategias (ya en el repo) | Fable (paso 1) |
| `docs/research-mercado-nov-2026.md` | Research de mercado, Jiang, Fang y Trump | Contexto |
| `docs/VERIFICACIONES.md` | Dudas del kit contrastadas con docs oficiales (cripto, paper, permisos, oferta Fable) | Tú / Claude |
| `plantillas/.env.example`, `plantillas/.gitignore` | Para copiar al repo | Tú |

---

## Informes

Informes ya en `main` (el código del motor sigue en la rama [`prep/motor-backtest`](https://github.com/SrJorgeG/trading-lab/tree/prep/motor-backtest), sin fusionar):

| Informe | Qué es |
|---|---|
| [`docs/INFORME_MOTOR_Y_BASELINES.md`](docs/INFORME_MOTOR_Y_BASELINES.md) | Resumen en claro: qué hace el motor, tabla de referencia y las 3 decisiones para Fable |
| [`docs/baselines.md`](docs/baselines.md) | Resultados de referencia completos (CAGR, drawdown, Sharpe, costes ×2) |
| [`docs/PREP_NOTES.md`](docs/PREP_NOTES.md) | Notas técnicas del motor, limitaciones y preguntas para Fable |
| [`docs/estrategias.md`](docs/estrategias.md) | Informe de 15–20 estrategias (paso 1) |
| [`docs/research-mercado-nov-2026.md`](docs/research-mercado-nov-2026.md) | Research de mercado, Jiang, Fang y Trump (nov 2026) |
| [`docs/VERIFICACIONES.md`](docs/VERIFICACIONES.md) | Dudas del kit contrastadas con docs oficiales (cripto, paper, permisos, oferta Fable) |
| [`docs/research-llm-trading.md`](docs/research-llm-trading.md) | Qué dice la evidencia sobre LLMs operando, errores típicos de bots y encargos para Fable |
| [`docs/MONTECARLO.md`](docs/MONTECARLO.md) | Qué es una simulación de Monte Carlo, cómo leer el abanico y las corridas de referencia (Donchian, Faber, TSMOM) |

Los CSV y resúmenes de las corridas de referencia están en `reports/`. Los informes de Monte Carlo (md, csv, html, png) están en `reports/baselines/20261111-0141/<slug>/`.

---

## Instalación (5 minutos)

En jorge-cachy:

```bash
# 1) Descomprimir el kit y crear el repo
mkdir -p ~/trading-lab && cd ~/trading-lab
tar -xzf ~/Descargas/trading-lab-kit.tar.gz --strip-components=1   # ajusta la ruta del .tar.gz
cp plantillas/.gitignore .gitignore
cp plantillas/.env.example .env          # luego rellenas las claves (ver SETUP_ALPACA.md)
chmod 600 .env
git init && git add -A && git commit -m "kit inicial"   # .env queda fuera por el .gitignore

# 2) Comprobar herramientas
uv --version || sudo pacman -S uv        # uv: gestor de Python rápido (CachyOS/Arch)
claude --version
```

3) Pega el informe de estrategias en `docs/estrategias.md` (sustituye el texto de ejemplo).
4) Sigue `SETUP_ALPACA.md`.

---

## Orden de uso

Cada paso es **una sesión corta de Claude Code** que se abre en `~/trading-lab`. Para cada uno:

```bash
cd ~/trading-lab
claude                      # abre Claude Code
/model                      # elige el modelo que indica la tabla (o: claude --model fable / --model sonnet)
```

Y luego le dices: **"Lee y ejecuta `prompts/0X_....md`"**. Al acabar: revisa el resultado, `git commit`, y `/clear` (borra el contexto) antes del siguiente paso.

| Paso | Prompt | Modelo | Qué sale | Tiempo aprox. |
|---|---|---|---|---|
| 0 | `SETUP_ALPACA.md` | — (tú) | Cuenta paper + claves + MCP | 15 min |
| 1 | `01_fable_investigacion.md` | **Fable** | `docs/hipotesis.md` | 1 sesión |
| 2 | `02_sonnet_motor_backtest.md` | **Sonnet** | Repo con motor, datos, tests en verde | 1–2 sesiones |
| 3 | `03_fable_backtest_y_veredicto.md` | **Fable** | `docs/veredicto.md` + informes | 1–2 sesiones |
| 4 | `04_fable_manual_operacion.md` | **Fable** | `STRATEGY.md` + `docs/signals_spec.md` | 1 sesión |
| 5 | `05_sonnet_paper_diario.md` | **Sonnet** | `scripts/run_daily.py` + timer diario | 1 sesión |
| 6 | `06_revision_semanal.md` | **Sonnet** | `reports/semana_AAAA-SS.md` | cada semana |

**Si el paso 3 dice "ninguna estrategia pasa":** es un resultado válido (y frecuente). Vuelve al paso 1 con lo aprendido, **no** relajes los criterios para que algo "apruebe".

---

## Plan por tandas (horario de Madrid)

Datos de tu cuenta (según lo que pasó el Bot general): el límite semanal de Claude se renueva los **jueves a las 15:00**; Fable puede gastar como mucho el **50 % del límite semanal**, y lo consume más rápido que Sonnet. La otra mitad, para Sonnet.

### Tanda 1 — ahora → jueves 12 nov, 15:00
- Paso 0 (Alpaca) y paso 1 (**Fable**: hipótesis y criterios).
- Paso 2 (**Sonnet**: motor de backtest con tests). Este es el más largo, pero lo hace Sonnet, así que no gasta cupo de Fable.
- Si sobra cupo de Fable antes del jueves 15:00: empezar el paso 3 (aunque sea solo la auditoría del motor). El cupo que no gastes antes del reset **se pierde**.

### Tanda 2 — jueves 12 nov, 15:00 → lunes 17 nov, 08:59
- Paso 3 (**Fable**: backtests, estrés, walk-forward, veredicto).
- Paso 4 (**Fable**: `STRATEGY.md`, el manual que ejecutarán otros).
- Paso 5 (**Sonnet**: ejecutor diario en paper). Objetivo: que el lunes 16 ya opere en paper.
- Domingo 16: una última sesión de **Fable** para revisar el manual y el ejecutor ("busca agujeros"). Después del lunes 08:59 Fable vuelve a ir por créditos de pago.

### Tanda 3 — opcional, solo si tienes el reset extra de Fable
Oficialmente, el reset de Fable en Pro solo se da si la facturación de pago estaba activa **antes del 9 nov 2026 a las 18:00, hora de Madrid** (10:00 PT), y caduca el **lun 17 nov 08:59, hora de Madrid**. El Bot general creía que **no** lo tienes (te suscribiste después de ese corte). **Míralo en Settings → Usage** antes de contar con ello. Si lo tienes, úsalo **antes del lunes 08:59** para:
- una segunda ronda del paso 1 → 3 con las ideas que fallaron (nuevas hipótesis, no retocar las mismas hasta que "salgan"), o
- una auditoría profunda del código (look-ahead, costes, errores de órdenes).

### Después del 17
- El ejecutor diario es **Python puro**: no gasta cupo.
- Revisión semanal con **Sonnet** (paso 6).
- Dinero real: **no** hasta que lleve **como mínimo 2–3 meses en paper** comportándose como dice el backtest. Y aun así, con una cantidad que podáis perder entera.

---

## Qué modelo para qué

| Tarea | Modelo | Por qué |
|---|---|---|
| Diseñar hipótesis, fijar criterios, detectar trampas (sesgos), dar veredicto, escribir el manual | **Fable** | Requiere pensar de verdad |
| Programar el motor, tests, scripts, refactors, arreglar errores de lint | **Sonnet** | Es mecánico y Sonnet lo hace bien y barato |
| Ejecutar la estrategia cada día | **Python puro** (sin IA) | Determinista, gratis, sin "creatividad" |
| Revisión semanal | **Sonnet** | Leer números y compararlos |

Cambiar de modelo dentro de Claude Code: `/model` y eliges. Desde la terminal: `claude --model fable` o `claude --model sonnet` (son alias oficiales; `fable` resuelve a Fable 5.2). Hace falta Claude Code **v2.1.321 o posterior** para Fable 5.2 (`claude update` si no). Comprueba con `/status` qué modelo está activo antes de empezar. Detalle de la oferta Pro: `docs/VERIFICACIONES.md`.

> **Ojo:** `/model` guarda el modelo elegido como **predeterminado para las sesiones nuevas**. Si te quedas en Fable, el siguiente `claude` (o un `claude -p` del cron) también usará Fable. Por eso todos los comandos automáticos de este kit llevan `--model sonnet` explícito, y conviene volver a `/model` → Sonnet al terminar cada sesión de Fable.

---

## Consejos para no quemar el cupo de Fable

1. **Fable solo piensa, no teclea código repetitivo.** Si Fable propone un cambio grande de código, que lo deje escrito como tarea en `docs/tareas_sonnet.md` y lo haces luego con Sonnet.
2. **Sesiones cortas y con un único objetivo.** Un prompt = una sesión. Al terminar: `git commit` y `/clear`.
3. **`/clear` entre fases.** El contexto acumulado se paga en cada mensaje. Todo lo importante ya queda escrito en `docs/`.
4. **No le pegues datos enormes.** Que Fable lea resúmenes (`reports/*.md`, CSV pequeños), no 10.000 filas de velas.
5. **Lanza los cálculos pesados fuera del chat.** Los backtests los corre Python; Fable solo lee el informe que sale.
6. **Mira el consumo** con `/usage` de vez en cuando (muestra los límites del plan). Si Fable pasa del 40 % del límite semanal, cierra lo que esté haciendo y deja el resto escrito para la siguiente tanda.
7. **Si algo falla en bucle** (tests, instalación), corta, `/clear`, y pásaselo a Sonnet.

---

## Reglas que no se negocian (resumen de `CLAUDE.md`)

- Solo **paper**. Nunca el endpoint real. Nunca claves reales.
- Riesgo máx. **1 %** por operación, stop obligatorio, máx. **3** posiciones abiertas.
- Sin apalancamiento, sin cortos (vender sin tener el activo) y sin opciones.
- **Kill switch** (parada de emergencia) si la cuenta cae más de un **10 %** desde su máximo.
- **Nunca inventar resultados.** Si un número no sale de un script que se ha ejecutado, no existe.

Ni yo ni Claude somos asesores financieros. Esto es para aprender.
