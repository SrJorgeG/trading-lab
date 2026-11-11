# 20 estrategias comunes de trading

Informe educativo para Jorge, en Madrid: 20 estrategias habituales y el copy trading como referencia, con evidencia citada, una tabla comparativa y una shortlist de cinco reglas simples que Fable puede backtestear antes del 17 de noviembre de 2026, a las 8:59 hora de Madrid. No es asesoramiento financiero; la rentabilidad pasada no garantiza resultados futuros.

> **Esto no es asesoramiento financiero**
>
> Este informe es solo educativo. No es una recomendación para comprar, vender ni invertir dinero real. La rentabilidad pasada, incluida la de los papers que cito, no garantiza resultados futuros. Ningún número de este texto es una previsión. Si alguna vez pasáis de paper a real, será porque tú lo decidas, no porque este documento lo autorice.

| | |
| --- | --- |
| **20 + 1** | Estrategias y una referencia |
| **5** | Candidatas para Fable |
| **17 nov, 8:59** | Fin de Fable (hora de Madrid) |

## Cómo usar este informe

Preparado el 11 de noviembre de 2026, hora de Madrid (Europe/Madrid, UTC+1), para alguien que empieza, todavía no tiene capital real y quiere usar Claude Fable —disponible en su plan hasta el 17 de noviembre de 2026 a las 8:59, hora de Madrid— para dejar una estrategia escrita en reglas, fácil de ejecutar después por un modelo más barato (Sonnet) o por un script de Python. El paper trading sería en Alpaca, con acciones y ETFs de EE. UU. y cripto.

La meta no es que Fable 'invente dinero' en una semana. Es que proponga reglas claras, las backtestee con comisiones y slippage, y deje un manual que luego pueda ejecutar un modelo menos capaz, o incluso código sin inteligencia artificial. Por eso aquí gana la estrategia aburrida y escrita, no la que exige estar pegado a la pantalla o 'tener ojo'.

Empieza por la tabla, filtra por lo que te importa (poco tiempo de pantalla, que encaje en Alpaca, que un script pueda ejecutarla) y abre la ficha de cada una. Al final va mi shortlist: cinco candidatas para que Fable las ponga a prueba, no para que las des por buenas. El listón es siempre el mismo: ¿le gana, después de costes, a comprar y mantener?

Cómo leer la columna de evidencia. Sólida: hay papers serios que documentan el fenómeno; no significa que tú lo vayas a capturar. Mixta: hay estudios, pero se contradicen, se debilitan tras costes o dependen de cómo se implemente. Débil: lo que hay no sostiene una ventaja estable para un particular. Insuficiente: no hay un cuerpo académico comparable; no invento estadísticas.

## Tabla comparativa

Capital 'bajo' quiere decir que se puede probar con poco (un ETF o un par cripto). 'Alto' suele pedir universo amplio, cortos, margen, opciones o mucho colchón. En paper, Alpaca te da un saldo ficticio; esas etiquetas miran al día en que, si acaso, pasáis a real. 'Sonnet / Python' valora si la regla se puede ejecutar sin criterio humano. Las filas de la shortlist se marcan en la primera columna.

| Estrategia | Familia | Frecuencia | Automatizar | Capital | Pantalla | Alpaca | Sonnet / Python | Evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Comprar y mantener + rebalanceo · shortlist | Pasivo | Muy baja | Baja | Baja | Baja | Alta | Alta | Sólida |
| 2. DCA y DCA con filtro de tendencia | Pasivo | Muy baja | Baja | Baja | Baja | Alta | Alta | Mixta |
| 3. Cruce de medias móviles | Tendencia | Baja | Baja | Baja | Baja | Alta | Alta | Mixta |
| 4. Asignación táctica de Faber (media de 10 meses) · shortlist | Tendencia | Muy baja | Baja | Baja | Baja | Alta | Alta | Sólida |
| 5. Ruptura Donchian / Turtle · shortlist | Tendencia | Baja | Baja | Media | Baja | Alta | Alta | Sólida |
| 6. Momentum de series temporales · shortlist | Momentum | Muy baja | Baja | Media | Baja | Alta | Alta | Sólida |
| 7. Momentum cruzado (ganadores frente a perdedores) | Momentum | Baja | Media | Alta | Baja | Media | Media | Sólida |
| 8. Dual momentum · shortlist | Momentum | Muy baja | Baja | Baja | Baja | Alta | Alta | Mixta |
| 9. Volatility targeting (ajuste por volatilidad) | Tendencia | Baja | Media | Media | Baja | Media | Media | Mixta |
| 10. Reversión a la media con RSI(2) / Connors | Reversión | Media | Baja | Media | Baja | Alta | Alta | Insuficiente |
| 11. Bandas de Bollinger (reversión) | Reversión | Media | Baja | Media | Baja | Alta | Alta | Insuficiente |
| 12. Swing en pullbacks | Tendencia | Baja | Media | Media | Media | Alta | Media | Insuficiente |
| 13. Pairs trading | Estadístico | Media | Alta | Alta | Media | Media | Baja | Mixta |
| 14. PEAD (deriva después de resultados) | Momentum | Media | Media | Media | Media | Media | Media | Sólida |
| 15. Carry / funding en cripto | Carry | Baja | Media | Alta | Media | No encaja | Media | Sólida |
| 16. Ruptura del rango de apertura (ORB) | Intradía | Alta | Media | Media | Alta | Media | Media | Débil |
| 17. VWAP (precio medio ponderado por volumen) | Intradía | Alta | Media | Media | Alta | Media | Media | Insuficiente |
| 18. Grid trading | Reversión | Alta | Baja | Media | Media | Media | Media | Insuficiente |
| 19. Scalping | Intradía | Alta | Alta | Alta | Alta | Baja | Baja | Débil |
| 20. Covered calls y The Wheel | Opciones | Baja | Media | Alta | Media | Media | Media | Mixta |
| 21. Copy trading (referencia, no es una estrategia propia) | Social | Media | Baja | Media | Baja | No encaja | Baja | Débil |

## Las 20 estrategias, una a una

Fichas para leer con calma. El copy trading va al final, como referencia, no como candidata.

### 1. Comprar y mantener + rebalanceo · Shortlist
**Evidencia:** Sólida

Comprar un índice amplio (o un puñado de ETFs) y dejarlo trabajar, reequilibrando de vez en cuando.

| Campo | Valor |
| --- | --- |
| Familia | Pasivo |
| Etiqueta | Shortlist |
| Entrada | Comprar un ETF amplio de acciones de EE. UU. (por ejemplo SPY o VTI) o una cartera simple de ETFs (acciones, bonos) y mantenerla. |
| Salida | No hay salida de 'trade'. Solo se rebalancea periódicamente (por ejemplo una vez al año, o cuando un activo se desvía un 5–10 % de su peso objetivo) o si necesitas el dinero. |
| Stop | No suele llevar stop de trading. El riesgo es aguantar caídas grandes y largas. |
| Mercado | ETFs de EE. UU. en Alpaca. También se puede 'mantener' BTC o ETH, pero es mucho más volátil y no es un índice clásico. |
| Timeframe | Años |
| Frecuencia | Muy baja. Cero o uno o dos ajustes al año. |
| Automatizar | Baja |
| Capital | Baja |
| Pantalla | Baja |
| Alpaca | Alta. Encaja perfecto en paper: un ETF líquido y órdenes ocasionales. |
| Sonnet / Python | Alta |
| Perfil | Pasivo · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | ETFs de EE. UU. en Alpaca. También se puede 'mantener' BTC o ETH, pero es mucho más volátil y no es un índice clásico. Años. Cero o uno o dos ajustes al año. |

#### Riesgos y trampas típicas

Caídas duras (un drawdown es la caída desde un máximo hasta el mínimo siguiente). Concentrarte en un solo activo. Vender en el peor momento por miedo, que es justo lo que destroza un plan pasivo.

#### Qué dice la evidencia (sólida)

No es una receta para 'ganar al mercado': es el propio mercado (menos comisiones). Sirve como listón. Cualquier estrategia activa tiene que superarlo después de costes para justificar el esfuerzo. No hay una rentabilidad futura que se pueda prometer.

_Sin enlaces en la ficha._

### 2. DCA y DCA con filtro de tendencia
**Evidencia:** Mixta

Invertir una cantidad fija a intervalos regulares. La variante con filtro evita comprar cuando la tendencia de largo plazo es bajista.

