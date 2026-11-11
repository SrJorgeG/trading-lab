"""Diagnóstico del contraste yfinance ↔ Alpaca: días peores y solape con ex-dividendos.

Uso (en el PC con las claves PAPER de Alpaca en .env):
    uv run python scripts/diag_alpaca_vs_yf.py

No opera. Lee ALPACA_API_KEY / ALPACA_SECRET_KEY del entorno o de .env; si no están,
avisa y sale con código 0. Las claves nunca se imprimen.

Para cada ETF de las candidatas descarga:
- yfinance con auto_adjust (retorno total, la fuente de los backtests) y Close solo por splits;
- Alpaca SIP con adjustment=all (el contraste oficial) y adjustment=split (sin dividendos).

Compara las rentabilidades diarias (no los niveles), lista los peores desajustes junto a las
fechas ex-dividendo de yfinance, y aísla si el hueco es de dividendos o de cierres distintos.
Escribe reports/datos/diag_alpaca_vs_yf_<fecha>.md. Ver docs/INVESTIGACION_DATOS.md.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from tlab.config import ROOT, asset_class_of, load_settings  # noqa: E402
from tlab.data.crosscheck import (  # noqa: E402
    COMMON_START,
    TOLERANCES,
    attach_dividends,
    compare_returns,
    exdiv_overlap_stats,
    to_naive_dates,
    with_naive_dates,
)
from tlab.report import MADRID, now_madrid  # noqa: E402

END = "2026-10-31"
# Universo de las candidatas ETF + los que ya cuadraron, para comparar.
DEFAULT_SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "EFA", "EEM", "IEF", "GLD", "DBC", "VNQ"]
N_WORST = 25


def _yf_dividends(symbol: str, start: str, end: str) -> pd.Series:
    import yfinance as yf

    acts = yf.Ticker(symbol).dividends
    if acts is None or len(acts) == 0:
        return pd.Series(dtype=float)
    s = acts.copy()
    s = s[(s.index >= start) & (s.index <= end)]
    return s.astype(float)


def _yf_split_only(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Close de yfinance ajustado solo por splits (auto_adjust=False). Índice UTC."""
    import yfinance as yf

    # end de yfinance es exclusivo; pedimos un día más para incluir `end` si existe.
    end_dl = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    raw = yf.download(
        symbol,
        start=start,
        end=end_dl,
        interval="1d",
        auto_adjust=False,
        progress=False,
        multi_level_index=False,
        threads=False,
    )
    if raw is None or raw.empty:
        empty = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        empty.index = to_naive_dates(pd.DatetimeIndex([], dtype="datetime64[ns]"))
        return empty
    df = raw.rename(columns=str.lower)
    out = pd.DataFrame(
        {
            "open": df["open"],
            "high": df["high"],
            "low": df["low"],
            "close": df["close"],
            "volume": df["volume"],
        }
    ).astype(float)
    out = with_naive_dates(out)
    s, e = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    return out.loc[(out.index >= s) & (out.index <= e)]


def _fmt_pct(x: float) -> str:
    return "—" if pd.isna(x) else f"{x * 100:.1f} %"


def _fmt_corr(x: float) -> str:
    return "—" if pd.isna(x) else f"{x:.4f}"


def _pair_line(label: str, r) -> str:
    return (
        f"| {label} | {_fmt_corr(r.corr)} | {r.best_lag:+d} | "
        f"{r.share_within_tol * 100:.1f} % | {r.median_abs_diff_bp:.2f} | "
        f"{r.p99_abs_diff_bp:.1f} | {r.max_abs_diff_bp:.1f} ({r.max_diff_date}) | "
        f"**{r.verdict}** | {r.reasons} |"
    )


