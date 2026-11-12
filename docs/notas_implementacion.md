# Notas de implementación (ronda 2) — decisiones donde la especificación era ambigua

Regla aplicada: ante la duda, la opción más conservadora. Una línea por duda.

| Tarea | Duda | Opción tomada |
|---|---|---|
| R2-9 | `window` figura en la especificación, pero H6 está aparcada (E15) | No implementado. `MODES = ("rank", "persist")`; pedir `window` da `ValueError` (test). |
| R2-9 | Cualquier tramo para el script de monos | Solo `is` y `replica`; `holdout_*` y `full` → `TrancheGuardError`. En `replica` exige `--confirm-tranche`, congelada y la base de la réplica ya ejecutada. |
| R2-9 | Mono sin Sharpe (sin operaciones) | Cuenta en n y como «no supera» (D7): `p = (1 + k)/(n + 1)`. No se usa `empirical_p`. |
| R2-9 | `run_custom_monkeys` con `entry_delay != 0` | `ValueError`: los monos se ejecutan con retraso 0. |
| R2-10 | `criterion_17` con relación del benchmark no definida (NaN, p. ej. caída 0 y CAGR ≤ 0) | `False` (no se concede la casilla sin una cifra clara). |
| R2-10 | «Calibración con el límite 0,12» en `checklist("is")` | Se muestra la caída máxima del riesgo usado en la ejecución; la calibración completa sigue saliendo de `candidate_sections` (sin duplicarla). |
| R2-10 | Casillas 5, 6, 7-IS, 8-IS, 10-IS y 14 | No se recalculan en `r2_report`: salen de los modos `wf`/`robust`, de las variantes de costes/retraso y de los monos, como en la ronda 1. |
| R2-10 | Caja en los informes | `run_backtest`/`run_round2` aceptan `cash_rate` (serie ya en base de rentabilidad). Si no se pasa y hay datos reales, se carga con `load_tbill_rate`; en tests sintéticos, sin serie, el informe dice «Caja no disponible». |
| R2-10 | Monte Carlo agrupado por meses de `tom_etf` | No se enlaza al informe (H6 aparcada). La función `monte_carlo_dd_grouped` existe y está probada (ME14), pero no se usa. |
| R2-10 | Walk-forward informativo con parámetros por defecto en las 8 ventanas | Lo da el modo `wf` existente (`wf_fixed_section`); no se ha añadido nada nuevo. |
| R2-10 | 16a si falta el informe base de `holdout_old` | `g_old = None` → fila «no calculable» (ME16). |
| R2-11 | Bloques de la banda | El sorteo es bloque a bloque para que la banda corta y la conjunta coincidan exactamente (B6). |
| R2-19 | Potencia sintético: número de series y de monos | 40 series por escenario y 99 monos (p mínimo 0,01): con 1.000 monos por serie el tiempo no es razonable. El criterio 14 se evalúa con p < 0,02 sobre 99 monos; es una aproximación, anotada en `reports/potencia/potencia.md`. |
| R2-19 | Qué es «ventaja conocida» | Deriva diaria persistente por activo (OU, memoria ≈ 100 sesiones, sd diaria 0,0004). Es una elección mía: el informe es informativo y no cambia ningún criterio. |
| R2-8, R2-12, R2-15 | H6 aparcada (E15) | No se hacen. No se ha borrado nada existente. |
| R2-18 | No estaba en la lista de esta sesión y requiere descarga y red | No hecho en esta sesión. |
| General | Prohibido ejecutar backtests de H5–H7 con datos reales | No se ha ejecutado ninguno; los tests y el test de potencia usan solo datos sintéticos. |
