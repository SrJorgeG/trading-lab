# Investigación: contraste yfinance ↔ Alpaca (7 ETFs en REVISAR)

11 nov 2026, hora de Madrid. Investigación hecha **sin claves de Alpaca** (no hay barras
Alpaca en este ordenador). Los números de Alpaca que se citan son los del contraste ya
corrido en el PC de Jorge. Los de yfinance se midieron hoy aquí, con `auto_adjust=True` y
`auto_adjust=False`, tramo 2016-01-01 → 2026-10-31 (2.722 sesiones).

No es asesoramiento financiero. Solo paper.

## 1. Qué compara el script (y qué no)

`scripts/check_alpaca_vs_yf.py` y `src/tlab/data/crosscheck.py` comparan **rentabilidades
diarias de cierre a cierre**, no los niveles de precio. La correlación es de esos retornos.
El código está bien: no hay un bug de «correlacionar precios». Un desfase de calendario de
±1 día también se mira (`best_lag`); en el resumen que vimos no se reportó desfase, así que
la alineación de fechas (Alpaca pone la vela diaria a las 04:00/05:00 UTC, medianoche ET, y
el loader la pasa a medianoche UTC, igual que yfinance) **parece** correcta. El diagnóstico
de §5 lo confirma.

Tolerancias (fijadas antes de ver datos, y no se tocan ahora): ETFs, |Δ| ≤ 10 pb en ≥ 99 %
de los días y correlación ≥ 0,999.

## 2. Qué vimos en el contraste

REVISAR: DIA corr 0,9983; EEM 99,0 % de días dentro de ±10 pb; EFA corr 0,9987; GLD corr
0,9958; IWM 98,3 % dentro de ±10 pb; SPY 98,4 % y corr 0,9961; VNQ corr 0,9801.

OK: BTC/ETH/LTC/BCH (corr ~0,997, con tolerancia más laxa), DBC, IEF (0,9999), QQQ (1,0000).

No tenemos aquí la tabla completa (mediana, p99, fecha del máximo, días que faltan, feed
real, `best_lag`). Eso sale otra vez con el diagnóstico.

## 3. Causas, con lo confirmado y lo que sigue siendo hipótesis

Hay **dos mecanismos**, y no es «todo dividendos».

### A. Los cierres no son exactamente el mismo precio (confirma el mecanismo; la magnitud
contra Alpaca no se puede medir aquí)

