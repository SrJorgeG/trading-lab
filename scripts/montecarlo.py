"""Monte Carlo de robustez sobre un backtest ya corrido.

Ejemplos:

    uv run python scripts/montecarlo.py --list
    uv run python scripts/montecarlo.py --run reports/donchian_atr/is_20261111-0140 --method shuffle
    uv run python scripts/montecarlo.py --run reports/baselines/20261111-0141/faber_sma_spy \
        --method block
    uv run python scripts/montecarlo.py --prepare-baselines
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.backtest.montecarlo import (  # noqa: E402
    DEFAULT_BLOCK,
    DEFAULT_KILL,
    DEFAULT_N,
    DEFAULT_RUIN,
    DEFAULT_SEED,
    METHODS,
    MCConfig,
    load_run,
    run_montecarlo,
    write_outputs,
)
from tlab.config import ROOT  # noqa: E402


def discover_runs(root: Path | None = None) -> list[Path]:
    """Carpetas de reports/ que tienen equity.csv."""
    root = root or (ROOT / "reports")
    if not root.exists():
        return []
    return sorted({p.parent for p in root.rglob("equity.csv")})


def resolve_run(spec: str, reports: Path | None = None) -> Path:
    """Acepta una ruta, un id tipo estrategia/modo_fecha, o un slug de baseline."""
    reports = reports or (ROOT / "reports")
    raw = Path(spec).expanduser()
    candidates = []
    if raw.is_dir() and (raw / "equity.csv").exists():
        return raw.resolve()
    for c in (
        raw,
        ROOT / spec,
        reports / spec,
        Path.cwd() / spec,
    ):
        if c.is_dir() and (c / "equity.csv").exists():
            candidates.append(c.resolve())
    # id suelto: busca por sufijo de ruta o nombre de carpeta
    for p in discover_runs(reports):
        rel = p.relative_to(reports) if p.is_relative_to(reports) else p
        if spec in {p.name, str(rel), str(rel).replace("\\", "/")}:
            candidates.append(p)
        elif spec in str(rel):
            candidates.append(p)
    # registro de pruebas: última columna es la ruta del resumen.md
    registry = ROOT / "docs" / "registro_pruebas.md"
    if registry.exists():
        for line in registry.read_text(encoding="utf-8").splitlines():
            if spec in line and line.startswith("|"):
                parts = [x.strip() for x in line.strip("|").split("|")]
                if parts:
                    maybe = ROOT / parts[-1]
                    folder = maybe.parent if maybe.suffix else maybe
                    if (folder / "equity.csv").exists():
                        candidates.append(folder.resolve())
    uniq = list(dict.fromkeys(candidates))
    if len(uniq) == 1:
        return uniq[0]
    if len(uniq) > 1:
        opts = "\n".join(f"  {p}" for p in uniq)
        raise SystemExit(f"Varias carpetas coinciden con {spec!r}:\n{opts}")
    raise SystemExit(
        f"No encuentro una carpeta de backtest para {spec!r}. "
        "Pasa la ruta a un directorio con equity.csv, o usa --list."
    )


def prepare_baselines(out_parent: Path | None = None) -> list[Path]:
    """Re-simula las baselines de referencia y guarda equity/trades (mismos parámetros)."""
    from dataclasses import replace

    import pandas as pd

    from tlab.backtest.allocation_sim import simulate_weights
    from tlab.backtest.costs import cost_models
    from tlab.backtest.portfolio_sim import SimConfig, simulate
    from tlab.config import load_settings
    from tlab.data.loader import load_bars, pick_source
    from tlab.strategies import allocation
    from tlab.strategies.donchian_atr import generate_signals as donchian

    # Reutilizamos el sello de la corrida de referencia si existe.
    default_stamp = ROOT / "reports" / "baselines" / "20261111-0141"
    out_parent = out_parent or (default_stamp if default_stamp.exists() else None)
    if out_parent is None:
        from tlab.report import MADRID

        stamp = pd.Timestamp.now(tz=MADRID).strftime("%Y%m%d-%H%M")
        out_parent = ROOT / "reports" / "baselines" / stamp
    out_parent = Path(out_parent)
    out_parent.mkdir(parents=True, exist_ok=True)

    s = load_settings()
    src = pick_source(s["data"]["source"])
    syms = ["SPY", "QQQ", "EFA", "EEM", "TLT", "IEF", "GLD", "BIL", "BTC/USD"]
    data = load_bars(
        syms,
        "1Day",
        start=s["data"]["history_start"],
        source=src,
        cache_dir=ROOT / s["data"]["cache_dir"],
    )
    init = s["capital"]["virtual_equity_usd"]
    costs = cost_models(s, "base")
    eq_start = "2005-01-01"

    def save(slug: str, equity: pd.Series, trades: pd.DataFrame, title: str) -> Path:
        d = out_parent / slug
        d.mkdir(parents=True, exist_ok=True)
        equity.to_csv(d / "equity.csv", header=True)
        trades.to_csv(d / "trades.csv", index=False)
        (d / "resumen.md").write_text(
            f"# {title}\n\nCurvas exportadas para Monte Carlo (costes base, mismos "
            f"parámetros que docs/baselines.md).\n",
            encoding="utf-8",
        )
        return d

    def alloc(fn, params, symbols, start=eq_start):
        closes = pd.DataFrame({x: data[x]["close"] for x in symbols}).dropna(how="all")
        bars = {x: data[x].reindex(closes.index) for x in symbols}
        w = fn(closes, params)
        return simulate_weights(bars, w, costs, init, start=start)

    written: list[Path] = []
    jobs = [
        (
            "faber_sma_spy",
            "Faber SMA 10 meses (SPY)",
            allocation.faber_sma,
            {"months": 10},
            ["SPY"],
        ),
        ("tsmom_12m_spy", "TSMOM 12m (SPY)", allocation.tsmom, {"months": 12}, ["SPY"]),
        (
            "tsmom_12m_1n",
            "TSMOM 12m 1/N (SPY, EFA, EEM, TLT, GLD)",
            allocation.tsmom,
            {"months": 12},
            ["SPY", "EFA", "EEM", "TLT", "GLD"],
        ),
    ]
    for slug, title, fn, params, symbols in jobs:
        eq, tr = alloc(fn, params, symbols)
        written.append(save(slug, eq, tr, title))

    r = s["risk"]
    cfg = SimConfig(
        initial_equity=init,
        risk_per_trade=r["risk_per_trade"],
        max_positions=r["max_positions"],
        max_gross_exposure=r["max_gross_exposure"],
        kill_switch_drawdown=None,
        costs=costs,
    )
    dp = {"entry_n": 20, "exit_n": 10, "atr_mult": 2.0, "atr_n": 20}
    dsyms = ["SPY", "QQQ", "BTC/USD"]
    a = pd.Timestamp(eq_start, tz="UTC")
    bars = {x: data[x] for x in dsyms}
    sigs = {x: donchian(b, dp) for x, b in bars.items()}
    bb = {x: b[b.index >= a] for x, b in bars.items()}
    ss = {x: sigs[x][sigs[x].index >= a] for x in dsyms}
    res = simulate(bb, ss, replace(cfg, kill_switch_drawdown=None))
    written.append(
        save(
            "donchian_nokill",
            res.equity,
            res.trades,
            "Donchian 20/10 — igual pero SIN kill switch (informativo)",
        )
    )
    print("Curvas de baseline escritas en:")
    for p in written:
        print(f"  {p.relative_to(ROOT)}")
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", help="carpeta de informe, id de registro o slug (ver --list)")
    ap.add_argument("--method", choices=METHODS, default="shuffle")
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument(
        "--block", type=int, default=DEFAULT_BLOCK, help="longitud de bloque (método block)"
    )
    ap.add_argument(
        "--kill", type=float, default=DEFAULT_KILL, help="kill switch (fracción, 0.10 = 10 %)"
    )
    ap.add_argument(
        "--ruin", type=float, default=DEFAULT_RUIN, help="umbral de ruina desde el inicio"
    )
    ap.add_argument("--sizing", choices=("additive", "compound"), default="additive")
    ap.add_argument("--out", default=None, help="carpeta de salida (por defecto, la del backtest)")
    ap.add_argument("--list", action="store_true", help="lista carpetas con equity.csv")
    ap.add_argument("--prepare-baselines", action="store_true")
    ap.add_argument("--no-html", action="store_true")
    ap.add_argument("--no-png", action="store_true")
    ap.add_argument(
        "--cdn-html",
        action="store_true",
        help="HTML más ligero (plotly por CDN; hace falta red para verlo)",
    )
    a = ap.parse_args(argv)

    if a.prepare_baselines:
        prepare_baselines()
        if not a.run:
            return 0
    if a.list:
        runs = discover_runs()
        if not runs:
            print("No hay carpetas con equity.csv en reports/.")
            return 0
        for p in runs:
            try:
                rel = p.relative_to(ROOT)
            except ValueError:
                rel = p
            print(rel)
        return 0
    if not a.run:
        ap.error("indica --run, --list o --prepare-baselines")

    folder = resolve_run(a.run)
    equity, trades, meta = load_run(folder)
    cfg = MCConfig(
        n=a.n,
        seed=a.seed,
        method=a.method,
        block_length=a.block,
        kill_switch=a.kill,
        ruin_threshold=a.ruin,
        sizing=a.sizing,
    )
    result = run_montecarlo(equity, trades, cfg)
    out = Path(a.out) if a.out else folder
    paths = write_outputs(
        result,
        out,
        meta.get("title", folder.name),
        cfg,
        html=not a.no_html,
        png=not a.no_png,
        offline_html=not a.cdn_html,
    )
    print(f"Monte Carlo {result.method} n={result.n} semilla={result.seed}")
    print(
        f"  P(kill switch)={result.p_kill:.2%}  "
        f"P(bajo inicio)={result.p_below_start:.2%}  "
        f"P(ruina)={result.p_ruin:.2%}"
    )
    print(f"  CAGR real={result.real['cagr']:.2%}  DD real={result.real['max_dd']:.2%}")
    for k, p in paths.items():
        try:
            print(f"  {k}: {p.relative_to(ROOT)}")
        except ValueError:
            print(f"  {k}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
