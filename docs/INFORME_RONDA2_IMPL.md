# Informe de implementación — ronda 2 (para Fable)

Rama `ronda2/implementacion`. Sin `push`. Ningún backtest de H5–H7 con datos reales (ni IS ni
OOS): los tests y el test de potencia usan datos sintéticos. `reports/oos_log.csv` no tiene filas
nuevas.

## Tarea → commit → tests

| Tarea | Commit | Tests |
|---|---|---|
| R2-1, R2-2 | `57e6d80` | `tests/test_r2_config.py` |
| R2-3 (solo configuración) | `04c72cb` | `tests/test_r2_config.py` |
| R2-4 | `8cfb103` | `tests/test_r2_cash.py` (CA1–CA7) |
| R2-5 (+E20/E21) | `81629b6`, `7728b3f` | `tests/test_r2_tranches.py` |
| R2-6 | `55baafa` | `tests/test_r2_infra.py`, `tests/test_r2_panel.py` |
| R2-7, R2-14 | `77c04ee` | `tests/test_r2_panel.py`, `tests/test_r2_sim.py` (S1–S13) |
| R2-9, R2-16 | `79aed74`, `48528cb` | `tests/test_r2_monkeys.py` (M1, M3–M7, M11–M14 y script guardado) |
| R2-10, R2-17 | `f89d22c` | `tests/test_r2_metrics.py` (ME1–ME16 y secciones por tramo) |
| R2-11 | `8ee71a5` | `tests/test_r2_paper_band.py` (B1–B6) |
| R2-19 | `6b524e4` + informe | `tests/test_r2_power.py`; resultado en `reports/potencia/potencia.md` |

## Resultado del test de potencia (R2-19; cifras en `reports/potencia/potencia.md`)

Informativo, datos inventados, no cambia ningún criterio. Lo que dice el informe: en ambos
escenarios el criterio 14 sale «sí» en 0 % de las series, también con ventaja conocida
(sd diaria 0,0004), y el criterio 17 en 25 % (sin ventaja) y 55 % (con ventaja). El criterio 0
sale «sí» en 100 % (la deriva común positiva lo hace trivial en sintético). Lectura prudente para
Fable: con esta ventaja sintética y solo 99 monos (p mínimo 0,01) el criterio 14 casi no
discrimina; no sé si es por la ventaja elegida (elección mía) o porque el examen es muy exigente.
No lo he investigado más ni he tocado ningún criterio.

## Dudas de interpretación (una por línea, con la opción tomada)

Ver `docs/notas_implementacion.md`: cada duda lleva la opción conservadora elegida.

## Desviaciones respecto a la especificación

- `window` (R2-9), R2-8, R2-12, R2-15 y el Monte Carlo agrupado en el informe: no hechos por
  E15 (H6 aparcada). `monte_carlo_dd_grouped` existe y está probada (ME14), pero no se enlaza al
  informe.
- R2-19: 40 series por escenario y 99 monos por serie (no 1.000) por tiempo de cálculo.
- R2-10: las casillas 5, 6, 7-IS, 8-IS, 10-IS y 14 no se recalculan en `r2_report`; salen de los
  modos `wf`/`robust`, de las variantes de coste/retraso y de los monos, como en la ronda 1.

## Verificación de datos (R2-3 / R2-18)

No se ha hecho en esta sesión: R2-18 (tabla de primeras velas, saltos > ±20 %, comparación
Alpaca–yfinance, `get_asset`, recuentos de aperturas) y la descarga de datos de R2-3 siguen
pendientes. No hay rutas a `reports/datos/…` nuevas.

## Base de la serie de caja

Tipo de descuento (base 360, letra a 91 días) de `^IRX`, con respaldo `DTB3` de FRED, convertido a
rentabilidad con `y = 365·d / (360 − 91·d)` (enmienda E10; casos CA1–CA7). La fuente real usada
solo se sabrá al descargar (`load_tbill_rate` la devuelve en su segundo valor).

## Lo que NO se ha hecho

- R2-3 (descarga real) y R2-18 completos.
- R2-8, R2-12, R2-15 (H6 aparcada).
- Ninguna ejecución con datos reales; ninguna escritura en `reports/sector_mom`,
  `reports/sector_lowvol` ni `reports/tom_etf`.
- E19 (avance rápido de `main`) y E20 (etiqueta `ronda2/pre-is`): no se tocan sin visto bueno de
  Jorge / Fable.
