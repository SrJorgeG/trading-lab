# Prompt 01 — Investigación e hipótesis (modelo: **Fable**)

> Cómo lanzarlo: `cd ~/trading-lab && claude --model fable` → escribe: *"Lee y ejecuta prompts/01_fable_investigacion.md"*.
> Duración objetivo: **una sesión**. Al acabar: `git add -A && git commit -m "paso 1: hipótesis"` y `/clear`.

---

## Tu papel
Eres el **investigador cuantitativo jefe** de este proyecto. En este paso **solo piensas y escribes**: no programas, no ejecutas backtests, no miras rentabilidades de las candidatas. Tu trabajo es elegir qué vamos a probar y **fijar por escrito, antes de ver ningún resultado, qué significa "aprobar"**. Esto se llama **pre-registro** y es nuestra principal defensa contra el **sobreajuste** (ajustar una estrategia al pasado hasta que "funciona" y luego falla en real).

## Lee primero (y nada más)
1. `CLAUDE.md` (reglas duras: solo paper, 1 % de riesgo, stop obligatorio, máx. 3 posiciones, sin apalancamiento/cortos/opciones, kill switch al −15 %).
2. `docs/estrategias.md` (informe de 15–20 estrategias). **Si todavía contiene el texto de ejemplo**, dilo al principio de tu respuesta y trabaja con tu propio conocimiento, marcándolo en `docs/hipotesis.md`.
3. Skills disponibles en `~/.claude/skills`: `backtest-expert` (cómo validar sin engañarse), `backtesting-frameworks`, `position-sizer`, `crypto-regime-analyzer`. Úsalas como referencia de método; no instales nada.

## Restricciones del problema (tenlas en cuenta al elegir)
- Broker: **Alpaca paper**. Mercados: **acciones/ETFs de EE. UU.** (solo compras) y **cripto spot** (BTC/USD, ETH/USD y como mucho otras 3 muy líquidas).
- **Baja frecuencia**: velas **diarias** (en cripto se admite 4 h si lo justificas). Ejecución automática **una vez al día** por un script de Python sin IA.
- Capital virtual: **10.000 $**. Con 1 % de riesgo y máx. 3 posiciones, las órdenes son pequeñas: comprueba que la estrategia funciona con **acciones enteras** en ETFs (sin fracciones) o explica cómo se resolvería.
- **Datos gratis:**
  - Alpaca Market Data, plan Basic: acciones desde **2016**, **200 llamadas/min**. Las barras históricas SIP (todas las bolsas) se pueden pedir siempre que el final de la consulta sea de hace más de 15 min; el feed en tiempo real gratuito es solo IEX. Cripto: barras de Alpaca (verifica desde qué fecha hay historia).
  - **yfinance** como respaldo (más historia: p. ej. SPY desde 1993, BTC-USD desde 2014), con precios ajustados.
  - Al menos **8 años** de historia para acciones y lo máximo disponible en cripto.
- **Sesgo de supervivencia** (probar solo con empresas que existen hoy): por eso, para acciones, **prioriza universos de ETFs** (SPY, QQQ, IWM, DIA, ETFs sectoriales XL*, TLT, IEF, GLD…). Si propones acciones individuales, justifica cómo controlas el sesgo.
- **Costes pesimistas de partida** (Sonnet los pondrá en `config/settings.toml`; puedes cambiarlos si lo justificas):
  - ETFs/acciones: comisión 0 $ (Alpaca no cobra comisión por acciones) + **slippage de 5 pb por lado** (1 pb = 0,01 %) en ETFs muy líquidos; 15 pb en el resto.
  - Cripto: **comisión 0,25 % por lado** (tarifa "taker" del tramo más bajo de Alpaca; **verifícala** en la web de Alpaca o con el MCP `search_alpaca_docs`) + slippage de 10 pb.
  - Escenario de estrés: **costes × 2**.

