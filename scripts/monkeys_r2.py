"""Monos a medida de la ronda 2 (R2-9): `rank` y `persist`. Solo IS y réplica.

    uv run python scripts/monkeys_r2.py --strategy sector_mom --mode rank --tranche is

La réplica exige `--confirm-tranche`. `holdout_*` y `full` se rechazan siempre.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.backtest.monkeys_r2 import run_monkeys_r2  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--mode", required=True, choices=["rank", "persist"])
    ap.add_argument("--tranche", default="is")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--confirm-tranche", action="store_true")
    a = ap.parse_args()
    out = run_monkeys_r2(
        a.strategy, a.mode, a.tranche, a.n, a.seed, confirm_tranche=a.confirm_tranche
    )
    print(f"escrito {out}")


if __name__ == "__main__":
    main()