| Campo | Valor |
| --- | --- |
| Familia | Pasivo |
| Etiqueta | Pasivo |
| Entrada | DCA puro (dollar-cost averaging: comprar una cantidad fija a intervalos regulares): cada mes o cada semana compras por un importe fijo, da igual el precio. Con filtro: solo compras si el precio mensual está por encima de su media de 10 meses; si no, el dinero se queda en efectivo. |
| Salida | Normalmente no se vende por una señal. Es un plan de acumulación, no un sistema de entradas y salidas. |
| Stop | No típico. El filtro de tendencia, si lo usas, simplemente deja de comprar. |
| Mercado | ETFs de EE. UU. y, si se quiere, BTC o ETH en Alpaca. |
| Timeframe | Mensual (a veces semanal) |
| Frecuencia | Muy baja. Una orden programada al mes, o ninguna si el filtro bloquea. |
| Automatizar | Baja |
| Capital | Baja |
| Pantalla | Baja |
| Alpaca | Alta. Muy fácil de ejecutar en paper con órdenes periódicas. |
| Sonnet / Python | Alta |
| Perfil | Pasivo · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | ETFs de EE. UU. y, si se quiere, BTC o ETH en Alpaca. Mensual (a veces semanal). Una orden programada al mes, o ninguna si el filtro bloquea. |

#### Riesgos y trampas típicas

Si los mercados suben más a menudo que bajan, repartir la entrada suele rendir menos que invertir de golpe, porque parte del dinero se queda en efectivo. El filtro puede hacerte perder tramos de subida o quedarte mucho tiempo sin comprar.

#### Qué dice la evidencia (mixta)

Vanguard, en 'Cost averaging: Invest now or temporarily hold your cash?', concluye que invertir una cantidad de golpe superó a repartirla en el tiempo en torno a dos tercios de los periodos que analizaron (por ejemplo, en ventanas móviles de un año entre 1976 y 2022). El DCA puede ayudar si te cuesta psicológicamente entrar de una vez, pero no es una fórmula para ganar más. El filtro de tendencia se solapa con la evidencia de Faber, que es otro apartado.

