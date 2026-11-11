# Verificaciones oficiales (11 nov 2026, hora de Madrid)

Respuestas contrastadas con documentación oficial (y, donde hace falta, con la API en vivo) a las dudas que el kit dejaba abiertas. Lo que hay que cambiar en el kit está al final de cada apartado y en el resumen.

---

## 1. Cripto en Alpaca desde España (paper y live)

### Paper

**Sí, en principio se puede operar cripto en paper.** La documentación oficial de Paper Trading dice dos cosas a la vez:

- «Paper trading simulates crypto trading as well.»
- «Anyone globally can create an Alpaca Paper Only Account! All you need to do is sign up with your email address.»

El ejemplo oficial de orden cripto usa precisamente el endpoint paper (`https://paper-api.alpaca.markets/v2/orders` con `BTC/USD`). Jorge ya tiene la cuenta paper en [app.alpaca.markets](https://app.alpaca.markets) (plataforma de EE. UU., no Alpaca Europe). Mañana conviene una prueba de humo: una orden paper minúscula de `BTC/USD` (o listar `GET /v2/assets?asset_class=crypto` y comprobar `tradable: true`). Si esa orden se rechaza por jurisdicción, pasar al plan B.

### Live (más adelante)

**No está confirmado que un residente en España pueda operar cripto en una cuenta real de Alpaca.** La doc de Crypto Spot Trading dice, desde el 18 nov 2022, que el trading de cripto está abierto a «select international jurisdictions and some U.S. jurisdictions». El artículo de soporte lista estados de EE. UU. y habla de «eligible international participants», pero **no publica una lista de países**. En el foro, un empleado de Alpaca indica que si en la cuenta *live* no aparece la opción de activar cripto, suele ser porque la jurisdicción no está soportada.

Otras piezas que no hay que mezclar:

- **Abrir una cuenta live de acciones/ETFs desde España sí parece posible.** Alpaca dice apoyar servicios en 195+ países; en la guía para no residentes cita explícitamente a un residente fiscal en Portugal. Canadá, por ejemplo, no está soportado. La lista exacta la confirma el propio onboarding o `support@alpaca.markets`.
- **Alpaca Europe no ofrece cripto.** Alpaca Europe A.V., SLU (sede en España, autorizada por la CNMV, pasaporte MiFID II en el EEE) da infra de broker para **acciones y ETFs de EE. UU.**, sobre todo B2B. En su propia doc: «We currently support trading of whole and fractional shares for stocks and ETFs listed on US public exchanges.» Cripto no está en el producto ni en el roadmap que publican (opciones, renta fija, renta variable europea, wrappers fiscales). El pasaporte EEE de julio 2026 es de servicios de inversión regulados (MiFID II), no un alta como CASP bajo MiCA.
- La cuenta de Jorge en `app.alpaca.markets` es la plataforma de **Alpaca Securities / Alpaca Crypto (EE. UU.)**, no el producto de Alpaca Europe.

Conclusión para el lab: **el experimento de cripto se hace en paper**. El live de cripto, si algún día se plantea, hay que comprobarlo en Account → Configure → Enable crypto trading (o con soporte) antes de contar con ello. Acciones/ETFs live son otro asunto y parecen más realistas, pero eso queda fuera de esta fase.

### Pares disponibles

La lista canónica es la API: `GET https://api.alpaca.markets/v2/assets?asset_class=crypto` (con las claves paper también vale; en paper el host de trading es `paper-api.alpaca.markets`). La doc de trading habla de «20+ unique crypto assets across 56 trading pairs» (USD, USDT, USDC y BTC), cifra que puede estar desfasada.

El artículo de soporte **[What cryptocurrencies does Alpaca currently support?](https://alpaca.markets/support/what-cryptocurrencies-does-alpaca-currently-support)** (marzo 2026) lista estos pares (una X = par activo). Para el lab, priorizar pares `*/USD` (`BTC/USD`, `ETH/USD`, `SOL/USD`, …):

| Activo | USD | USDC | USDT | BTC |
|---|:---:|:---:|:---:|:---:|
| AAVE | X | X | X | |
| ADA | X | | | |
| ARB | X | | | |
| AVAX | X | X | X | |
| BAT | X | X | | |
| BCH | X | X | X | X |
| BONK | X | | | |
| BTC | X | X | X | |
| CRV | X | X | | |
| DOGE | X | X | X | |
| DOT | X | X | | |
| ETH | X | X | X | X |
| FIL | X | | | |
| GRT | X | X | | |
| HYPE | X | | | |
| LDO | X | | | |
| LINK | X | X | X | X |
| LTC | X | X | X | X |
| ONDO | X | | | |
| PAXG | X | | | |
| PEPE | X | | | |
| POL | X | | | |
| RENDER | X | | | |
| SHIB | X | X | X | |
| SKY | X | | | |
| SOL | X | X | X | |
| SUSHI | X | X | X | |
| TRUMP | X | | | |
| UNI | X | X | X | X |
| USDC | X | | | |
| USDG | X | | | |
| USDT | X | X | | |
| WIF | X | | | |
| XRP | X | | | |
| XTZ | X | X | | |
| YFI | X | X | X | |

Notas de la misma doc de trading: cripto **no** se compra con margen, **no** se puede vender en corto, horario 24/7, órdenes `market` / `limit` / `stop_limit` con `time_in_force` `gtc` o `ioc`, comisión por tramos (en el tramo más bajo: 15 bps maker / 25 bps taker).

### Plan B si paper cripto no está disponible

1. **Preferido: Demo Trading de Bybit EU.** Desde España la entidad regulada (MiCA) es [Bybit EU](https://www.bybit.eu/). Tiene cuenta demo con fondos simulados y API (`https://api-demo.bybit.com` en la doc global; en la UE puede aplicar el host `.eu`). No es lo mismo que el *testnet* de desarrollo. Hay que crear la API key **dentro** del modo Demo, no mezclarla con la de producción ni con la de testnet.
2. **Alternativa: Binance Spot Testnet**, [testnet.binance.vision](https://testnet.binance.vision/) (doc: [general-info del Spot Test Network](https://developers.binance.com/docs/binance-spot-api-docs/testnet/general-info)). Es un entorno de prueba de la API Spot, con fondos virtuales, pensado para desarrolladores. El endpoint de ping `https://testnet.binance.vision/api/v3/ping` respondió 200 desde este entorno el 11 nov 2026. Binance tiene entidad registrada en España para el exchange real; el testnet es independiente. Un 451 en alguna petición suele ser geobloqueo por IP del servidor, no de la cuenta: si Jorge lo abre desde su PC en España y carga, vale. Solo expone endpoints `/api` (no `/sapi`).

Para este lab, el plan B solo hace falta si la prueba de humo en Alpaca paper falla. Mientras Alpaca paper acepte cripto, nos quedamos ahí (mismo broker que las acciones, mismas reglas del kit).

### Fuentes

- [Paper Trading](https://docs.alpaca.markets/us/docs/paper-trading)
- [Crypto Spot Trading](https://docs.alpaca.markets/us/docs/crypto-trading)
- [Does Alpaca support cryptocurrency?](https://alpaca.markets/support/alpaca-cryptocurrency) (may 2023; lista de estados de EE. UU.)
- [What cryptocurrencies does Alpaca currently support?](https://alpaca.markets/support/what-cryptocurrencies-does-alpaca-currently-support) (marzo 2026)
- [About Alpaca Europe](https://docs.alpaca.markets/eu/docs/about-alpaca)
- [How to Open a Live Trading Account as a Non-US Resident](https://alpaca.markets/learn/live-trading-account-non-us) (actualizado 11 mar 2026)
- [Is crypto trading available? (foro, Dan Whitnable, Alpaca)](https://forum.alpaca.markets/t/is-crypto-trading-available/13707)
- [Bybit Demo Trading API](https://bybit-exchange.github.io/docs/v5/demo)
- [Binance Spot Test Network](https://testnet.binance.vision/)

### Qué cambiar en el kit

- `SETUP_ALPACA.md`: actualizar la nota de cripto (ya no es un «si te bloquea, ya veremos»). Apuntar a este documento y a la prueba de humo.
- No hace falta cambiar el plan A (Alpaca paper) mientras la prueba salga bien.

---

## 2. ¿Se puede reiniciar el paper y poner 10.000 $ de saldo?

**Sí, con un saldo inicial a medida, pero ya no hay botón de Reset.** La doc oficial aún dice que la cuenta inicial nace con 100.000 $ y que «you can reset the paper trading account at any time later with arbitrary amount», pero justo debajo aclara el cambio de interfaz:

> We've updated the dashboard to allow you to create and delete paper accounts, rather than resetting them.

Cómo hacerlo hoy:

1. En el dashboard, pulsa el número de la cuenta paper (arriba a la izquierda) → **Open New Paper Account**.
2. Pon nombre y **capital inicial** (p. ej. 10.000 $).
3. **Genera claves API nuevas** para esa cuenta. Las anteriores no valen.
4. Opcional: borra la cuenta vieja en Account Settings → Delete Account.
5. Puedes tener **hasta 3** cuentas paper a la vez (dato de una guía práctica de ago 2026 que describe la misma UI; la doc oficial confirma crear/borrar, no el tope).
6. **No se puede cambiar el saldo de una cuenta ya creada.** Si quieres otro capital, creas otra cuenta (o, en el kit, usas el capital virtual de `config/settings.toml`).

El FAQ de market data sigue diciendo «when you reset your paper account, you need to regenerate your credentials»: la idea (claves nuevas) sigue siendo cierta, aunque la UI ya no se llame Reset.

### Fuentes

- [Paper Trading — Reset Your Paper Trading Account](https://docs.alpaca.markets/us/docs/paper-trading)
- [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) (regenerar claves tras un reset)
- [Paper trading balance (foro, empleado de Alpaca, oct 2025)](https://forum.alpaca.markets/t/paper-trading-balance/17970): el equity no se cambia; hay que crear una cuenta nueva.

### Qué cambiar en el kit

- `SETUP_ALPACA.md` §2 estaba **desfasado** (hablaba de Reset / Reset Account). Corregido en este commit.

---

## 3. Zona horaria de las velas diarias de cripto en Alpaca

**Las velas `1Day` de cripto del API actual empiezan a las 00:00:00 UTC.** El campo `t` es el inicio de la barra; cubre `[00:00 UTC, 00:00 UTC del día siguiente)`.

Comprobado el 11 nov 2026 contra `GET https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols=BTC/USD&timeframe=1Day` (no hace falta clave) en varios periodos, incluidos cambios de horario de EE. UU.:

- sep 2022, ene 2023, jul 2025, marzo 2026 (cambio a DST el día 8), oct–nov 2026 (fin de DST el 1 nov) y días recientes: **todas** las barras llevan `t=…T00:00:00Z`.
- Los OHLC de sep 2022 coinciden con el ejemplo en C# de la guía oficial (`2022-09-01T00:00:00Z`, open 20051.81, close 20132.97).

Cuidado con documentación vieja o de **acciones**:

- La guía [Getting Started with Market Data](https://docs.alpaca.markets/us/docs/getting-started-with-alpaca-market-data) todavía muestra, en los ejemplos de Python/Go/JS, barras de BTC de sep 2022 a las **05:00 UTC**. Esos números **ya no salen** en el API v1beta3 (el ejemplo en C# de la misma página sí usa 00:00 UTC y coincide con el API).
- El FAQ «How are bars aggregated?» habla de truncar al día **en Nueva York**. Eso aplica a **acciones**: una vela diaria de AAPL el 29 sep 2023 (horario de verano en EE. UU.) sale a `2023-09-29T04:00:00Z` = medianoche ET. Un post del foro de un empleado de Alpaca (ene 2023) explica lo mismo para velas de un valor a ~11 $, no cripto.
- No hay que usar medianoche ET para cripto. El ejecutor cripto a las **00:15 UTC** del kit es el correcto: 15 minutos después de que cierre la vela UTC.

Recomendación para el motor: preferir las barras nativas `timeframe=1Day` de Alpaca (ya son días UTC). Remuestrear velas de 1 h a días UTC debería dar el mismo recorte; si se usa otra definición, backtest y paper se desalinean.

### Fuentes

- Consulta directa al API v1beta3, 11 nov 2026 (hora de Madrid)
- [Getting Started with Market Data API](https://docs.alpaca.markets/us/docs/getting-started-with-alpaca-market-data) (ejemplos; el de C# está al día, Python/Go/JS no)
- [Historical crypto bars](https://docs.alpaca.markets/us/reference/cryptobars-1)
- [Market Data FAQ — How are bars aggregated?](https://docs.alpaca.markets/us/docs/market-data-faq) (velas de **acciones**, día de Nueva York)
- [Why is day candles only at 5pm utc? (foro; velas de acciones)](https://forum.alpaca.markets/t/why-is-day-candles-only-at-5pm-utc/11580)

### Qué cambiar en el kit

- `prompts/05_sonnet_paper_diario.md` y `CLAUDE.md`: dejar explícito que las `1Day` de cripto son medianoche UTC (para que nadie las «corrija» a ET por los ejemplos viejos). El horario 00:15 UTC ya era el adecuado.

---

## 4. Sintaxis de permisos en Claude Code (editar una carpeta y herramientas MCP)

Documentación vigente: [Configure permissions](https://code.claude.com/docs/en/permissions) (el mismo contenido está en [docs.claude.com](https://docs.claude.com/en/docs/claude-code/permissions)). Aplica a Claude Code 2.1.x.

### Editar solo una subcarpeta

Las reglas `Read` / `Edit` usan patrones tipo gitignore. `path` y `./path` son lo mismo: relativos al **directorio de trabajo actual**.

| Regla (en `allow`) | Efecto si lanzas `claude` en la raíz del repo |
|---|---|
| `Edit(./journal/**)` | Permite editar `journal/` y su contenido. **Válida.** Es la forma que ya usa el kit. |
| `Edit(journal/**)` | **Equivalente** a la anterior como regla `allow`: solo `<cwd>/journal/**`, no un `journal/` anidado en otro sitio. |
| `Edit(/journal/**)` | Ancla en el origen de la configuración. En flags CLI / reglas de sesión / settings del proyecto, es `<cwd>/journal/**` si arrancas en la raíz. También vale, pero `./journal/**` es más claro. |
| `Edit(**/journal/**)` | Cualquier carpeta llamada `journal` a cualquier profundidad. Más amplio de lo que queremos. |

Como regla `allow`, un patrón de un solo segmento (`journal/**`) **no** coincide con `vendor/pkg/journal/…`. Como regla `deny` o `ask`, sí buscaría un `journal/` a cualquier profundidad. Para el cron del kit (`--allowedTools`, modo `dontAsk`) usamos `allow`, así que `Edit(./journal/**)` y `Edit(journal/**)` sirven igual.

No uses `Write(journal/**)`: las rutas se comprueban contra `Edit(path)` y `Read(path)`. Una regla `Write(…)` con ruta no coincide.

### Herramientas MCP

Formato: `mcp__<servidor>` o `mcp__<servidor>__<herramienta>`. Ejemplos oficiales con el servidor `puppeteer`:

- `mcp__puppeteer` — cualquier herramienta de ese servidor
- `mcp__puppeteer__*` — lo mismo, con comodín (esta es la forma que hay que usar en reglas `allow` con glob)
- `mcp__puppeteer__puppeteer_navigate` — una herramienta concreta

Para el servidor del kit, que se registra como `alpaca`:

- `mcp__alpaca` o `mcp__alpaca__*` — todas las herramientas del MCP de Alpaca
- `mcp__alpaca__<nombre_exacto>` — una sola (el nombre es el que aparece en las herramientas del servidor)

Reglas importantes:

- Las reglas `allow` de MCP **van sin paréntesis** (sin `ruleContent`). Si en un `settings.json` pones una regla `mcp__…(…)` , Claude Code **la ignora**.
- Un `allow` con glob solo se acepta después del prefijo literal `mcp__` y el nombre del servidor, p. ej. `mcp__alpaca__*`. Un `mcp__*` suelto en `allow` se descarta.
- En el paso 5 el kit usa `--strict-mcp-config` **sin** `--mcp-config`, así que esa sesión de nota diaria **no carga MCP**. No hace falta añadir reglas `mcp__` ahí. Si algún día se quiere dejar a Claude consultar la cuenta en modo lectura, se añadiría por ejemplo `mcp__alpaca__*` (o las herramientas concretas de cuenta/datos) en `--allowedTools`, nunca las de trading.

### Fuentes

- [Configure permissions (code.claude.com)](https://code.claude.com/docs/en/permissions)
- [Configure permissions (docs.claude.com)](https://docs.claude.com/en/docs/claude-code/permissions)

### Qué cambiar en el kit

- Nada de sintaxis: `Edit(./journal/**)`, `Edit(./reports/**)` y `Edit(./docs/tareas_sonnet.md)` en los prompts 05 y 06 son correctos.

---

## 5. Oferta de lanzamiento de Claude Fable 5.2 (plan Pro) y alias en Claude Code

Fuente: [Claude Fable 5.2 launch offers](https://support.claude.com/en/articles/17506494-claude-fable-5-2-launch-offers) (artículo actualizado el 10 nov 2026). Alias: [Model configuration](https://code.claude.com/docs/en/model-config).

### Qué incluye Pro

- **Todos los modelos Fable** (5.2, 5.1 y 5) entran en los límites semanales del plan **durante una semana**: del lanzamiento el **9 nov 2026** hasta el **16 nov 2026 a las 23:59 PT**.
- PT en esas fechas es PST (UTC−8), así que el cierre es el **lunes 17 nov 2026 a las 08:59, hora de Madrid**. El `README.md` ya usaba esa hora: correcto.
- Durante esa semana puedes gastar **como máximo el 50 % del límite semanal** en modelos Fable, sin coste extra. Fable consume el límite más rápido que otros modelos.
- Cuando agotas ese 50 %, o cuando acaba la semana, Fable **pasa a créditos de uso** si los tienes activados. La parte del 50 % que no uses **no se acumula**.
- El modelo por defecto **no cambia**: hay que elegir Fable a mano (`/model` o `--model`).

### Reset de Fable

- En Pro (y asientos standard de Team) hay **un** reset de límite de Fable, **solo si** la facturación de pago estaba activa **antes del 9 nov 2026 a las 10:00 PT** = **9 nov 2026 a las 18:00, hora de Madrid**.
- Si la suscripción empezó antes pero seguía en prueba gratis, el reset llega cuando pasa a pago. Si te suscribiste **después** de ese corte, **no** hay reset (coherente con lo que apuntaba el Bot general; hay que mirarlo en Settings → Usage).
- El reset de Pro **caduca en el mismo instante** que la semana incluida: 16 nov 2026 23:59 PT = 17 nov 2026 08:59, hora de Madrid.
- Qué hace el reset: devuelve el uso gastado en modelos Fable del límite semanal (el uso de otros modelos se queda). Si hay límite de 5 horas, lo rellena entero. **No sube** los techos; el tope del 50 % en Fable sigue ahí.
- Se lanza en Settings → Usage → «Reset for free». Se puede usar antes de llegar al límite; una vez usado, no se deshace.

Elegibles: Pro, Max, Ultra, asientos standard y premium de Team, y asientos premium de Enterprise antiguo por asientos. **No** entra: Free, asientos standard de ese Enterprise antiguo, Enterprise self-serve ni Enterprise por uso.

### Alias en Claude Code

- `claude --model fable` o, dentro de la sesión, `/model fable`. Es el alias oficial.
- El alias `fable` resuelve a **Fable 5.2** en casi todas partes. En sesiones *Claude apps gateway* resuelve a Fable 5, y ahí hay que pedir `claude-fable-5-2` explícito.
- ID completo: `claude-fable-5-2`.
- **Hace falta Claude Code v2.1.321 o posterior** para Fable 5.2. Si la versión es más vieja: `claude update`.
- `/model` guarda el elegido como predeterminado de las sesiones nuevas. Por eso los comandos automáticos del kit llevan `--model sonnet` explícito.

### Fuentes

- [Claude Fable 5.2 launch offers](https://support.claude.com/en/articles/17506494-claude-fable-5-2-launch-offers)
- [Model configuration](https://code.claude.com/docs/en/model-config)

### Qué cambiar en el kit

- Fechas, tope del 50 % y alias `fable` del `README.md` ya eran correctos. Se añade la versión mínima de Claude Code (2.1.321) y el corte oficial del reset (9 nov 2026, 18:00 hora de Madrid).

---

## Resumen de parches aplicados en este commit

| Archivo | Cambio |
|---|---|
| `docs/VERIFICACIONES.md` | Este documento (nuevo). |
| `SETUP_ALPACA.md` | UI actual para crear una cuenta paper con 10.000 $ (ya no hay Reset); nota de cripto actualizada. |
| `CLAUDE.md` | Velas diarias de cripto = 00:00 UTC. |
| `prompts/05_sonnet_paper_diario.md` | Deja claro que las `1Day` nativas de Alpaca ya son días UTC. |
| `README.md` | Enlace a este documento; Claude Code ≥ 2.1.321; corte del reset de Fable. |
