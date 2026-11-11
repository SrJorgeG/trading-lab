"""Baja y cachea el universo de config/settings.toml y muestra un resumen."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.config import ROOT, load_settings  # noqa: E402
from tlab.data.loader import load_bars, pick_source  # noqa: E402
from tlab.data.validate import validate_bars  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=None, help="auto | alpaca | yfinance")
    ap.add_argument("--start", default=None)
    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    s = load_settings()
    src = pick_source(args.source or s["data"]["source"])
    start = args.start or (
        s["data"]["history_start"] if src.name == "yfinance" else s["data"]["equity_start"]
    )
    print(f"Fuente: {src.name} (desde {start})")
    print(f"{'símbolo':10} {'primera':12} {'última':12} {'velas':>6}  avisos")
    for ac in ("equity", "crypto"):
        syms = s["universe"][ac]
        data = load_bars(
            syms,
            "1Day",
            start=start,
            source=src,
            cache_dir=ROOT / s["data"]["cache_dir"],
            asset_class=ac,
        )
        for sym, df in data.items():
            if df.empty:
                print(f"{sym:10} SIN DATOS")
                continue
            issues = "; ".join(validate_bars(df, ac)) or "-"
            print(
                f"{sym:10} {df.index[0].date()!s:12} {df.index[-1].date()!s:12} "
                f"{len(df):>6}  {issues}"
            )


if __name__ == "__main__":
    main()