- [Vanguard, Cost averaging: Invest now or temporarily hold your cash?](https://corporate.vanguard.com/content/dam/corp/research/pdf/cost_averaging_invest_now_or_temporarily_hold_your_cash.pdf)

### 3. Cruce de medias móviles
**Evidencia:** Mixta

Comprar cuando una media corta cruza por encima de una larga, y vender cuando cruza a la baja.

| Campo | Valor |
| --- | --- |
| Familia | Tendencia |
| Etiqueta | Tendencia |
| Entrada | Señal clásica: la media de 50 días cruza por encima de la de 200 (el llamado golden cross). Hay versiones más rápidas (10/20, 20/50). La media es el promedio del precio de las últimas N velas. |
| Salida | El cruce contrario (death cross: la media corta cruza por debajo de la larga). |
| Stop | Muchas versiones clásicas solo usan el cruce de salida. Otras añaden un stop bajo un mínimo reciente o a 2 veces el ATR (el tamaño medio reciente de las velas). |
| Mercado | Índices, ETFs líquidos y cripto. Mejor en diario o 4 horas; en minutos hay mucho ruido. |
| Timeframe | Diario o 4 horas |
| Frecuencia | Baja. Pocos cruces al año en 50/200; más si las medias son cortas. |
| Automatizar | Baja |
| Capital | Baja |
| Pantalla | Baja |
| Alpaca | Alta. Regla 100 % mecánica sobre SPY, QQQ, BTC o ETH. |
| Sonnet / Python | Alta |
| Perfil | Tendencia · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | Índices, ETFs líquidos y cripto. Mejor en diario o 4 horas; en minutos hay mucho ruido. Diario o 4 horas. Pocos cruces al año en 50/200; más si las medias son cortas. |

#### Riesgos y trampas típicas

Falsos cruces en mercados laterales. Llegas tarde a las subidas y tarde a las salidas. Elegir los periodos (50/200, 10/20…) mirando el pasado es una trampa clásica de sobreajuste.

#### Qué dice la evidencia (mixta)

Brock, Lakonishok y LeBaron (1992, Journal of Finance) encontraron que, en el Dow Jones de 1897 a 1986, las señales de compra de reglas simples de medias y rupturas se comportaron mejor que las de venta. Sullivan, Timmermann y White (1999, Journal of Finance) volvieron a mirar miles de variantes y, tras corregir el data-snooping (probar tantas reglas que alguna 'gana' por casualidad), no encontraron que esa ventaja persistiera en 1987–1996.

- [Brock, Lakonishok y LeBaron, 1992, Journal of Finance](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x)
- [Sullivan, Timmermann y White, 1999, Journal of Finance](https://doi.org/10.1111/0022-1082.00163)

### 4. Asignación táctica de Faber (media de 10 meses) · Shortlist
**Evidencia:** Sólida

Estar invertido en un activo solo cuando su precio mensual cierra por encima de su media de 10 meses; si no, efectivo.

| Campo | Valor |
| --- | --- |
| Familia | Tendencia |
| Etiqueta | Shortlist |
| Entrada | Al cierre del mes, si el precio (con dividendos, en la receta original) está por encima de su media móvil de 10 meses, se compra o se mantiene. |
| Salida | Al cierre del mes, si el precio queda por debajo de esa media, se vende y el dinero pasa a efectivo o a un activo muy seguro. |
| Stop | No hay stop intradía. La propia media mensual hace de salida. |
| Mercado | ETFs de acciones, bonos, oro o inmobiliario; se puede aplicar también a BTC en velas mensuales. |
| Timeframe | Mensual |
| Frecuencia | Muy baja. Unas pocas decisiones al año, siempre a fin de mes. |
| Automatizar | Baja |
| Capital | Baja |
| Pantalla | Baja |
| Alpaca | Alta. Ideal en paper con ETFs líquidos (SPY, QQQ, IEF, GLD, VNQ, etc.). |
| Sonnet / Python | Alta |
| Perfil | Tendencia · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | ETFs de acciones, bonos, oro o inmobiliario; se puede aplicar también a BTC en velas mensuales. Mensual. Unas pocas decisiones al año, siempre a fin de mes. |

#### Riesgos y trampas típicas

La señal llega tarde. En una caída muy rápida la media no te saca a tiempo. En mercados laterales puedes entrar y salir varias veces. El paper original no incluye comisiones ni slippage (la diferencia entre el precio que esperas y el que te dan).

#### Qué dice la evidencia (sólida)

Faber (2007, Journal of Wealth Management), en 'A Quantitative Approach to Tactical Asset Allocation', presenta esta regla mensual y reporta, en su muestra histórica, rentabilidades tipo renta variable con volatilidad y caídas más parecidas a la renta fija. Eso es un resultado histórico del autor, no una previsión. El propio trabajo avisa de que deja fuera comisiones y slippage. Hay que repetir el test con costes, en datos que no se usaron para diseñarlo, y compararlo con comprar y mantener.

- [Faber, 2007, Journal of Wealth Management (SSRN)](https://ssrn.com/abstract=962461)

### 5. Ruptura Donchian / Turtle · Shortlist
**Evidencia:** Sólida

Comprar cuando el precio rompe el máximo de N días y salir cuando rompe un mínimo reciente.

| Campo | Valor |
| --- | --- |
| Familia | Tendencia |
| Etiqueta | Shortlist |
| Entrada | Reglas Turtle típicas: Sistema 1, entrar un tick por encima del máximo de 20 días (a veces se salta si la ruptura anterior habría sido ganadora). Sistema 2, ruptura de 55 días. Para un principiante en long-only (solo compras, sin vender corto): comprar la ruptura del máximo de 20 o 55 días. |
| Salida | Sistema 1: ruptura del mínimo de 10 días. Sistema 2: mínimo de 20 días. |
| Stop | Los Turtles usaban un stop de 2 veces N, donde N es el ATR. El tamaño de la posición era inverso a la volatilidad. Una regla moderna prudente: arriesgar como mucho un 1 % del capital por operación. |
| Mercado | Originalmente, futuros. Hoy se prueba en ETFs, índices y cripto. Diario (clásico) o 4 horas. |
| Timeframe | Diario o 4 horas |
| Frecuencia | Baja. Varias operaciones al año por activo; no es intradía. |
| Automatizar | Baja |
| Capital | Media |
| Pantalla | Baja |
| Alpaca | Alta. Muy usable en long-only sobre un ETF y sobre BTC/ETH. Los futuros apalancados de las reglas originales no son el mismo producto. |
| Sonnet / Python | Alta |
| Perfil | Tendencia · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | Originalmente, futuros. Hoy se prueba en ETFs, índices y cripto. Diario (clásico) o 4 horas. Diario o 4 horas. Varias operaciones al año por activo; no es intradía. |

#### Riesgos y trampas típicas

Muchas rupturas falsas y rachas largas de pérdidas. Las reglas originales son de futuros con apalancamiento, un perfil de riesgo distinto. El documento de los Turtles es un texto de practitioners, no un paper académico.

#### Qué dice la evidencia (sólida)

El seguimiento de tendencia de este estilo tiene respaldo amplio en Hurst, Ooi y Pedersen (2017, Journal of Portfolio Management), 'A Century of Evidence on Trend-Following Investing': estudian estrategias de tendencia / momentum de series temporales en muchos mercados desde 1880 y encuentran rentabilidades medias positivas en cada década de su muestra, con baja correlación a acciones y bonos. Eso no implica que una cuenta pequeña en BTC o SPY vaya a repetir esos números.

- [Hurst, Ooi y Pedersen, 2017, Journal of Portfolio Management (AQR)](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing)

### 6. Momentum de series temporales · Shortlist
**Evidencia:** Sólida

Si un activo ha subido (respecto al efectivo) en los últimos 12 meses, se mantiene largo el mes siguiente; si ha bajado, se queda fuera o se pone corto.

| Campo | Valor |
| --- | --- |
| Familia | Momentum |
| Etiqueta | Shortlist |
| Entrada | Al cierre mensual, si el retorno de los últimos 12 meses es positivo (o supera a las letras del Tesoro), se compra o se mantiene. Algunas versiones combinan señales de 1, 3 y 12 meses. |
| Salida | En el siguiente rebalanceo mensual, si el signo de la señal cambia. |
| Stop | No es un stop de operación. A menudo se escala el tamaño según la volatilidad reciente. |
| Mercado | En la literatura, futuros de índices, divisas, materias primas y bonos. En Alpaca: versión solo-compras sobre ETFs y cripto. |
| Timeframe | Mensual |
| Frecuencia | Muy baja. Una decisión al mes por activo. |
| Automatizar | Baja |
| Capital | Media |
| Pantalla | Baja |
| Alpaca | Alta. La versión long-only sobre SPY, un ETF internacional y BTC/ETH es directa. La versión académica usa futuros y cortos. |
| Sonnet / Python | Alta |
| Perfil | Momentum · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | En la literatura, futuros de índices, divisas, materias primas y bonos. En Alpaca: versión solo-compras sobre ETFs y cripto. Mensual. Una decisión al mes por activo. |

#### Riesgos y trampas típicas

El efecto se revierte en parte a horizontes más largos. Hay periodos malos (mercados laterales o giros bruscos). Aplicarlo a un solo activo, por ejemplo solo BTC, no es el estudio original, que diversifica muchos contratos.

#### Qué dice la evidencia (sólida)

Moskowitz, Ooi y Pedersen (2012, Journal of Financial Economics) documentan 'time series momentum' en 58 futuros: el retorno de 12 meses predice el retorno siguiente. El efecto dura unos doce meses y luego se revierte en parte. En su muestra, los beneficios a 12 meses fueron positivos en cada contrato. Es pariente, pero distinto, del momentum cruzado. En cripto, Liu y Tsyvinski (2021, Review of Financial Studies) documentan momentum de series temporales a horizonte de una y dos semanas en las criptomonedas principales.

- [Moskowitz, Ooi y Pedersen, 2012, Journal of Financial Economics](https://www.sciencedirect.com/science/article/pii/S0304405X11002613)
- [Liu y Tsyvinski, 2021, Review of Financial Studies](https://doi.org/10.1093/rfs/hhaa113)

### 7. Momentum cruzado (ganadores frente a perdedores)
**Evidencia:** Sólida

Comprar los activos que más han subido frente a sus pares en los últimos 3 a 12 meses, y evitar o vender los que más han bajado.

| Campo | Valor |
| --- | --- |
| Familia | Momentum |
| Etiqueta | Momentum |
| Entrada | Cada mes, ordenar el universo por el retorno de 12 meses (a menudo saltando el último mes, para no mezclarlo con la reversión a muy corto plazo). Comprar el grupo de ganadores (un decil o un tercil). |
| Salida | Rebalanceo mensual, o mantener 3 a 12 meses según la receta. |
| Stop | No suele llevar stop clásico. Se evitan valores ilíquidos y, a veces, se limita el peso de cada nombre. |
| Mercado | Muchas acciones de EE. UU.; la literatura lo ha visto también en otros países y clases de activo. |
| Timeframe | Mensual |
| Frecuencia | Baja. Rebalanceo mensual, pero con muchas líneas si el universo es grande. |
| Automatizar | Media |
| Capital | Alta |
| Pantalla | Baja |
| Alpaca | Media. Se puede hacer una versión solo-compras con pocos ETFs sectoriales o un universo reducido. Un decil de acciones con cortos pide más capital y más datos. |
| Sonnet / Python | Media |
| Perfil | Momentum · Automatizar media · Alpaca media · Sonnet/Python media |
| Mercado y timeframe | Muchas acciones de EE. UU.; la literatura lo ha visto también en otros países y clases de activo. Mensual. Rebalanceo mensual, pero con muchas líneas si el universo es grande. |

#### Riesgos y trampas típicas

Hay 'momentum crashes': cuando el mercado rebota con fuerza, los perdedores pueden dispararse y aplastar la estrategia (Daniel y Moskowitz, 2016, Journal of Financial Economics). Los costes de rotación importan. Si el backtest no incluye acciones que luego se delistaron, el resultado queda inflado.

#### Qué dice la evidencia (sólida)

Jegadeesh y Titman (1993, Journal of Finance) documentan que comprar ganadores y vender perdedores a horizontes de 3 a 12 meses generó rentabilidades anómalas en acciones de EE. UU. entre 1965 y 1989. Asness, Moskowitz y Pedersen (2013, Journal of Finance), en 'Value and Momentum Everywhere', encuentran primas de momentum (y de valor) en varios mercados y clases de activo. La evidencia del fenómeno es amplia; capturarlo con poco capital, sin cortos y después de costes es otra cosa.

- [Jegadeesh y Titman, 1993, Journal of Finance](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x)
- [Asness, Moskowitz y Pedersen, 2013, Journal of Finance](https://doi.org/10.1111/jofi.12021)

### 8. Dual momentum · Shortlist
**Evidencia:** Mixta

Elige el mercado más fuerte (momentum relativo) y solo invierte si también está en tendencia alcista absoluta; si no, te vas a un activo refugio.

| Campo | Valor |
| --- | --- |
| Familia | Momentum |
| Etiqueta | Shortlist |
| Entrada | Versión educativa al estilo GEM de Antonacci: cada mes comparas el retorno a 12 meses de acciones de EE. UU. (por ejemplo SPY) y de acciones internacionales (un ETF cotizado en EE. UU.). Te quedas con el más fuerte. Si ese más fuerte no ha superado a las letras del Tesoro —o no tiene retorno absoluto positivo— en 12 meses, pasas a bonos o a efectivo. |
| Salida | El mismo rebalanceo mensual: cambias de ETF cuando lo dicen las reglas. |
| Stop | El salto a refugio es la protección. No hay stop intradía. |
| Mercado | ETFs de acciones de EE. UU., internacionales y de bonos, todos cotizados en EE. UU. |
| Timeframe | Mensual |
| Frecuencia | Muy baja. Una decisión al mes, a menudo sin hacer nada. |
| Automatizar | Baja |
| Capital | Baja |
| Pantalla | Baja |
| Alpaca | Alta. Muy natural en Alpaca: pocos ETFs líquidos y órdenes mensuales. |
| Sonnet / Python | Alta |
| Perfil | Momentum · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | ETFs de acciones de EE. UU., internacionales y de bonos, todos cotizados en EE. UU. Mensual. Una decisión al mes, a menudo sin hacer nada. |

#### Riesgos y trampas típicas

La señal va con un año de retraso y puedes quedarte fuera de un rebote. Es fácil tentarse a 'optimizar' el lookback. Los números del autor no son una garantía.

#### Qué dice la evidencia (mixta)

Antonacci, en 'Risk Premia Harvesting Through Dual Momentum' (SSRN; una versión apareció en Journal of Management & Entrepreneurship, 2017), concluye que el momentum absoluto reduce más la volatilidad y las caídas, y que combinar absoluto y relativo da el mejor resultado en su muestra. Es investigación del propio autor de la receta, no un clásico del mismo rango que Jegadeesh o Moskowitz. Hay que backtestearlo de forma independiente, con comisiones, y no dar por buenos los números del paper.

- [Antonacci, Risk Premia Harvesting Through Dual Momentum (SSRN)](https://ssrn.com/abstract=2042750)

### 9. Volatility targeting (ajuste por volatilidad)
**Evidencia:** Mixta

No es una señal de compra por sí sola: reduce el tamaño cuando el mercado está nervioso y lo aumenta cuando está tranquilo, para intentar mantener la volatilidad de la cartera más estable.

| Campo | Valor |
| --- | --- |
| Familia | Tendencia |
| Etiqueta | Tendencia |
| Entrada | Las entradas son las de la estrategia de debajo (por ejemplo, estar en SPY). El tamaño se calcula como volatilidad objetivo dividida por la volatilidad reciente (por ejemplo, de 20 o 21 días). |
| Salida | Las de la estrategia subyacente. El overlay solo cambia cuánto capital está invertido. |
| Stop | No sustituye a un stop; solo limita el tamaño. |
| Mercado | Índices y ETFs; también como capa encima de un sistema de tendencia. |
| Timeframe | Ajuste diario o mensual |
| Frecuencia | Baja. Reajustes periódicos del tamaño, no un flujo de trades. |
| Automatizar | Media |
| Capital | Media |
| Pantalla | Baja |
| Alpaca | Media. Se puede hacer en paper. Los papers académicos a veces asumen apalancamiento cuando la volatilidad es baja; para un principiante, mejor no superar el 100 % del capital. |
| Sonnet / Python | Media |
| Perfil | Tendencia · Automatizar media · Alpaca media · Sonnet/Python media |
| Mercado y timeframe | Índices y ETFs; también como capa encima de un sistema de tendencia. Ajuste diario o mensual. Reajustes periódicos del tamaño, no un flujo de trades. |

#### Riesgos y trampas típicas

Si la volatilidad reciente era baja, la regla puede pedirte más tamaño justo antes de un susto. El resultado depende mucho de cómo midas la volatilidad y de si te apalancas. Es una capa, no un sistema completo.

#### Qué dice la evidencia (mixta)

Moreira y Muir (2017, Journal of Finance) encuentran que escalar la exposición de forma inversa a la varianza del mes anterior mejoró, en su estudio, la relación entre rentabilidad y riesgo de varios factores. Cederburg, O'Doherty, Wang y Yan (2020, Journal of Financial Economics) argumentan que, en implementaciones que se pueden usar de verdad en tiempo real, las carteras 'volatility-managed' no superan de forma sistemática a las que no se gestionan así.

- [Moreira y Muir, 2017, Journal of Finance](https://doi.org/10.1111/jofi.12513)
- [Cederburg, O'Doherty, Wang y Yan, 2020, Journal of Financial Economics](https://doi.org/10.1016/j.jfineco.2020.04.015)

### 10. Reversión a la media con RSI(2) / Connors
**Evidencia:** Insuficiente

En una tendencia alcista de fondo, comprar un bajón muy corto y vender el rebote.

| Campo | Valor |
| --- | --- |
| Familia | Reversión |
| Etiqueta | Reversión |
| Entrada | El precio está por encima de su media de 200 días y el RSI de 2 periodos cae por debajo de 5 o de 10. El RSI (Relative Strength Index) es un oscilador de 0 a 100 que resume la fuerza reciente del precio. |
| Salida | El precio cierra por encima de su media de 5 días, o el RSI(2) vuelve por encima de 50–70, según la variante. |
| Stop | Las reglas originales de Connors a menudo no llevaban un stop fijo, y eso es un riesgo. Para paper, un stop amplio (por ejemplo 2–3 veces el ATR) es más prudente, aunque ya no es la regla original. |
| Mercado | Acciones de EE. UU. líquidas; a veces índices. Suele usarse en diario. |
| Timeframe | Diario (a veces 4 horas) |
| Frecuencia | Media. Varias operaciones al mes si miras un universo de acciones. |
| Automatizar | Baja |
| Capital | Media |
| Pantalla | Baja |
| Alpaca | Alta. Fácil de programar sobre acciones líquidas o sobre un ETF, siempre con comisiones realistas. |
| Sonnet / Python | Alta |
| Perfil | Reversión · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | Acciones de EE. UU. líquidas; a veces índices. Suele usarse en diario. Diario (a veces 4 horas). Varias operaciones al mes si miras un universo de acciones. |

#### Riesgos y trampas típicas

Suele acertar muchas veces y perder fuerte de vez en cuando. Los costes se comen un margen ya estrecho. En una caída de todo el mercado, 'comprar el bajón' puede ser pillar un cuchillo que sigue cayendo. Es muy fácil sobreajustar el umbral del RSI.

#### Qué dice la evidencia (insuficiente)

Las reglas las popularizó Larry Connors en libros y guías de trading, no en un paper clásico revisado por pares comparable a Jegadeesh o Moskowitz. Pruebas independientes posteriores —sobre todo blogs cuantitativos, no revistas académicas— dan resultados mixtos y a menudo frágiles después de comisiones. No hay una rentabilidad oficial que se pueda citar con confianza.

_Sin enlaces en la ficha._

### 11. Bandas de Bollinger (reversión)
**Evidencia:** Insuficiente

Apostar a que el precio vuelve hacia su media cuando se sale demasiado de ella.

| Campo | Valor |
| --- | --- |
| Familia | Reversión |
| Etiqueta | Reversión |
| Entrada | Cierre por debajo de la banda inferior: la media de 20 periodos menos dos desviaciones típicas. A veces solo si la tendencia de fondo no es claramente bajista. |
| Salida | Vuelta a la media de 20 periodos, o a la banda contraria. |
| Stop | Si el precio sigue viajando por fuera de la banda (tendencia fuerte), un stop o una regla del tipo 'si cierra otra vez fuera, cancelar'. |
| Mercado | Acciones líquidas, índices y, con más cuidado, cripto. Diario o 4 horas. |
| Timeframe | Diario o 4 horas |
| Frecuencia | Media. Varias señales al mes por activo, según la volatilidad. |
| Automatizar | Baja |
| Capital | Media |
| Pantalla | Baja |
| Alpaca | Alta. Mecánica y fácil de probar en paper sobre ETFs o acciones líquidas. |
| Sonnet / Python | Alta |
| Perfil | Reversión · Automatizar baja · Alpaca alta · Sonnet/Python alta |
| Mercado y timeframe | Acciones líquidas, índices y, con más cuidado, cripto. Diario o 4 horas. Diario o 4 horas. Varias señales al mes por activo, según la volatilidad. |

#### Riesgos y trampas típicas

En una tendencia fuerte las bandas 'caminan' y la reversión no llega. Los parámetros 20 y 2 se optimizan en exceso. Las comisiones importan si operas a menudo.

#### Qué dice la evidencia (insuficiente)

John Bollinger creó las bandas como herramienta descriptiva. No hay un paper académico de referencia que demuestre una prima persistente y explotable, después de costes, para la regla simple de 'comprar la banda inferior'.

_Sin enlaces en la ficha._

### 12. Swing en pullbacks
**Evidencia:** Insuficiente

Operar a favor de la tendencia, pero entrando en un retroceso (un pullback), no en la ruptura eufórica.

| Campo | Valor |
| --- | --- |
| Familia | Tendencia |
| Etiqueta | Tendencia |
| Entrada | El precio está por encima de su media de 200 días. Se espera un retroceso a la media de 20 días o a una zona de soporte, y se compra si el precio aguanta y retoma la dirección. Si la 'vela de giro' no se define al milímetro, la regla deja de ser mecánica. |
| Salida | Un objetivo en el máximo previo, un trailing por debajo de mínimos de swing, o un múltiplo del riesgo (por ejemplo, dos veces lo que arriesgas). |
| Stop | Debajo del mínimo del retroceso, o a 1–2 veces el ATR. |
| Mercado | Acciones, ETFs y cripto. Operaciones que duran días. |
| Timeframe | Diario o 4 horas |
| Frecuencia | Baja. Unas pocas operaciones al mes por activo. |
| Automatizar | Media |
| Capital | Media |
| Pantalla | Media |
| Alpaca | Alta. Viable en Alpaca si la entrada queda 100 % escrita. Si hay criterio humano, ya no es un manual para Sonnet. |
| Sonnet / Python | Media |
| Perfil | Tendencia · Automatizar media · Alpaca alta · Sonnet/Python media |
| Mercado y timeframe | Acciones, ETFs y cripto. Operaciones que duran días. Diario o 4 horas. Unas pocas operaciones al mes por activo. |

#### Riesgos y trampas típicas

Si la regla no está escrita con precisión, cada persona o cada modelo la interpreta distinto y no se puede backtestear. El retroceso puede convertirse en un cambio de tendencia.

#### Qué dice la evidencia (insuficiente)

Es una forma práctica de entrar en seguimiento de tendencia, no una anomalía con un estudio clásico propio. La evidencia útil es la de tendencia y momentum, no un paper de esta receta exacta.

_Sin enlaces en la ficha._

### 13. Pairs trading
**Evidencia:** Mixta

Dos acciones que suelen moverse juntas se separan: compras la que se ha quedado atrás y vendes corto la que se ha adelantado, apostando a que se reencuentran.

| Campo | Valor |
| --- | --- |
| Familia | Estadístico |
| Etiqueta | Estadístico |
| Entrada | Receta de Gatev y coautores: emparejar acciones por la menor distancia entre sus precios normalizados en un periodo de formación (por ejemplo, 12 meses). Operar cuando la diferencia (el spread) supera dos desviaciones típicas históricas. |
| Salida | Cuando el spread vuelve a la media, al final de una ventana (por ejemplo, 6 meses), o si se dispara demasiado. |
| Stop | Un límite de pérdida en el spread. A veces la relación se rompe de verdad (fusión, fraude, cambio de negocio). |
| Mercado | Pares de acciones del mismo sector, muy líquidas. Diario. |
| Timeframe | Diario |
| Frecuencia | Media. Varias operaciones al año por par, con dos patas cada vez. |
| Automatizar | Alta |
| Capital | Alta |
| Pantalla | Media |
| Alpaca | Media. El paper de Alpaca permite vender corto acciones, pero ejecutar las dos patas a la vez y, en real, conseguir el préstamo de títulos es otro problema. |
| Sonnet / Python | Baja |
| Perfil | Estadístico · Automatizar alta · Alpaca media · Sonnet/Python baja |
| Mercado y timeframe | Pares de acciones del mismo sector, muy líquidas. Diario. Diario. Varias operaciones al año por par, con dos patas cada vez. |

#### Riesgos y trampas típicas

La correlación se rompe. Hay costes del corto. Es fácil usar sin querer datos futuros al elegir los pares. No es una estrategia de baja complejidad ni de poco capital.

#### Qué dice la evidencia (mixta)

Gatev, Goetzmann y Rouwenhorst (2006, Review of Financial Studies) documentan que una regla simple de pares fue rentable en acciones de EE. UU. en una muestra que llega hasta 2002, incluso tras estimaciones conservadoras de costes en su estudio. Trabajos posteriores encuentran que la ventaja se ha reducido y es muy sensible a los costes reales.

- [Gatev, Goetzmann y Rouwenhorst, 2006, Review of Financial Studies](https://doi.org/10.1093/rfs/hhj020)

### 14. PEAD (deriva después de resultados)
**Evidencia:** Sólida

Después de unos resultados mejores o peores de lo esperado, el precio suele seguir moviéndose en esa dirección durante días o semanas, no se ajusta del todo el mismo día.

| Campo | Valor |
| --- | --- |
| Familia | Momentum |
| Etiqueta | Momentum |
| Entrada | Tras una sorpresa positiva de beneficios (el dato publicado supera lo que esperaba el consenso de analistas), comprar y mantener unos días o hasta unos 60 días. Lo contrario, con cortos, en sorpresas negativas. |
| Salida | Un horizonte fijo (1 a 60 días) o una regla de salida cuando el movimiento se agota. |
| Stop | Un stop porcentual o de ATR, porque a veces la reacción del día siguiente se da la vuelta. |
| Mercado | Acciones de EE. UU. con cobertura de analistas, en las temporadas de resultados (earnings). |
| Timeframe | Días o semanas alrededor de la fecha de resultados |
| Frecuencia | Media. Oleadas en temporada de resultados. |
| Automatizar | Media |
| Capital | Media |
| Pantalla | Media |
| Alpaca | Media. Puedes operar las acciones en Alpaca, pero el dato de 'sorpresa' frente al consenso no lo da el bróker por sí solo. |
| Sonnet / Python | Media |
| Perfil | Momentum · Automatizar media · Alpaca media · Sonnet/Python media |
| Mercado y timeframe | Acciones de EE. UU. con cobertura de analistas, en las temporadas de resultados (earnings). Días o semanas alrededor de la fecha de resultados. Oleadas en temporada de resultados. |

#### Riesgos y trampas típicas

El efecto puede haberse reducido al ser muy conocido. Hay gaps de apertura, costes y el riesgo de medir mal el consenso. En temporada de resultados no encaja con 'poco tiempo de pantalla'.

#### Qué dice la evidencia (sólida)

Bernard y Thomas (1989, Journal of Accounting Research) documentan el post-earnings-announcement drift y argumentan que encaja mejor con una reacción lenta al dato que con una prima de riesgo. Eso no prueba que un particular, hoy, con comisiones y con datos retrasados, vaya a capturarlo.

- [Bernard y Thomas, 1989, Journal of Accounting Research](https://doi.org/10.2307/2491062)

### 15. Carry / funding en cripto
**Evidencia:** Sólida

Cobrar el extra que paga el mercado por mantener una posición: en cripto, a menudo comprar el spot y vender el futuro o el perpetuo para intentar quedarse cubierto y cobrar esa diferencia (el carry o el funding).

| Campo | Valor |
| --- | --- |
| Familia | Carry |
| Etiqueta | Carry |
| Entrada | Cuando el carry —la base entre futuro y spot, o el funding de los perpetuos— es claramente positivo después de costes y de margen. |
| Salida | Cuando el carry se estrecha, se vuelve negativo, o hay que reducir riesgo de margen. |
| Stop | No es un trade direccional, pero una liquidación o un desajuste entre las dos patas puede hacer mucho daño. Hace falta un límite de margen y de desviación entre spot y futuro. |
| Mercado | BTC y ETH en bolsas con futuros o perpetuos. No es el producto spot de Alpaca. |
| Timeframe | Continuo, con revisiones diarias o en cada funding |
| Frecuencia | Baja. Pocas 'señales', pero hay que vigilar el margen. |
| Automatizar | Media |
| Capital | Alta |
| Pantalla | Media |
| Alpaca | No encaja. Alpaca paper es spot de cripto y acciones, no futuros perpetuos con funding. Esta receta, tal cual, no es el experimento de Alpaca. |
| Sonnet / Python | Media |
| Perfil | Carry · Automatizar media · Alpaca no encaja · Sonnet/Python media |
| Mercado y timeframe | BTC y ETH en bolsas con futuros o perpetuos. No es el producto spot de Alpaca. Continuo, con revisiones diarias o en cada funding. Pocas 'señales', pero hay que vigilar el margen. |

#### Riesgos y trampas típicas

No es dinero gratis: subidas de margen, liquidaciones, inversión del carry, riesgo de la plataforma y de ejecución. Un carry alto ha coincidido históricamente con fases de euforia y luego caídas.

#### Qué dice la evidencia (sólida)

Schmeling, Schrimpf y Todorov, en 'Crypto Carry' (BIS Working Paper; después en Management Science), documentan que el carry de los futuros cripto puede ser muy grande —en su trabajo, de media por encima del 10 % anual y en picos hasta el 60 % anual— y muy variable. Lo atribuyen sobre todo a un convenience yield volátil: demanda apalancada de inversores pequeños en momentos alcistas y escasez de capital de arbitraje. En su estudio, un carry alto predice caídas posteriores del precio. No es una renta segura.

- [Schmeling, Schrimpf y Todorov, Crypto Carry (BIS)](https://www.bis.org/publications/working-paper-1087-crypto-carry)

### 16. Ruptura del rango de apertura (ORB)
**Evidencia:** Débil

La primera media hora (u otro rango corto tras la apertura) define un techo y un suelo; si el precio lo rompe, se entra en esa dirección, a menudo hasta el cierre.

| Campo | Valor |
| --- | --- |
| Familia | Intradía |
| Etiqueta | Intradía |
| Entrada | En acciones o futuros de EE. UU., se miden el máximo y el mínimo de los primeros 15–30 minutos. Se compra una ruptura al alza o se vende una ruptura a la baja. |
| Salida | Al cierre de la sesión, un objetivo (una extensión del rango), o si el precio vuelve dentro del rango (falsa ruptura). |
| Stop | Al otro lado del rango de apertura, o un múltiplo corto del ATR de 1 a 5 minutos. |
| Mercado | Índices y acciones muy líquidos, en el horario de Nueva York. |
| Timeframe | Minutos, intradía |
| Frecuencia | Alta. Casi cada sesión si hay señal. |
| Automatizar | Media |
| Capital | Media |
| Pantalla | Alta |
| Alpaca | Media. Se puede probar en paper. En real, en EE. UU., repetir day trades puede chocar con la regla PDT (Pattern Day Trader: 4 o más day trades en 5 días hábiles suelen exigir 25.000 $ en una cuenta de margen). Además, la apertura de Nueva York es hacia las 15:30 hora de Madrid. |
| Sonnet / Python | Media |
| Perfil | Intradía · Automatizar media · Alpaca media · Sonnet/Python media |
| Mercado y timeframe | Índices y acciones muy líquidos, en el horario de Nueva York. Minutos, intradía. Casi cada sesión si hay señal. |

#### Riesgos y trampas típicas

Comisiones y slippage se comen un margen ya estrecho. Hay muchas rupturas falsas. No encaja con poco tiempo de pantalla. Es fácil sobreajustar el número de minutos del rango.

#### Qué dice la evidencia (débil)

Holmberg, Lönnbark y Lundström (2013, Finance Research Letters) encuentran rentabilidad en una versión sobre futuros de petróleo, pero los resultados no son robustos en todos los subperiodos y dependen de las fases más volátiles. No hay evidencia académica sólida y estable de que el ORB, después de costes reales, sea una ventaja duradera para un particular.

- [Holmberg, Lönnbark y Lundström, 2013, Finance Research Letters](https://doi.org/10.1016/j.frl.2012.09.001)

### 17. VWAP (precio medio ponderado por volumen)
**Evidencia:** Insuficiente

El VWAP es el precio promedio del día ponderado por volumen. Las instituciones lo usan sobre todo para ejecutar órdenes grandes. Como 'estrategia', algunos compran por debajo y venden por encima.

| Campo | Valor |
| --- | --- |
| Familia | Intradía |
| Etiqueta | Intradía |
| Entrada | Versión retail habitual: el precio cruza por encima del VWAP con volumen, o se compra un retroceso al VWAP en una tendencia alcista intradía. |
| Salida | Al cierre, o cuando el precio se aleja y vuelve en contra del VWAP. |
| Stop | Al otro lado del VWAP, o un stop corto intradía. |
| Mercado | Acciones e índices líquidos, en la sesión de EE. UU. |
| Timeframe | Intradía, minutos |
| Frecuencia | Alta. Varias decisiones por sesión. |
| Automatizar | Media |
| Capital | Media |
| Pantalla | Alta |
| Alpaca | Media. Se puede calcular e intentar en paper, pero el relleno real intradía no es el del backtest. |
| Sonnet / Python | Media |
| Perfil | Intradía · Automatizar media · Alpaca media · Sonnet/Python media |
| Mercado y timeframe | Acciones e índices líquidos, en la sesión de EE. UU. Intradía, minutos. Varias decisiones por sesión. |

#### Riesgos y trampas típicas

Confundir una herramienta de ejecución con una fuente de ventaja. Costes. El VWAP del día usa datos de ese mismo día: hay que calcularlo en tiempo real, sin 'mirar' el cierre futuro.

#### Qué dice la evidencia (insuficiente)

El VWAP es un estándar de ejecución institucional. No hay un cuerpo académico sólido que demuestre que 'comprar bajo el VWAP y vender encima' genere, de forma persistente y tras costes, un exceso de rentabilidad para un particular.

_Sin enlaces en la ficha._

### 18. Grid trading
**Evidencia:** Insuficiente

Colocar una rejilla de compras y ventas a intervalos fijos de precio, para ir comprando más abajo y vendiendo más arriba mientras el mercado va y viene.

| Campo | Valor |
| --- | --- |
| Familia | Reversión |
| Etiqueta | Reversión |
| Entrada | Cada vez que el precio cae un escalón (por ejemplo, un 1 %), compras. Cada vez que sube un escalón, vendes una parte. |
| Salida | Tomas de beneficio en el escalón contrario. A veces un cierre total si la tendencia se va demasiado lejos. |
| Stop | Muchos grids no tienen un stop claro, y ese es el problema: en una caída continua vas acumulando inventario. |
| Mercado | Muy popular en cripto, que cotiza 24/7. También se intenta en pares laterales. |
| Timeframe | Intradía o swing corto |
| Frecuencia | Alta. Muchas órdenes pequeñas. |
| Automatizar | Baja |
| Capital | Media |
| Pantalla | Media |
| Alpaca | Media. Se pueden poner órdenes en cripto spot, pero no es lo mismo que los bots de exchanges con futuros. |
| Sonnet / Python | Media |
| Perfil | Reversión · Automatizar baja · Alpaca media · Sonnet/Python media |
| Mercado y timeframe | Muy popular en cripto, que cotiza 24/7. También se intenta en pares laterales. Intradía o swing corto. Muchas órdenes pequeñas. |

#### Riesgos y trampas típicas

Una tendencia fuerte, sobre todo a la baja, convierte el grid en una pérdida grande y lenta. Hay muchas comisiones. En un backtest de mercado lateral parece que 'gana siempre'.

#### Qué dice la evidencia (insuficiente)

Es una receta popular de bots, no una anomalía documentada de forma comparable a momentum o PEAD. No hay un paper de referencia que establezca una prima persistente del grid.

_Sin enlaces en la ficha._

### 19. Scalping
**Evidencia:** Débil

Buscar movimientos muy pequeños, muchas veces al día, y salir en minutos o segundos.

| Campo | Valor |
| --- | --- |
| Familia | Intradía |
| Etiqueta | Intradía |
| Entrada | Micro-rupturas, desequilibrios del libro de órdenes, cruces de medias en velas de 1 minuto… Las recetas varían muchísimo y casi nunca están bien especificadas. |
| Salida | Unos pocos ticks o céntimos de beneficio, o salida rápida si el precio no se mueve. |
| Stop | Muy ajustado. Un solo error, o un hueco en el precio, puede comerse muchas ganancias pequeñas. |
| Mercado | Solo los mercados más líquidos (futuros de índices, grandes acciones). |
| Timeframe | Segundos a minutos |
| Frecuencia | Alta. Decenas o cientos de operaciones. |
| Automatizar | Alta |
| Capital | Alta |
| Pantalla | Alta |
| Alpaca | Baja. La API existe, pero el paper de Alpaca no reproduce la cola, la latencia ni el libro de órdenes reales. |
| Sonnet / Python | Baja |
| Perfil | Intradía · Automatizar alta · Alpaca baja · Sonnet/Python baja |
| Mercado y timeframe | Solo los mercados más líquidos (futuros de índices, grandes acciones). Segundos a minutos. Decenas o cientos de operaciones. |

#### Riesgos y trampas típicas

Costes, velocidad, sobreconfianza y agotamiento. Es lo contrario de lo que buscáis: poco tiempo, poco capital y reglas simples que luego ejecute un modelo barato o un script.

#### Qué dice la evidencia (débil)

La evidencia, para el particular típico, va en contra. Barber y Odean (2000, Journal of Finance), con 66.465 hogares en 1991–1996, encuentran que los que más operaban obtuvieron un 11,4 % anual neto frente al 17,9 % del mercado; el mensaje del paper es que operar mucho resta patrimonio, sobre todo por costes. Barber, Lee, Liu y Odean, con datos de day traders de Taiwán, encuentran que la gran mayoría pierde dinero después de comisiones; solo una minoría muy pequeña es consistentemente rentable.

- [Barber y Odean, 2000, Journal of Finance](https://faculty.haas.berkeley.edu/odean/Papers%20current%20versions/Individual_Investor_Performance_Final.pdf)
- [Barber, Lee, Liu y Odean, Do Individual Day Traders Make Money? Evidence from Taiwan](https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trade%20040330.pdf)

### 20. Covered calls y The Wheel
**Evidencia:** Mixta

Cobrar una prima vendiendo opciones sobre acciones que ya tienes (o que estás dispuesto a tener), a costa de recortar las subidas.

| Campo | Valor |
| --- | --- |
| Familia | Opciones |
| Etiqueta | Opciones |
| Entrada | Covered call: si ya tienes 100 acciones, vendes una opción de compra (call) y cobras la prima. The Wheel: primero vendes puts (te comprometes a comprar si el precio cae) y, si te asignan las acciones, pasas a vender calls cubiertas, en ciclo. |
| Salida | Dejar que la opción expire, recomprarla, o 'enrollarla' a otra fecha. Si hay asignación, entregas (o te quedan) las acciones al precio de ejercicio. |
| Stop | Las opciones complican el stop. El riesgo de verdad es que la acción caiga: sigues expuesto a la baja y has recortado la subida. |
| Mercado | Acciones y ETFs de EE. UU. con opciones líquidas. Horizontes de semanas. |
| Timeframe | Semanas (por ejemplo, 30–45 días) |
| Frecuencia | Baja. Una o dos decisiones al mes por posición. |
| Automatizar | Media |
| Capital | Alta |
| Pantalla | Media |
| Alpaca | Media. Alpaca permite opciones en paper, pero hay que entender asignación, vencimientos y, en real, las aprobaciones del bróker. No es el primer experimento si aún no hay capital. |
| Sonnet / Python | Media |
| Perfil | Opciones · Automatizar media · Alpaca media · Sonnet/Python media |
| Mercado y timeframe | Acciones y ETFs de EE. UU. con opciones líquidas. Horizontes de semanas. Semanas (por ejemplo, 30–45 días). Una o dos decisiones al mes por posición. |

#### Riesgos y trampas típicas

No es ingreso pasivo gratis. Limitas la subida y sigues sufriendo las caídas. En un mercado alcista fuerte te quedas corto frente a solo mantener. En un crash, la prima no te salva.

#### Qué dice la evidencia (mixta)

Israelov y Nielsen (2014, Financial Analysts Journal) explican que una covered call es, en esencia, estar largo del activo y corto de volatilidad. Desmontan mitos habituales: que 'protegen a la baja', que son solo 'generar renta' o que equivalen a comprar más barato. Pueden reducir la volatilidad frente a solo tener el índice, a costa de recortar las subidas. No es magia.

- [Israelov y Nielsen, 2014, Financial Analysts Journal (AQR)](https://www.aqr.com/Insights/Research/Journal-Article/Covered-Call-Strategies-One-Fact-and-Eight-Myths)

### 21. Copy trading (referencia, no es una estrategia propia) · Referencia
**Evidencia:** Débil

Unir tu cuenta a la de un 'líder' para que se copien sus órdenes.

| Campo | Valor |
| --- | --- |
| Familia | Social |
| Etiqueta | Referencia |
| Entrada | Las del líder, con retraso y, a menudo, un tamaño distinto. |
| Salida | Las del líder, o cuando tú cortas la copia. |
| Stop | El del líder, si es que lo tiene. Tú no controlas la regla. |
| Mercado | Plataformas de copy trading. No es el flujo nativo de Alpaca + Claude Code. |
| Timeframe | El del líder |
| Frecuencia | Media. La que tenga el líder, más el retraso de la copia. |
| Automatizar | Baja |
| Capital | Media |
| Pantalla | Baja |
| Alpaca | No encaja. Alpaca no es una plataforma de copy trading nativo. Este no es el experimento de paper que encaja con Fable escribiendo reglas. |
| Sonnet / Python | Baja |
| Perfil | Social · Automatizar baja · Alpaca no encaja · Sonnet/Python baja |
| Mercado y timeframe | Plataformas de copy trading. No es el flujo nativo de Alpaca + Claude Code. El del líder. La que tenga el líder, más el retraso de la copia. |

#### Riesgos y trampas típicas

Eliges al líder con sesgo de supervivencia: ves a los que ya les fue bien. Hay retraso, comisiones, cambios de estilo, apalancamiento ajeno y menos aprendizaje propio.

#### Qué dice la evidencia (débil)

No hay evidencia sólida de que copiar a 'los mejores' de una plataforma produzca, de media, buenos resultados para el seguidor. Heimer (2016, Review of Financial Studies) encuentra que el acceso a una red social de trading casi duplica el disposition effect: la tendencia a vender ganadores y aguantar perdedores. El copy puede valer, como mucho, para observar con muy poco tamaño; no es un plan para 'inventar dinero' ni una regla que Fable pueda dejar escrita y que Sonnet ejecute.

- [Heimer, 2016, Review of Financial Studies](https://doi.org/10.1093/rfs/hhw063)

## Trampas generales

Da igual la estrategia que elijáis: un backtest mal hecho puede hacer que una regla inútil parezca una máquina de dinero. Estas cuatro trampas son las que más distorsionan.

### Sobreajuste (overfitting)

Overfitting es ajustar tanto la regla a los datos del pasado que luego no funciona en datos nuevos. Si pruebas cientos de combinaciones (medias de 17 y 43 días, RSI a 6, stop a 1,7 ATR…) y te quedas con la que 'mejor' salió, es muy probable que hayas cazado ruido. Bailey, Borwein, López de Prado y Zhu, en 'The Probability of Backtest Overfitting', formalizan precisamente ese riesgo: la probabilidad de que la estrategia elegida como mejor en la muestra acabe por debajo de la mediana fuera de la muestra.

### Look-ahead bias (usar el futuro sin querer)

Look-ahead bias es diseñar o ejecutar la regla con información que, en ese momento, todavía no existía. Ejemplos típicos: usar el cierre del día para una entrada que se habría dado por la mañana; incluir en 2019 una acción que no cotizó hasta 2021; calcular una media o el VWAP del día entero para decidir a media sesión; elegir los pares de un pairs trade mirando todo el historial. Si Fable escribe código, esta es la primera cosa que hay que auditar.

### Comisiones y slippage

Una estrategia puede parecer ganadora a coste cero y quedarse plana o perdedora cuando sumas comisiones, el spread (la diferencia entre compra y venta) y el slippage. Eso pega especialmente a las que operan mucho: reversión de corto plazo, grid, ORB, scalping. Barber y Odean (2000) muestran que, en su muestra de particulares, el problema no era tanto 'elegir mal las acciones' como operar demasiado y pagar por ello. Un backtest honesto tiene que incluir costes pesimistas, no optimistas.

### Sesgo de supervivencia (survivorship bias)

Si solo pruebas la estrategia sobre las acciones o los 'líderes' de copy trading que siguen existiendo hoy, estás ignorando a los que quebraron, se delistaron o desaparecieron. El resultado queda demasiado bonito. Shumway (1997) documentó que omitir las rentabilidades de salida de bolsa (sobre todo por mal desempeño) sesga los estudios a la alta. El remedio es un universo punto a punto en el tiempo, con las bajas incluidas.

Otras trampas menores, igual de reales: el paper trading de Alpaca no es el mercado real (los rellenos, las colas y las comisiones pueden ser distintos). Una semana, o incluso un mes, es demasiado poco para declarar ganador a nadie. Y un modelo de lenguaje gastando cupo cada hora no es un operador de baja latencia.

## Mi shortlist para probar con Fable

Cinco candidatas, no porque vayan a 'imprimir dinero', sino porque son reglas escritas, se pueden backtestear, operan poco y encajan en Alpaca paper. Fable debería compararlas todas con comprar y mantener, con comisiones y slippage incluidos, y entregar un STRATEGY.md más un script de señales que luego pueda correr Sonnet o Python, sin intuición.

> **El orden que yo probaría**
>
> Primero el listón (comprar y mantener). Luego las tres reglas mensuales (Faber, momentum de 12 meses y dual momentum), que piden muy poco tiempo de pantalla. Por último, la ruptura Donchian en diario o 4 horas, que es más 'trading' y sigue siendo 100 % mecánica, con un riesgo máximo del 1 % por operación.

### 1. Comprar y mantener + rebalanceo

**Shortlist**

Comprar un índice amplio (o un puñado de ETFs) y dejarlo trabajar, reequilibrando de vez en cuando.

Por qué está aquí: no es la estrategia 'inteligente', es el rival. Si Fable no puede demostrarle una ventaja después de costes, no habéis encontrado nada. Además es la más simple de ejecutar el día que haya capital pequeño.

### 4. Asignación táctica de Faber (media de 10 meses)

**Shortlist**

Estar invertido en un activo solo cuando su precio mensual cierra por encima de su media de 10 meses; si no, efectivo.

Por qué está aquí: una sola regla mensual, publicada y fácil de auditar. Encaja con poco tiempo de pantalla, con ETFs de Alpaca y con un script tonto. El matiz: el paper original no incluye costes; Fable tiene que ponerlos.

### 5. Ruptura Donchian / Turtle

**Shortlist**

Comprar cuando el precio rompe el máximo de N días y salir cuando rompe un mínimo reciente.

Por qué está aquí: es la candidata más 'trader' sin pasarse a intradía. Reglas concretas de entrada, salida y stop, con tamaño por volatilidad y 1 % de riesgo. Funciona en un ETF y en BTC/ETH. No hay que copiar el apalancamiento de los Turtles originales.

### 6. Momentum de series temporales

**Shortlist**

Si un activo ha subido (respecto al efectivo) en los últimos 12 meses, se mantiene largo el mes siguiente; si ha bajado, se queda fuera o se pone corto.

Por qué está aquí: es la columna académica más sólida del seguimiento de tendencia. Se puede bajar a una versión solo-compras, mensual, sobre uno o unos pocos ETFs y BTC/ETH. Hay que respetar que el paper diversifica muchos futuros, no un solo par.

### 8. Dual momentum

**Shortlist**

Elige el mercado más fuerte (momentum relativo) y solo invierte si también está en tendencia alcista absoluta; si no, te vas a un activo refugio.

Por qué está aquí: es un manual completo de asignación (EE. UU. vs internacional vs refugio) y sigue siendo una decisión al mes. Muy ejecutable por Sonnet. La evidencia es del autor de la receta, así que el backtest independiente importa aún más.

### Lo que yo no pondría a Fable esta semana

Scalping, ORB y VWAP piden horario de Nueva York y se los comen los costes. El grid y el RSI(2) son fáciles de programar, pero la evidencia es floja o frágil tras comisiones. El carry de cripto no vive en Alpaca. Pairs trading y el momentum cruzado de muchas acciones piden más infraestructura y capital. Las opciones son otro oficio. El copy trading no deja un manual de reglas. El volatility targeting sí se puede añadir después, como capa, si alguna regla mensual aguanta el backtest.

## Glosario

Cada término en inglés, en una frase.

| Término | En una frase |
| --- | --- |
| Paper trading | Operar con dinero ficticio, sin riesgo real. |
| Backtest | Probar una regla en datos del pasado. |
| Slippage | Diferencia entre el precio que esperas y el que te dan de verdad. |
| Spread | Diferencia entre el precio de compra y el de venta en un momento dado. |
| Overfitting | Ajustar tanto la regla al pasado que luego falla en el futuro. |
| Look-ahead bias | Usar sin querer datos que, en ese momento, todavía no existían. |
| Survivorship bias | Sesgo de supervivencia: olvidar a los que desaparecieron. |
| Timeframe | El tamaño de cada vela, o el horizonte de la operación. |
| SMA | Media móvil simple: el promedio del precio de las últimas N velas. |
| ATR | Average True Range: una medida del tamaño típico reciente de las velas. |
| RSI | Relative Strength Index: un oscilador de 0 a 100 sobre la fuerza reciente del precio. |
| Stop | Regla u orden para salir si el precio va en contra. |
| Breakout | Ruptura de un máximo o un mínimo reciente. |
| Pullback | Un retroceso temporal dentro de una tendencia. |
| Momentum | Apuesta a que lo que ha subido o bajado sigue un tiempo en esa dirección. |
| Mean reversion | Apuesta a que el precio vuelve hacia su media. |
| Carry / funding | Cobro (o pago) por mantener una posición; en perpetuos cripto, el funding rate. |
| Drawdown | Caída desde un máximo de la curva de capital hasta el mínimo siguiente. |
| ETF | Fondo que cotiza en bolsa y suele seguir un índice. |
| DCA | Dollar-cost averaging: comprar una cantidad fija a intervalos regulares. |
| ORB | Opening range breakout: ruptura del rango de la apertura. |
| VWAP | Volume-weighted average price: precio promedio del día ponderado por volumen. |
| PEAD | Post-earnings-announcement drift: el precio sigue derivando después de los resultados. |
| Covered call | Vender una opción de compra sobre acciones que ya tienes. |
| The Wheel | Ciclo de vender puts y, si te asignan, pasar a vender calls cubiertas. |
| PDT | Pattern Day Trader: en EE. UU., varios day trades en cinco días pueden exigir 25.000 $ reales. |
| Long-only | Solo compras; no vendes en corto. |

## Fuentes

Solo cito trabajos que he podido verificar. Si no había evidencia sólida, lo digo en la ficha en vez de inventar un porcentaje. Daniel y Moskowitz (2016), Momentum Crashes, Journal of Financial Economics, se cita en la ficha de momentum cruzado; no enlazo un PDF que no haya abierto en esta investigación.

- [Moskowitz, Ooi y Pedersen, 2012, Time Series Momentum, Journal of Financial Economics](https://www.sciencedirect.com/science/article/pii/S0304405X11002613)
- [Jegadeesh y Titman, 1993, Returns to Buying Winners and Selling Losers, Journal of Finance](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x)
- [Asness, Moskowitz y Pedersen, 2013, Value and Momentum Everywhere, Journal of Finance](https://doi.org/10.1111/jofi.12021)
- [Hurst, Ooi y Pedersen, 2017, A Century of Evidence on Trend-Following Investing, Journal of Portfolio Management](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing)
- [Faber, 2007, A Quantitative Approach to Tactical Asset Allocation, Journal of Wealth Management](https://ssrn.com/abstract=962461)
- [Antonacci, Risk Premia Harvesting Through Dual Momentum](https://ssrn.com/abstract=2042750)
- [Brock, Lakonishok y LeBaron, 1992, Simple Technical Trading Rules, Journal of Finance](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x)
- [Sullivan, Timmermann y White, 1999, Data-Snooping, Technical Trading Rule Performance, and the Bootstrap, Journal of Finance](https://doi.org/10.1111/0022-1082.00163)
- [Gatev, Goetzmann y Rouwenhorst, 2006, Pairs Trading, Review of Financial Studies](https://doi.org/10.1093/rfs/hhj020)
- [Bernard y Thomas, 1989, Post-Earnings-Announcement Drift, Journal of Accounting Research](https://doi.org/10.2307/2491062)
- [Moreira y Muir, 2017, Volatility-Managed Portfolios, Journal of Finance](https://doi.org/10.1111/jofi.12513)
- [Cederburg, O'Doherty, Wang y Yan, 2020, On the Performance of Volatility-Managed Portfolios, Journal of Financial Economics](https://doi.org/10.1016/j.jfineco.2020.04.015)
- [Barber y Odean, 2000, Trading Is Hazardous to Your Wealth, Journal of Finance](https://faculty.haas.berkeley.edu/odean/Papers%20current%20versions/Individual_Investor_Performance_Final.pdf)
- [Barber, Lee, Liu y Odean, Do Individual Day Traders Make Money? Evidence from Taiwan](https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trade%20040330.pdf)
- [Schmeling, Schrimpf y Todorov, Crypto Carry, BIS / Management Science](https://www.bis.org/publications/working-paper-1087-crypto-carry)
- [Liu y Tsyvinski, 2021, Risks and Returns of Cryptocurrency, Review of Financial Studies](https://doi.org/10.1093/rfs/hhaa113)
- [Israelov y Nielsen, 2014, Covered Call Strategies: One Fact and Eight Myths, Financial Analysts Journal](https://www.aqr.com/Insights/Research/Journal-Article/Covered-Call-Strategies-One-Fact-and-Eight-Myths)
- [Heimer, 2016, Peer Pressure: Social Interaction and the Disposition Effect, Review of Financial Studies](https://doi.org/10.1093/rfs/hhw063)
- [Holmberg, Lönnbark y Lundström, 2013, Assessing the Profitability of Intraday Opening Range Breakout Strategies, Finance Research Letters](https://doi.org/10.1016/j.frl.2012.09.001)
- [Bailey, Borwein, López de Prado y Zhu, The Probability of Backtest Overfitting](https://ssrn.com/abstract=2326253)
- [Shumway, 1997, The Delisting Bias in CRSP Data](https://www.tylergshumway.org/Shumway-DelistingBiasCRSP-1997.pdf)
- [Vanguard, Cost averaging: Invest now or temporarily hold your cash?](https://corporate.vanguard.com/content/dam/corp/research/pdf/cost_averaging_invest_now_or_temporarily_hold_your_cash.pdf)

Preparado el 11 de noviembre de 2026, hora de Madrid. Educativo, no es asesoramiento financiero. La rentabilidad pasada no garantiza resultados futuros.