def _worst_table(det: pd.DataFrame, n: int = N_WORST) -> str:
    if det.empty or "abs_diff" not in det.columns:
        return "_sin detalle_"
    top = det.sort_values("abs_diff", ascending=False).head(n)
    lines = [
        "| fecha | ret yf (pb) | ret Alpaca (pb) | |Δ| (pb) | ex-div | dividendo |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for ts, row in top.iterrows():
        ex = "sí" if bool(row.get("is_exdiv", False)) else ""
        div = row.get("div_amount", float("nan"))
        div_s = "—" if pd.isna(div) else f"{div:.4f}"
        lines.append(
            f"| {pd.Timestamp(ts).date()} | {row['ret_yf'] * 1e4:.1f} | "
            f"{row['ret_alpaca'] * 1e4:.1f} | {row['abs_diff'] * 1e4:.1f} | {ex} | {div_s} |"
        )
    return "\n".join(lines)


def _overlap_line(stats: dict, tol_bp: float) -> str:
    so = stats["share_over_that_are_exdiv"]
    se = stats["share_exdiv_that_are_over"]
    so_s = "—" if pd.isna(so) else f"{so * 100:.0f} %"
    se_s = "—" if pd.isna(se) else f"{se * 100:.0f} %"
    return (
        f"- Días con |Δ| > {tol_bp:.0f} pb: **{stats['n_over']}**. "
        f"Ex-dividendos en el tramo: **{stats['n_exdiv']}**. "
        f"Coinciden: **{stats['n_over_and_exdiv']}** "
        f"(el {so_s} de los desajustes caen en ex-div; "
        f"el {se_s} de los ex-div superan {tol_bp:.0f} pb)."
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="*", default=None)
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
            "no se hace el diagnóstico. Ejecútalo en el PC que tiene el .env con las claves paper."
        )
        return 0

    s = load_settings()
    cache = ROOT / s["data"]["cache_dir"]
    syms = a.symbols or DEFAULT_SYMBOLS
    yf_src = YFinanceSource()
    alp_all = AlpacaSource(adjustment="all")
    alp_split = AlpacaSource(adjustment="split")
    start_equity = COMMON_START["equity"]
    sections: list[str] = []

    header = [
        "# Diagnóstico yfinance ↔ Alpaca",
        f"Generado: {now_madrid()}.",
        f"Alpaca: feed pedido SIP (si cae a IEX se verá abajo; all={alp_all.feed} al crear). "
        f"Ajuste `all` y, en paralelo, `split`.",
        f"Tramo: ETFs {start_equity} → {a.end}. Se comparan rentabilidades diarias, no niveles.",
        "Dividendos: fechas ex-div de yfinance (`Ticker.dividends`).",
        "",
        "Lectura rápida de las 4 comparaciones por activo:",
        "- **YF auto vs Alpaca all**: el contraste oficial (retorno total contra retorno total).",
        "- **YF auto vs Alpaca split**: si Alpaca no aplicara dividendos, aquí deberían "
        "concentrarse los desajustes en los ex-div.",
        "- **YF split vs Alpaca split**: solo cierres (sin dividendos). Si esto ya no cuadra, "
        "el hueco no es (solo) el ajuste de dividendos.",
        "- **YF auto vs YF split**: efecto puro de los dividendos en Yahoo; referencia.",
        "",
    ]

    for sym in syms:
        ac = asset_class_of(sym)
        if ac != "equity":
            print(f"{sym}: este diagnóstico es para ETFs; se salta")
            continue
        start = start_equity
        print(f"=== {sym} ===")
        yf_auto = load_bars(
            [sym], start=s["data"]["history_start"], source=yf_src, cache_dir=cache, asset_class=ac
        )[sym]
        yf_split = _yf_split_only(sym, start="2015-01-01", end=a.end)
        try:
            alp_a = load_bars(
                [sym],
                start="2015-01-01",
                end=a.end,
                source=alp_all,
                cache_dir=cache,
                asset_class=ac,
            )[sym]
        except Exception as e:
            print(f"{sym}: error Alpaca all ({type(e).__name__}: {e})")
            alp_a = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
            alp_a.index = pd.DatetimeIndex([], tz="UTC")
        try:
            alp_s = load_bars(
                [sym],
                start="2015-01-01",
                end=a.end,
                source=alp_split,
                cache_dir=cache,
                asset_class=ac,
            )[sym]
        except Exception as e:
            print(f"{sym}: error Alpaca split ({type(e).__name__}: {e})")
            alp_s = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
            alp_s.index = pd.DatetimeIndex([], tz="UTC")

        yf_auto = with_naive_dates(yf_auto)
        yf_split = with_naive_dates(yf_split)
        alp_a = with_naive_dates(alp_a)
        alp_s = with_naive_dates(alp_s)
        pairs = {
            "YF auto vs Alpaca all": (yf_auto, alp_a),
            "YF auto vs Alpaca split": (yf_auto, alp_s),
            "YF split vs Alpaca split": (yf_split, alp_s),
            "YF auto vs YF split": (yf_auto, yf_split),
        }
        results = {}
        details = {}
        for label, (left, right) in pairs.items():
            r, det = compare_returns(sym, ac, left, right, start, a.end)
            results[label] = r
            details[label] = det
            print(
                f"  {label:28} {r.verdict:8} corr={r.corr:.4f} "
                f"share={r.share_within_tol * 100:.1f}% {r.reasons}"
            )

        divs = _yf_dividends(sym, start, a.end)
        official = attach_dividends(details["YF auto vs Alpaca all"], divs)
        stats = exdiv_overlap_stats(official, tol=TOLERANCES["equity"]["abs_diff"])
        print(
            f"  overlap: {stats['n_over_and_exdiv']}/{stats['n_over']} desajustes en ex-div "
            f"(ex-divs={stats['n_exdiv']})"
        )

        sec = [
            f"## {sym}",
            f"Feed Alpaca usado en esta corrida: **{alp_all.feed}** "
            f"(all) / **{alp_split.feed}** (split). Dividendos yfinance en el tramo: "
            f"**{len(divs)}**.",
            "",
            (
                "| comparación | corr | desfase | % dentro tol. | mediana pb | p99 pb "
                "| máx pb (fecha) | veredicto | motivo |"
            ),
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for label, r in results.items():
            sec.append(_pair_line(label, r))
        sec += ["", _overlap_line(stats, TOLERANCES["equity"]["abs_diff"] * 1e4), ""]
        sec += [
            f"Peores {N_WORST} días del contraste oficial (YF auto vs Alpaca all):",
            "",
            _worst_table(official, N_WORST),
            "",
        ]
        sections.append("\n".join(sec))

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(MADRID).strftime("%Y%m%d-%H%M")
    p = out / f"diag_alpaca_vs_yf_{stamp}.md"
    p.write_text("\n".join(header + sections), encoding="utf-8")
    print(f"Informe: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
