"""R2-19: test de potencia sintético (sin datos reales). Escribe reports/potencia/.

    uv run python scripts/power_test_r2.py --n-series 100 --edge 0.0004

Informativo: no cambia ningún criterio. Semilla 42.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.backtest.power_test import pass_rates, run_power  # noqa: E402
from tlab.config import ROOT, load_settings  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-series", type=int, default=100)
    ap.add_argument("--n-monkeys", type=int, default=99)
    ap.add_argument("--edge", type=float, default=0.0004, help="sd diaria de la deriva persistente")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(ROOT / "reports" / "potencia"))
    a = ap.parse_args()
    s = load_settings()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Test de potencia sintético (R2-19, E22/A1)",
        "",
        "Series INVENTADAS de 9 activos; ningún dato real. Informativo: no cambia ningún criterio.",
        f"N = {a.n_series} series por escenario, {a.n_monkeys} monos `rank` por serie "
        f"(p mínimo {1 / (a.n_monkeys + 1):.4f}), semilla {a.seed}.",
        "Criterios calculados: 0, 3-IS, 16-IS (caja sintética constante del 3 %), 17-IS "
        "(frente a la media de los 9) y 14. No calculados aquí: 5, 6, 7-IS, 8-IS, 10-IS "
        "y calibración.",
        "",
    ]
    for label, edge in (("sin ventaja", 0.0), ("con ventaja", a.edge)):
        df = run_power(edge, a.n_series, s, a.n_monkeys, a.seed)
        df.to_csv(out / f"series_{label.replace(' ', '_')}.csv", index_label="serie")
        pr = pass_rates(df)
        lines += [
            f"## {label} (sd diaria de la deriva = {edge})",
            "| criterio | frecuencia de «sí» |",
            "|---|---|",
            *[f"| {k} | {v * 100:.1f} % |" for k, v in pr.items()],
            f"\nSharpe medio {df['sharpe'].mean():.3f}; "
            f"CAGR medio {df['cagr'].mean() * 100:.2f} %.\n",
        ]
    (out / "potencia.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"escrito {out / 'potencia.md'}")


if __name__ == "__main__":
    main()
