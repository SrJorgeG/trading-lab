# trading-lab

Laboratorio educativo de **estrategias de trading basadas en reglas escritas**: backtest riguroso y, cuando toque, ejecución en **paper trading** en [Alpaca](https://alpaca.markets/). **Solo paper. Nunca dinero real.**

Python 3.12 (`uv`, pandas, numpy, vectorbt y un simulador propio). El trabajo es conjunto con un amigo. El proyecto está **en pausa desde el 2026-11-12**: la ronda 1 cerró sin candidatas aptas; la ronda 2 está implementada en código, **sin backtests ejecutados** con datos reales, y no se opera en paper.

> **No es asesoramiento financiero.** Un backtest no garantiza resultados futuros. Una semana —ni un año— de paper trading demuestra poco. Nada de esto es una recomendación de inversión.

---

## Metodología

Antes de mirar ningún resultado se **pre-registra** la hipótesis: qué se prueba, con qué parámetros, qué significa «aprobar» y qué tramo de datos queda reservado. Después no se cambia (solo enmiendas fechadas *antes* de ver nada).

- **IS / walk-forward / OOS de un solo uso.** En ETFs, el tramo de desarrollo (IS) es 2007-07 → 2020-12; el examen final (OOS) es 2021-01 → 2026-10 y se mira **una sola vez**. El walk-forward repite «elige en el pasado, prueba el año siguiente» dentro del IS. Un candado en el código impide repetir un tramo reservado con los mismos parámetros, y se niega a lanzarlo si hay cambios sin commitear.
- **Costes siempre activados** (comisión + slippage). También se prueba todo × 2 y con un día de retraso.
- **Monte Carlo contra entradas al azar («monos»):** miles de estrategias que entran al azar con las mismas salidas, stops, tamaños y costes. Si la idea real no queda claramente por encima, su ventaja puede ser suerte.
- Otras pruebas: parámetros vecinos, quitar las 5 mejores operaciones, quitar el mejor activo, subperiodos.
- **CI** en GitHub Actions: `ruff` + `pytest` **sin red** (los tests de red van con `@pytest.mark.network` y no corren por defecto).

Las reglas duras están en [`CLAUDE.md`](CLAUDE.md): riesgo máx. 1 % por operación, stop obligatorio, máx. 3 posiciones, sin apalancamiento, sin cortos y sin opciones, kill switch si la cuenta cae un **15 %** desde su máximo (era 10 % en la ronda 1). **Nunca inventar cifras:** si un número no sale de un script ejecutado, no existe.

---

## Ronda 1 (cerrada, 2026-11-11)

Ninguna de las 4 candidatas pre-registradas aprobó. **No se opera nada con ellas.** El motor de backtest pasó una auditoría 7/7 (`docs/veredicto.md`). Cifras tomadas de los informes en `reports/`.

| Hipótesis | Idea | Veredicto |
|---|---|---|
| **H1** `donchian_crypto` | Ruptura de 55 días en BTC/ETH/LTC/BCH | Rechazada en IS: la caída superaba el kill switch del 10 % incluso arriesgando el 0,5 % |
| **H2** `tsmom_etf` | Momentum a 12 meses en 7 ETFs | Rechazada en IS: no se distinguía del azar (**p = 0,597**) |
| **H3** `rsi2_etf` | RSI(2) con tendencia SMA200 | Rechazada en IS: expectancy casi nula; negativa con costes × 2 y con un día de retraso |
| **H4** `donchian_etf` | Ruptura de 55 días en 7 ETFs | Rechazada en el OOS (el único que se gastó) |

**H4** fue la mejor: pasó **13 de 14** criterios. En el OOS (2021-01 → 2026-10, riesgo 0,5 %), [el informe](reports/donchian_etf/oos_20261111-1636/resumen.md) da:

| Métrica (OOS) | H4 | SPY (comprar y mantener) |
|---|---|---|
| CAGR | **3,45 %** | 14,65 % |
| Máx. drawdown | **7,04 %** | 24,50 % |
| Sharpe | 0,62 | 0,91 |

Suspendió el criterio 3 (rentabilidad frente a SPY) y, por regla, quedó rechazada: no se retoca después de ver el examen.

Baselines previos al veredicto (referencia, no son el veredicto): Donchian sin kill switch, contra 1.000 estrategias al azar, **p = 0,034**. TSMOM SPY: **p = 0,33** (indistinguible). Detalle en [`docs/ROBUSTEZ.md`](docs/ROBUSTEZ.md) y [`docs/registro_pruebas.md`](docs/registro_pruebas.md).

Para la ronda 2, el objetivo pasó a un «punto medio» entre caída y rentabilidad (ya no se exige batir a SPY en CAGR) y el kill switch subió de −10 % a −15 %.

---

## Ronda 2 (implementada, sin backtests; en pausa)

Hipótesis pre-registradas en [`docs/hipotesis_ronda2.md`](docs/hipotesis_ronda2.md):

- **H5** `sector_mom`: una vez al mes, los 3 sectores de EE. UU. que más han subido en 6 meses (9 Select Sector SPDR), solo si han subido.
- **H6** `tom_etf`: estar en bolsa solo alrededor del cambio de mes. **Aparcada** (no se implementa ni se ejecuta en esta ronda).
- **H7** `sector_lowvol`: el mismo esqueleto que H5, eligiendo los 3 sectores más tranquilos.

El 2026-11-12 se fijaron las decisiones P7–P16 ([`docs/decisiones_ronda2.md`](docs/decisiones_ronda2.md)) *antes* de cualquier IS: efectivo parado al 0 %, paper 12 meses, cripto fuera, riesgo calibrado a caída IS ≤ 12 %, caja = letras a 3 meses + 2 pp, máx. 60 variantes (solo H5 y H7), la ronda 2 es la última de backtest salvo decisión posterior, cuenta paper a margen 1× sin cortos ni opciones, y candado de un solo uso por tramo.

La [PR #2](https://github.com/SrJorgeG/trading-lab/pull/2) fusionó esa implementación a `main`. CI en verde: **322 tests pasados**, 3 deseleccionados (red). **No se ha ejecutado ningún backtest de H5/H7 con datos reales.** Siguen pendientes la descarga y verificación de datos (R2-3, R2-18) y, al retomar, revisar el criterio 14: en un test de potencia sintético no aprueba en el 0 % de las series, ni siquiera con ventaja conocida (`reports/potencia/potencia.md`).

---

## Estructura

```
README.md, CLAUDE.md, SETUP_ALPACA.md
config/                   # settings.toml y una ficha TOML por estrategia
src/tlab/                 # motor: datos, simulador, métricas, riesgo, broker paper
scripts/                  # backtest, datos, Monte Carlo, robustez, visor
tests/                    # pytest; por defecto sin red
docs/                     # hipótesis, veredictos, especificaciones, informes
reports/                  # informes de la ronda 1 y potencia sintética; sin IS de H5/H7
prompts/                  # sesiones originales del flujo de trabajo (investigación → paper)
plantillas/.env.example   # plantilla de claves paper (nunca subir un .env)
```

Documentos de partida:

| Documento | Qué es |
|---|---|
| [`docs/veredicto.md`](docs/veredicto.md) | Veredicto de la ronda 1 (H1–H4) y auditoría del motor |
| [`docs/informe_estudio.md`](docs/informe_estudio.md) | Revisión independiente (2026-11-12) |
| [`docs/decisiones_ronda2.md`](docs/decisiones_ronda2.md) | Decisiones P7–P16, antes de cualquier IS |
| [`docs/hipotesis.md`](docs/hipotesis.md) / [`docs/hipotesis_ronda2.md`](docs/hipotesis_ronda2.md) | Pre-registro de cada ronda |
| [`docs/INFORME_RONDA2_IMPL.md`](docs/INFORME_RONDA2_IMPL.md) | Qué se implementó en la PR #2 y qué no |
| [`docs/MONTECARLO.md`](docs/MONTECARLO.md) | Cómo leer una simulación de Monte Carlo |
| [`docs/ROBUSTEZ.md`](docs/ROBUSTEZ.md) | Mapa de parámetros (DSR/PBO) y prueba contra el azar |
| [`docs/baselines.md`](docs/baselines.md) | Corridas de referencia (Donchian, Faber, TSMOM) |

Los CSV y resúmenes de la ronda 1 están en `reports/`. Monte Carlo: `reports/baselines/20261111-0141/<slug>/`. Robustez: `reports/robustez/<slug>/`.

---

## Instalación y tests

Hace falta **Python 3.12** y [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/SrJorgeG/trading-lab.git
cd trading-lab
uv sync --all-extras --dev

uv run ruff check
uv run ruff format --check
uv run pytest -q                  # sin red; en el CI de main: 322 passed, 3 deselected
```

Los tests de red (Alpaca/yfinance) no corren por defecto:

```bash
uv run pytest -q -m network       # opcional; algunos necesitan claves paper
```

Para un backtest, `uv run python scripts/backtest.py --help`. Los modos reservados (OOS y tramos equivalentes de la ronda 2) están candados: H1–H4 están rechazadas y no se reexaminan. El visor opcional:

```bash
uv sync --extra visor
uv run streamlit run scripts/visor.py
```

Si quieres conectar la cuenta **paper** de Alpaca, sigue [`SETUP_ALPACA.md`](SETUP_ALPACA.md): copia `plantillas/.env.example` a `.env` (queda fuera de git) y usa **solo** claves paper. El código se niega a arrancar contra el endpoint real.

Todavía no hay ejecutor diario ni `STRATEGY.md`: ese era el siguiente paso, cuando se retome.

---

Ni este repo ni quienes lo mantienen somos asesores financieros. Esto es para aprender.