Alpaca construye la vela diaria SIP con el **último trade elegible** de la sesión. El
mensaje de cierre oficial (condición `M`) **no** entra en el OHLC; el trade de la subasta
(condición `6`) sí. Yahoo, en la práctica, usa el cierre oficial de la bolsa de cotización
(y el *adjusted close* sigue el criterio CRSP: factor `1 − dividendo / cierre anterior`,
[documentado por Yahoo](https://help.yahoo.com/kb/finance/adjusted-close-sln28256.html)).
Casi siempre coinciden; a veces no (un print elegible posterior a la subasta, o un ETP cuyo
cierre oficial no es un trade). Docs: [FAQ de Alpaca](https://docs.alpaca.markets/us/docs/market-data-faq),
[foro sobre open/close vs subasta](https://forum.alpaca.markets/t/open-close-daily-bar-prices-vs-open-close-auction-prices-on-primary-exchange/14227).

Esto es la única explicación viable para **GLD**:

- En yfinance, GLD **no tiene ningún dividendo ni split** en 2016–2026. Close y Adj Close
  son idénticos los 2.722 días (ratio = 1).
- Si Alpaca y Yahoo usaran el mismo cierre, la correlación de rentabilidades sería 1 y el
  contraste aprobaría. Se midió 0,9958 → **REVISAR no puede ser un tema de dividendos**.

El script pide `feed=sip` y, si no hay suscripción, cae a IEX. El IEX es un subconjunto de
trades y ensancha este hueco (el propio FAQ de Alpaca muestra AAPL el 2023-09-29: SIP 171,21
frente a IEX 171,29). El contraste se describió como SIP; el diagnóstico imprime el feed
real por si acaso hubo *fallback*.

### B. El ajuste por dividendos no es idéntico en todos los símbolos (contribuye, pero no
lo explica todo)

Las dos fuentes dicen ajustar por splits y dividendos (Alpaca `adjustment=all`, yfinance
`auto_adjust=True`). En yfinance, Close con `auto_adjust=True` coincide con `Adj Close`
(diferencia máxima 0 pb). Alpaca, en abril de 2026, corrigió el factor de dividendos para
usar el cierre **anterior** al ex-div (antes usaba el del propio ex-div;
[foro, TPG](https://forum.alpaca.markets/t/bad-data-incorrect-price-adjustment-for-cash-dividend/18614)).
En 2025 también limpiaron dividendos de más en su base
([foro](https://forum.alpaca.markets/t/adjusted-prices-rounding-issue/15519)). El contraste
es de noviembre de 2026, posterior a esos arreglos.

Si Alpaca **no** aplicara dividendos y Yahoo sí, el desajuste se concentraría en los
ex-div. Midiéndolo solo con yfinance (retorno total vs Close solo por splits):

| ETF | n.º div | med / máx div (pb) | corr adj vs split | % días ≤ 10 pb | ¿aprobaría las tolerancias? |
|---|---:|---:|---:|---:|---|
| SPY | 43 | 40 / 59 | 0,9990 | 98,4 % | no (share y corr) |
| QQQ | 43 | 17 / 30 | 0,9999 | 98,5 % | no (solo share) |
| IWM | 43 | 30 / 55 | 0,9996 | 98,4 % | no (solo share) |
| DIA | 130 | 19 / 37 | 0,9993 | 97,0 % | no (solo share) |
| EFA | 22 | 148 / 216 | 0,9925 | 99,2 % | no (solo corr) |
| EEM | 22 | 90 / 209 | 0,9970 | 99,2 % | no (solo corr) |
| IEF | 129 | 18 / 36 | 0,9941 | 96,1 % | no (los dos) |
| GLD | 0 | — | 1,0000 | 100 % | sí |
| DBC | 6 | 242 / 507 | 0,9910 | 99,8 % | no (solo corr) |
| VNQ | 43 | 95 / 206 | 0,9951 | 98,4 % | no (los dos) |

En todos, los días que superan 10 pb son **exactamente** los ex-div (cero días «sueltos»).

Esto **no** encaja con un «Alpaca no ajusta dividendos»:

- **IEF** (129 dividendos mensuales) y **DBC** (6 distribuciones, una de ~507 pb) **aprobaron**
  el contraste. Sin ajuste, IEF saldría a corr 0,9941 / 96,1 % de días y DBC a corr 0,9910.
  Alpaca **sí está ajustando**, al menos en estos.
- **QQQ** (43 dividendos, como SPY) aprobó con corr 1,0000. Sin ajuste fallaría el 98,5 % de
  días. Mismo argumento.
- **SPY** midió 98,4 % de días dentro de ±10 pb: el mismo porcentaje que sale al no ajustar
  sus 43 dividendos. Pero su correlación observada (0,9961) es **peor** que la de «Yahoo
  total vs Yahoo solo splits» (0,9990). Hace falta algo más que «se olvidó de los
  dividendos de SPY».
- **VNQ** (el de más yield; factor acumulado 0,65) midió corr 0,9801, **peor** que no
  ajustar en absoluto (0,9951). Dividendos solos no bastan; hay divergencia adicional
  (cierres distintos y/o algún corporativo mal aplicado en un proveedor).
- **EFA** observado (0,9987) es **mejor** que no ajustar (0,9925): Alpaca ajusta, pero no
  lo bastante para llegar a 0,999. DIA 0,9983 y EEM «99,0 %» están en la misma zona
  justita (99,0 % impreso puede ser un 98,95 % que ya no cumple el ≥ 99 %).

Conclusión honesta: las tolerancias son muy estrechas (DIA a 0,9983 ya es REVISAR). Parte
del REVISAR de los que pagan dividendo es coherente con pequeños desajustes en el día ex-div
(monto, fecha o cierre usado en el factor). **No** es la historia completa, y en GLD y VNQ
casi seguro no es la principal.

## 4. ¿Sesga los backtests que usan yfinance?

Los TOML de las candidatas llevan `data_source = "yfinance"` a propósito (historia larga;
Alpaca no llega a 2007 ni a 2015 en cripto). Esa serie es retorno total (`auto_adjust`).
Eso es lo correcto para un backtest que no cobra el dividendo en caja.

Lo que hay no es «yfinance está sin ajustar». Es un hueco **entre proveedores** en el tramo
común, de tamaño pequeño en QQQ/IEF/DBC y mayor en VNQ y GLD. Sin las barras de Alpaca no
puedo medir cuánto cambiaría la curva de equity si se repitiera el backtest en Alpaca
2016–2026. Por la correlación de retornos (aún 0,98 en el peor caso, 0,995–0,999 en el
resto) es poco probable que Donchian 55/20 o el momentum a 12 meses cambien de señal en
muchos días. RSI(2) es más sensible a movimientos de uno o dos días, sobre todo alrededor
de un ex-div si luego el paper usa barras de Alpaca.

El riesgo práctico no es tanto un sesgo de selección en el IS, sino que **el paper (Alpaca)
no va a clonar el backtest (yfinance) al tick**. Sobre todo en VNQ y en fechas ex-div.
Hay que vigilar esa divergencia, no tirar los backtests ni cambiar la fuente a Alpaca
(rompería las fechas pre-registradas).

## 5. Recomendación

1. **No bloquees el paso 3 de Fable por esto.** El script hizo su trabajo (parar e
   investigar). Tras investigarlo, el cuadro es: umbrales muy justos, dos proveedores
   que no son idénticos, yfinance sigue siendo la fuente adecuada para la historia larga,
   y cuatro universos (cripto, IEF, QQQ, DBC) ya cuadraban.
2. **No afines las tolerancias a posteriori** sin que lo decidan Jorge o Fable: se
   fijaron antes de ver datos.
3. En jorge-cachy, con el `.env` de Alpaca paper, corre el diagnóstico de abajo. Lo que
   hay que mirar: que el feed sea SIP y `best_lag = 0`; en GLD, que «YF split vs Alpaca
   split» falle igual que el contraste oficial (confirmaría cierres, no dividendos); en
   SPY/VNQ/IEF, qué fracción de los peores días cae en ex-div, y si «YF split vs Alpaca
   split» ya cuadra (entonces era el ajuste) o también falla (entonces también son los
   cierres).
4. Deja los TOML en yfinance. Cuando Fable tenga el veredicto, un backtest de sensibilidad
   en Alpaca 2016–2026 (mismas reglas, sin usar el resultado para elegir) es el control
   limpio. No hace falta para arrancar el paso 3.

## 6. Comando en el PC de Jorge

En `jorge-cachy`, con la app de Grok Bot abierta y el `.env` en el repo:

```bash
cd ~/trading-lab
git fetch origin
git checkout paso2/candidatas
git pull
uv run python scripts/diag_alpaca_vs_yf.py
```

Escribe `reports/datos/diag_alpaca_vs_yf_<fecha>.md` (no opera, no imprime claves). Si el
`git checkout` o el `pull` fallan por cambios locales, no los tires: avisa y lo vemos.
