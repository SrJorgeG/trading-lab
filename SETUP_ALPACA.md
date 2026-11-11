# SETUP_ALPACA.md — cuenta paper + claves + conexión con Claude Code

Tiempo: unos 15 minutos. Todo esto lo haces **tú** (crear cuentas y manejar claves no se lo dejamos a la IA).

**Paper trading** = operar con dinero ficticio contra precios reales. **API key** = usuario + contraseña para que un programa use tu cuenta. **MCP** (Model Context Protocol) = conector que deja a Claude usar una herramienta externa, aquí Alpaca.

---

## 1. Crear la cuenta en Alpaca

1. Entra en <https://alpaca.markets> → **Sign up**.
2. Email: **sr.g.jorge26@gmail.com** (no uses otro). Contraseña: la que guardes en tu gestor de contraseñas.
3. Verifica el email (te llega un enlace).
4. Para **paper** no hace falta verificar identidad ni meter dinero. Si en algún momento te pide DNI, datos bancarios o fondear la cuenta, **para**: eso es para la cuenta real y no la necesitamos.

> Nota: Alpaca es un broker de EE. UU. La cuenta paper suele estar disponible para residentes fuera de EE. UU. Si al registrarte desde España te bloquea algo (sobre todo con cripto), apúntalo y avísame; hay alternativas (por ejemplo, la testnet de Binance o Bybit para cripto).

## 2. (Recomendado) Poner un saldo paper realista

La cuenta paper empieza con unos 100.000 $ ficticios. Con eso todo parece fácil. Para que el experimento se parezca a vuestra realidad:

1. En el panel (<https://app.alpaca.markets>), arriba a la izquierda, asegúrate de estar en la cuenta **Paper** (no "Live").
2. Busca la opción de **reiniciar la cuenta paper** (Reset / "Reset Account") y pon un saldo de **10.000 $**. Si no te deja elegir saldo, déjalo en 100.000 $ y nuestro código usará un capital "virtual" de 10.000 $ (está previsto en `config/settings.toml`).
3. **Importante:** si reinicias la cuenta paper, después tienes que **volver a generar las claves** (las anteriores dejan de valer).

## 3. Sacar las claves API de paper

1. Con la cuenta **Paper** seleccionada, en la página de inicio verás el recuadro **API Keys** → **Generate New Keys** (o "Regenerate").
2. Te enseña dos cosas:
   - **API Key ID** (en paper suele empezar por `PK`).
   - **Secret Key**: **solo se muestra una vez.** Cópiala ya.
3. El endpoint de paper es `https://paper-api.alpaca.markets`. Si alguna vez ves `https://api.alpaca.markets` (sin "paper"), eso es la cuenta **real**: no lo uses.

## 4. Guardar las claves en `~/trading-lab/.env` (nunca en git)

```bash
cd ~/trading-lab
cp plantillas/.env.example .env      # si no lo hiciste ya
chmod 600 .env                        # solo tu usuario puede leerlo
nano .env                             # pega las dos claves
git check-ignore .env && echo "OK: .env está ignorado por git"
```

Contenido de `.env` (los nombres de las variables son los mismos que usa el servidor MCP oficial de Alpaca):

```dotenv
ALPACA_API_KEY=PKxxxxxxxxxxxxxxxx
ALPACA_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ALPACA_PAPER_TRADE=true
```

Si `git check-ignore` no imprime nada, **para** y revisa el `.gitignore` antes de hacer ningún commit.

## 5. Comprobar las claves con Python (sin IA)

```bash
cd ~/trading-lab
set -a; source .env; set +a
uv run --with alpaca-py python - <<'PY'
import os
from alpaca.trading.client import TradingClient
c = TradingClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"], paper=True)
a = c.get_account()
print("Estado:", a.status, "| Equity:", a.equity, "| Moneda:", a.currency)
PY
```

Debe imprimir `ACTIVE` y el saldo paper. Si da error 401/403: claves mal copiadas o generadas antes de un reset.

## 6. Conectar Alpaca a Claude Code (servidor MCP oficial)

Requisitos: `uv`/`uvx` instalado (`uv --version`). El servidor es `alpaca-mcp-server` v2 (<https://github.com/alpacahq/alpaca-mcp-server>). En v2 la configuración va **solo** en variables de entorno del cliente (no hay `init` ni `.env` propio del servidor).

### Opción A (recomendada): Claude puede **mirar** pero **no operar**

La operativa la hará nuestro script de Python (determinista y con las reglas duras dentro). A Claude le damos solo herramientas de lectura. `ALPACA_TOOLSETS` limita qué herramientas expone el servidor; dejamos fuera `trading` (órdenes y posiciones), `options-data` y `locates`.

```bash
cd ~/trading-lab
set -a; source .env; set +a          # carga las claves en la terminal sin escribirlas a mano

claude mcp add alpaca --scope local --transport stdio \
  --env ALPACA_API_KEY="$ALPACA_API_KEY" \
  --env ALPACA_SECRET_KEY="$ALPACA_SECRET_KEY" \
  --env ALPACA_PAPER_TRADE=true \
  --env ALPACA_TOOLSETS=account,assets,stock-data,crypto-data,news \
  -- uvx alpaca-mcp-server
```

- `--scope local`: el conector solo existe cuando abres Claude Code dentro de `~/trading-lab`.
- `--` separa las opciones de Claude de la orden que arranca el servidor (`uvx alpaca-mcp-server`).
- `ALPACA_PAPER_TRADE=true` ya es el valor por defecto, pero lo dejamos escrito a propósito.

### Opción B: Claude también puede operar en paper

Solo si quieres que Claude coloque órdenes él mismo (por ejemplo, para probar a mano). Es igual, pero con `trading` en la lista:

```bash
claude mcp remove alpaca --scope local    # si ya tenías la opción A
claude mcp add alpaca --scope local --transport stdio \
  --env ALPACA_API_KEY="$ALPACA_API_KEY" \
  --env ALPACA_SECRET_KEY="$ALPACA_SECRET_KEY" \
  --env ALPACA_PAPER_TRADE=true \
  --env ALPACA_TOOLSETS=account,trading,assets,stock-data,crypto-data,news \
  -- uvx alpaca-mcp-server
```

**Nunca** pongas `ALPACA_PAPER_TRADE=false` ni claves de una cuenta real.

### Seguridad de las claves

`claude mcp add` guarda la configuración (claves incluidas) en `~/.claude.json`, en texto plano. Asegúrate de que solo tú puedes leerlo:

```bash
chmod 600 ~/.claude.json
```

No subas `~/.claude.json` a ningún sitio.

### Comprobar la conexión

```bash
claude mcp list            # debe salir "alpaca" con ✔ Connected
claude mcp get alpaca
```

Dentro de Claude Code (en `~/trading-lab`): `/mcp` → `alpaca` debe estar conectado. Prueba de humo: *"Usa el MCP de Alpaca para decirme el estado y el equity de mi cuenta paper. No hagas nada más."*

Si falla: reinicia Claude Code, comprueba `uvx --version` y que las claves funcionan con el paso 5.

## 7. Checklist final

- [ ] Cuenta Alpaca creada con sr.g.jorge26@gmail.com, cuenta **Paper** seleccionada
- [ ] Claves de **paper** en `~/trading-lab/.env`, `chmod 600`, ignorado por git
- [ ] El script del paso 5 imprime `ACTIVE`
- [ ] `claude mcp list` muestra `alpaca` conectado (opción A)
- [ ] `chmod 600 ~/.claude.json`

Con esto ya puedes ir al paso 1 del `README.md`.