## Qué tienes que hacer
1. **Pre-selección:** de `docs/estrategias.md`, descarta en una tabla las que no encajan (alta frecuencia, necesitan cortos/opciones/apalancamiento, datos de pago, demasiado discrecionales) con una línea de motivo cada una.
2. **Elige 3–5 candidatas** que sean:
   - 100 % basadas en reglas (cualquiera que las lea calcula la misma señal),
   - de baja frecuencia, solo largos (comprar y vender lo que tienes),
   - con una **razón económica** plausible de por qué podrían funcionar (quién pierde el dinero que tú ganas, o qué prima de riesgo cobras), y si existe, evidencia publicada (cítala sin inventar referencias; si no estás seguro de una cita, no la pongas),
   - **diversas entre sí** (por ejemplo: una de tendencia, una de reversión a la media, una de rotación por momentum, una de cripto). No 4 variantes de lo mismo.
   - Ejemplos orientativos, no obligatorios: tendencia con media de 200 días o momentum 12-1 en ETFs; rotación de ETFs por fuerza relativa; reversión a corto plazo en índices (RSI de 2 periodos con filtro de tendencia); ruptura de canal de Donchian en BTC/ETH con stop por ATR.
3. **Para cada candidata, especifica con precisión matemática** (ver plantilla abajo): universo, timeframe, indicadores **con fórmula**, condiciones de entrada y salida, **stop** (precio exacto, p. ej. `entrada − 2 × ATR(14)`), cómo se ordenan las señales si hay más de 3 a la vez, frecuencia de revisión, y cuándo se ejecuta (siempre en la **apertura de la vela siguiente** a la señal). **Parámetros por defecto fijados ahora**, con su rango razonable para la prueba de robustez (±25 %).
4. **Compatibilidad con las reglas duras:** demuestra con un ejemplo numérico (equity 10.000 $) que el tamaño de posición con 1 % de riesgo da órdenes ejecutables y que nunca se superan 3 posiciones ni el 100 % de exposición.
5. **Estimación del nº de operaciones** esperado en la historia disponible (orden de magnitud y cómo lo estimas). Si una candidata dará < 100 operaciones, dilo y justifica por qué aun así merece la pena (o descártala).
6. **Benchmark** (referencia con la que comparar) para cada candidata: buy & hold (comprar y mantener) de **SPY** para acciones/ETFs y de **BTC** para cripto; si aplica, una cartera 60/40 o 50 % BTC / 50 % caja.
7. **Diseño de la validación (pre-registrado):**
   - **Partición temporal:** primer ~70 % de la historia = *in-sample* (para desarrollar); último ~30 % = *out-of-sample* (OOS, datos que no se miran hasta el final y **se usan una sola vez**). Fechas exactas.
   - **Walk-forward** (optimizar en una ventana, probar en la siguiente, avanzar): nº de ventanas (≥ 5), longitud de entrenamiento y de prueba.
   - **Presupuesto de variantes:** máximo de combinaciones de parámetros que se probarán por candidata (p. ej. ≤ 50) y la obligación de registrarlas todas en `docs/registro_pruebas.md`.
8. **Criterios de aceptación** — escríbelos como una lista de comprobación binaria (sí/no). Parte de estos mínimos; puedes **endurecerlos**, nunca suavizarlos:
   - [ ] **≥ 100 operaciones** en total (in-sample + OOS, todo el universo), o ≥ 30 en OOS con justificación escrita ahora.
   - [ ] **Expectancy** (ganancia media por operación, en múltiplos de R, donde 1R = el riesgo inicial) **> 0,10 R en OOS** con costes base.
   - [ ] **Sharpe OOS ≥ 0,5** (anualizado, tipo libre de riesgo 0) **y** al menos uno de: Sharpe ≥ el del benchmark en el mismo periodo, o **máximo drawdown ≤ 60 % del del benchmark** con CAGR (crecimiento anual compuesto) ≥ 50 % del del benchmark.
   - [ ] **Máximo drawdown** de la cartera ≤ **20 %** (ETFs) / ≤ **30 %** (cripto) en todo el periodo.
   - [ ] **Walk-forward:** ≥ 60 % de las ventanas de prueba con resultado positivo.
   - [ ] **Robustez de parámetros:** moviendo cada parámetro ±25 %, al menos el **70 %** de las combinaciones vecinas mantienen expectancy > 0 y Sharpe ≥ 50 % del central (sin "pico aislado").
   - [ ] **Costes × 2:** expectancy sigue > 0.
   - [ ] **Retraso de 1 vela** en la entrada: expectancy sigue > 0.
   - [ ] **Quitando las 5 mejores operaciones:** el resultado total sigue ≥ 0.
   - [ ] **Monte Carlo** (barajar el orden de las operaciones 1.000 veces): el percentil 95 del drawdown ≤ 1,5 × el límite de drawdown.
   - [ ] Funciona (expectancy > 0) en **al menos 2 de 3 subperiodos** y en más de un activo del universo.
   - Y una regla final: si una candidata **falla en OOS, muere**. No se reajusta y se vuelve a probar en el mismo OOS.
