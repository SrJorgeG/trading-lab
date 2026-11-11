"""Backtest de una estrategia: --strategy <id> --mode {is,wf,oos,full,robust}."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.backtest.runner import MODES, run_backtest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--mode", required=True, choices=MODES)
    ap.add_argument("--costs", default="base", choices=["base", "stress"])
    ap.add_argument("--params", default=None, help="TOML con [params] que sobrescriben")
    ap.add_argument("--confirm-oos", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--entry-delay", type=int, default=0, help="velas extra de retraso (estrés)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    p = run_backtest(
        a.strategy, a.mode, a.costs, a.params, a.confirm_oos, a.force, entry_delay=a.entry_delay
    )
    print(f"Informe: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
