"""¿La estrategia le gana al azar? N estrategias aleatorias con las mismas reglas.

Ejemplos (desde la raíz del repo):

    uv run python scripts/random_benchmark.py --preset donchian
    uv run python scripts/random_benchmark.py --preset tsmom_spy
    uv run python scripts/random_benchmark.py --strategy donchian_atr --no-kill-switch \\
        --n 1000 --seed 42 --metric sharpe

Por defecto SOLO in-sample. ``--period oos|full`` exige ``--confirm-oos`` (y queda anotado).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.backtest.random_benchmark import (  # noqa: E402
    COMPARE,
    DEFAULT_N,
    DEFAULT_SEED,
    run_random_benchmark,
)
from tlab.backtest.robust_reports import guard_oos, out_dir_for, write_random_outputs  # noqa: E402
from tlab.backtest.runner import OOSGuardError  # noqa: E402
from tlab.backtest.targets import PERIODS, build_target, check_period  # noqa: E402
from tlab.config import ROOT  # noqa: E402

PRESETS = {
    "donchian": {
        "strategy": "donchian_atr",
        "kill_switch": False,
        "title": "Donchian 20/10 (SPY, QQQ, BTC) sin kill switch",
    },
    "tsmom_spy": {
        "strategy": "tsmom_12m",
        "universe": ["SPY"],
        "start": "2005-01-01",
        "title": "TSMOM 12 meses (SPY)",
    },
    "faber_spy": {
        "strategy": "faber_sma10m",
        "universe": ["SPY"],
        "start": "2005-01-01",
        "title": "Faber SMA 10 meses (SPY)",
    },
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Compara la estrategia con N estrategias al azar emparejadas (mismo nº de "
        "operaciones, duración, exposición, stops, sizing y costes). Solo in-sample por defecto.",
        epilog="Presets: " + ", ".join(f"{k} ({v['title']})" for k, v in PRESETS.items()),
    )
    p.add_argument("--preset", choices=sorted(PRESETS))
    p.add_argument("--strategy")
    p.add_argument("--universe", nargs="+")
    p.add_argument("--n", type=int, default=DEFAULT_N, help="nº de monos (por defecto 1000)")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--metric", default="sharpe", choices=COMPARE, help="métrica del veredicto")
    p.add_argument("--period", default="is", choices=PERIODS)
    p.add_argument("--confirm-oos", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-kill-switch", action="store_true")
    p.add_argument("--costs", default="base", choices=["base", "stress", "zero"])
    p.add_argument("--start", help="inicio mínimo del periodo (AAAA-MM-DD)")
    p.add_argument("--no-calibrate", action="store_true", help="no alargar duraciones")
    p.add_argument("--n-jobs", type=int, default=-1)
    p.add_argument("--title")
    p.add_argument("--out")
    p.add_argument("--no-png", action="store_true")
    p.add_argument("--no-registry", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pre = PRESETS.get(args.preset, {}) if args.preset else {}
    strategy = args.strategy or pre.get("strategy")
    if not strategy:
        print("Falta --strategy o --preset (ver --help)")
        return 2
    kill = not (args.no_kill_switch or pre.get("kill_switch") is False)
    target = build_target(
        strategy,
        args.universe or pre.get("universe"),
        kill_switch=kill,
        costs_mode=args.costs,
        start=args.start or pre.get("start"),
    )
    try:
        check_period(args.period, args.confirm_oos)
        guard_oos(
            target,
            args.period,
            args.confirm_oos,
            args.force,
            "random_benchmark",
            {"n": args.n, "seed": args.seed},
        )
    except OOSGuardError as e:
        print(f"PARADO por el guard de OOS: {e}")
        return 3
    a, b = target.window(args.period)
    print(
        f"{strategy} · {args.period} {a.date()} → {b.date()} · {args.n} monos · semilla "
        f"{args.seed} · kill switch "
        f"{('sí' if kill else 'NO') if target.kind == 'signals' else 'n/a (pesos)'}"
    )
    rr = run_random_benchmark(
        target,
        args.n,
        args.seed,
        args.period,
        confirm_oos=args.confirm_oos,
        n_jobs=args.n_jobs,
        calibrate=not args.no_calibrate,
        progress=True,
    )
    out = Path(args.out) if args.out else out_dir_for(target, "azar", args.period)
    res = write_random_outputs(
        rr,
        out,
        metric=args.metric,
        title=args.title or pre.get("title"),
        registry=None if args.no_registry else ROOT / "docs" / "registro_pruebas.md",
        png=not args.no_png,
    )
    print(res["summary"].to_string(index=False))
    print(f"Veredicto ({args.metric}): {res['verdict']} (p = {res['p_value']:.3f})")
    for k, p in res["paths"].items():
        print(f"  {k}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