9. **Criterio de selección final** si pasan varias: preferir la más **simple** (menos parámetros), la de mayor robustez, y si van 2, que tengan correlación de retornos diarios < 0,5.
10. **Tareas para Sonnet:** al final de `docs/hipotesis.md`, una sección "Especificación para implementar" con, por candidata, la firma de `generate_signals`, columnas de salida y 2–3 **casos de prueba a mano** (velas pequeñas inventadas → señal esperada) para que Sonnet escriba tests unitarios.

## Entregable: `docs/hipotesis.md`
Usa exactamente esta estructura:

```markdown
# Hipótesis pre-registradas — <fecha, hora de Madrid>
Estado: PRE-REGISTRADO (no modificar criterios después de ver resultados)

## 0. Fuente
(¿se usó docs/estrategias.md o conocimiento propio?)

## 1. Descartadas
| Estrategia | Motivo |

## 2. Candidatas
### H1 — <id_corto> (p. ej. trend_sma200_etf)
- Idea en una frase:
- Razón económica / evidencia:
- Universo y timeframe:
- Datos (fuente, desde, ajustes):
- Indicadores (fórmulas):
- Entrada:
- Salida:
- Stop (fórmula exacta):
- Ranking si hay > 3 señales:
- Parámetros por defecto | rango robustez:
- Ejemplo numérico de sizing (equity 10.000 $):
- Nº de operaciones esperado:
- Benchmark:
- Riesgos conocidos / cuándo dejaría de funcionar:
(repetir H2…H5)

## 3. Diseño de validación
- Fechas in-sample / OOS:
- Walk-forward:
- Presupuesto de variantes:
- Costes base y de estrés:

## 4. Criterios de aceptación (checklist)

## 5. Criterio de selección final

## 6. Especificación para implementar (para Sonnet)
```

Crea también `docs/registro_pruebas.md` con una tabla vacía: `| fecha | hipótesis | variante/parámetros | conjunto (IS/WF/OOS) | resultado clave | archivo de informe |`.

## Criterios de "hecho"
- `docs/hipotesis.md` existe, sigue la plantilla, tiene 3–5 candidatas completas y la checklist de aceptación.
- Ninguna cifra de rentabilidad de las candidatas (no se han probado). Las únicas cifras son supuestos (costes, fechas, parámetros) y estimaciones marcadas como tales.
- `docs/registro_pruebas.md` creado.

## Condiciones de parada
- **No escribas código** ni ejecutes backtests. Si te ves tentado, anótalo en `docs/tareas_sonnet.md`.
- **No descargues datos** salvo una comprobación mínima de disponibilidad (p. ej. con el MCP de Alpaca, la fecha de la primera barra diaria de BTC/USD y SPY). No calcules rentabilidades.
- Si `CLAUDE.md` no existe o las reglas duras te impiden diseñar algo razonable, **para** y explícalo.
- Al terminar, responde con un resumen de 10 líneas: candidatas elegidas, por qué, y qué debe hacer ahora Sonnet (paso 2).
