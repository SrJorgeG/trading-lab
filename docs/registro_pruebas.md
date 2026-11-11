# Registro de pruebas

| fecha | hipótesis | variante/parámetros | conjunto (IS/WF/OOS) | resultado clave | archivo de informe |
|---|---|---|---|---|---|
| 2026-11-11 01:40 (hora de Madrid) | demo_sma | fast=20, slow=100, atr_mult=2.0, atr_n=14 | full/base | CAGR 0.25 %, Sharpe 0.09, DD -10.3 %, n=25 | reports/demo_sma/full_20261111-0140/resumen.md |
| 2026-11-11 01:40 (hora de Madrid) | donchian_atr | entry_n=20, exit_n=10, atr_mult=2.0, atr_n=20 | is/base | CAGR 4.24 %, Sharpe 0.68, DD -11.7 %, n=20 | reports/donchian_atr/is_20261111-0140/resumen.md |
| 2026-11-11 04:54 (hora de Madrid) | donchian_atr | rejilla=entry_n=10..60 (11) × exit_n=5..30 (6) × atr_mult=1.5..3.5 (5) | sweep-is/base/sin kill switch | N=330 configuraciones; robustez 89/100 en Sharpe (meseta); mejor 1.60 en entry_n=20, exit_n=10, atr_mult=2; PBO 33% | reports/robustez/donchian_atr_nokill/sweep_is_20261111-0454/resumen.md |
| 2026-11-11 04:54 (hora de Madrid) | tsmom_12m (SPY) | rejilla=months=1..24 (24) × skip=0..2 (3) | sweep-is/base | N=72 configuraciones; robustez 97/100 en Sharpe (meseta); mejor 0.67 en months=19, skip=2; PBO 87% | reports/robustez/tsmom_12m_spy/sweep_is_20261111-0454/resumen.md |
| 2026-11-11 04:55 (hora de Madrid) | donchian_atr [benchmark azar, no es variante] | entry_n=20, exit_n=10, atr_mult=2.0, atr_n=20 | azar-is/base/sin kill switch | 1000 monos (semilla 42); Sharpe real 1.60, percentil 97%, p=0.034 → ventaja probable | reports/robustez/donchian_atr_nokill/azar_is_20261111-0455/resumen.md |
| 2026-11-11 04:55 (hora de Madrid) | tsmom_12m (SPY) [benchmark azar, no es variante] | months=12, skip=0 | azar-is/base | 1000 monos (semilla 42); Sharpe real 0.49, percentil 68%, p=0.326 → indistinguible del azar | reports/robustez/tsmom_12m_spy/azar_is_20261111-0455/resumen.md |
