# Test de potencia sintético (R2-19, E22/A1)

Series INVENTADAS de 9 activos; ningún dato real. Informativo: no cambia ningún criterio.
N = 40 series por escenario, 99 monos `rank` por serie (p mínimo 0.0100), semilla 42.
Criterios calculados: 0, 3-IS, 16-IS (caja sintética constante del 3 %), 17-IS (frente a la media de los 9) y 14. No calculados aquí: 5, 6, 7-IS, 8-IS, 10-IS y calibración.

## sin ventaja (sd diaria de la deriva = 0.0)
| criterio | frecuencia de «sí» |
|---|---|
| c0 | 100.0 % |
| c3 | 67.5 % |
| c16 | 65.0 % |
| c17 | 25.0 % |
| c14 | 0.0 % |
| todos | 0.0 % |

Sharpe medio 0.561; CAGR medio 5.76 %.

## con ventaja (sd diaria de la deriva = 0.0004)
| criterio | frecuencia de «sí» |
|---|---|
| c0 | 100.0 % |
| c3 | 85.0 % |
| c16 | 82.5 % |
| c17 | 55.0 % |
| c14 | 0.0 % |
| todos | 0.0 % |

Sharpe medio 0.718; CAGR medio 7.75 %.
