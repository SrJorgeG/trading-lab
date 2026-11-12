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


def round2_symbols() -> list[str]:
    """Unión de universo, réplica, benchmark y benchmark_info de los TOML de la ronda 2
    que existan, más la renta fija del criterio 16d. Solo nombres: no toca precios."""
    from tlab.config import load_strategy_config
    from tlab.strategies import CANDIDATES_R2

    syms: set[str] = set()
    for sid in CANDIDATES_R2:
        try:
            sc = load_strategy_config(sid)
        except FileNotFoundError:
            continue  # p. ej. tom_etf: H6 aparcada (E15), no tiene TOML
        syms |= set(sc["universe"]) | set(sc.get("replica_universe", []))
        syms |= {sc["benchmark"]} | set(sc.get("benchmark_info", {}))
        if "fixed_income" in sc:
            syms.add(sc["fixed_income"])
    return sorted(syms)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=None, help="auto | alpaca | yfinance")
    ap.add_argument("--start", default=None)
    ap.add_argument(
        "--round2",
        action="store_true",
        help="ronda 2: baja con yfinance (ajustado) desde data.round2.history_start los "
        "símbolos de los TOML de la ronda 2. Solo fechas, nº de velas y avisos.",
    )
    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    s = load_settings()
    if args.round2:
        from tlab.data.yf_source import YFinanceSource

        start = args.start or s["data"]["round2"]["history_start"]
        syms = round2_symbols()
        print(f"Fuente: yfinance (desde {start}); {len(syms)} símbolos")
        print(f"{'símbolo':10} {'primera':12} {'última':12} {'velas':>6}  avisos")
        data = load_bars(
            syms,
            "1Day",
            start=start,
            source=YFinanceSource(),
            cache_dir=ROOT / s["data"]["cache_dir"],
            asset_class="equity",
        )
        for sym, df in data.items():
            if df.empty:
                print(f"{sym:10} SIN DATOS")
                continue
            issues = "; ".join(validate_bars(df, "equity")) or "-"
            print(
                f"{sym:10} {df.index[0].date()!s:12} {df.index[-1].date()!s:12} "
                f"{len(df):>6}  {issues}"
            )
        return
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
