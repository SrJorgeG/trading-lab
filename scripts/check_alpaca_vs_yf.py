"""Contraste yfinance ↔ Alpaca de los universos de las candidatas (rentabilidades diarias).

Uso (en el PC con las claves PAPER de Alpaca en .env):
    uv run python scripts/check_alpaca_vs_yf.py
Lee ALPACA_API_KEY / ALPACA_SECRET_KEY del entorno (o de .env). Si no están, avisa y sale con
código 0 sin hacer nada. Las claves nunca se imprimen. Solo lee datos de mercado (no opera).
Escribe reports/datos/contraste_<fecha>.md y .csv. Código de salida 1 si algún activo no cuadra.
Tolerancias y motivo: ver src/tlab/data/crosscheck.py.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from tlab.config import ROOT, asset_class_of, load_settings, load_strategy_config  # noqa: E402
from tlab.data.crosscheck import COMMON_START, compare_returns, results_table  # noqa: E402
from tlab.report import MADRID, now_madrid  # noqa: E402
from tlab.strategies import CANDIDATES  # noqa: E402

END = "2026-10-31"  # fin de datos común pre-registrado (hipotesis.md §3)


def candidate_symbols() -> list[str]:
    syms: set[str] = set()
    for sid in CANDIDATES:
        sc = load_strategy_config(sid)
        syms |= set(sc["universe"]) | {sc["benchmark"]} | set(sc.get("benchmark_info", {}))
    return sorted(syms, key=lambda s: (asset_class_of(s), s))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="*", default=None, help="por defecto, los de las candidatas")
    ap.add_argument("--end", default=END)
    ap.add_argument("--out", default=str(ROOT / "reports" / "datos"))
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    from tlab.data.alpaca_source import AlpacaSource, has_keys
    from tlab.data.loader import load_bars
    from tlab.data.yf_source import YFinanceSource

    if not has_keys():
        print(
            "Sin claves de Alpaca (ALPACA_API_KEY / ALPACA_SECRET_KEY en el entorno o en .env): "
            "no se hace el contraste. Ejecútalo en el PC que tiene el .env con las claves paper."
        )
        return 0
    s = load_settings()
    cache = ROOT / s["data"]["cache_dir"]
    syms = a.symbols or candidate_symbols()
    results, details = [], []
    yf_src, alp_src = YFinanceSource(), AlpacaSource()
    for sym in syms:
        ac = asset_class_of(sym)
        start = COMMON_START[ac]
        yf = load_bars([sym], start=s["data"]["history_start"], source=yf_src, cache_dir=cache,
                       asset_class=ac)[sym]  # fmt: skip
        try:
            alp = load_bars([sym], start="2015-01-01", end=a.end, source=alp_src,
                            cache_dir=cache, asset_class=ac)[sym]  # fmt: skip
        except Exception as e:  # sin datos o sin permiso: se anota, no se inventa
            print(f"{sym}: error al pedir datos a Alpaca ({type(e).__name__}); se marca REVISAR")
            alp = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
            alp.index = pd.DatetimeIndex([], tz="UTC")
        r, det = compare_returns(sym, ac, yf, alp, start, a.end)
        det["symbol"] = sym
        results.append(r)
        details.append(det)
        print(f"{sym:8} {r.verdict:8} corr={r.corr:.4f} días={r.common_days} {r.reasons}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(MADRID).strftime("%Y%m%d-%H%M")
    pd.DataFrame([asdict(r) for r in results]).to_csv(out / f"contraste_{stamp}.csv", index=False)
    ok = all(r.verdict == "OK" for r in results)
    md = [
        "# Contraste yfinance ↔ Alpaca",
        f"Generado: {now_madrid()}. Fuente Alpaca: feed {alp_src.feed}, ajuste `all`.",
        f"Tramo común: ETFs desde {COMMON_START['equity']}, cripto desde "
        f"{COMMON_START['crypto']}, hasta {a.end}. Se comparan rentabilidades diarias.",
        "Tolerancias: ver `src/tlab/data/crosscheck.py`.",
        "",
        results_table(results),
        "",
        f"**Resultado global: {'OK' if ok else 'REVISAR — parar e investigar antes de seguir'}**",
    ]
    p = out / f"contraste_{stamp}.md"
    p.write_text("\n".join(md), encoding="utf-8")
    print(f"Informe: {p}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
