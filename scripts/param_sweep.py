"""Mapa de sensibilidad de parámetros (¿meseta o pico?) con el motor real.

Ejemplos (desde la raíz del repo):

    uv run python scripts/param_sweep.py --preset donchian          # 3 parámetros, 330 configs
    uv run python scripts/param_sweep.py --preset tsmom_spy
    uv run python scripts/param_sweep.py --strategy donchian_atr \\
        --grid entry_n=10:60:5 --grid exit_n=5:30:5 --no-kill-switch --metric sharpe
    uv run python scripts/param_sweep.py --strategy tsmom_12m --universe SPY EFA \\
        --grid months=3:18 --start 2005-01-01

Por defecto SOLO in-sample. ``--period oos|full`` exige ``--confirm-oos`` (y queda anotado).
Cada barrido se apunta en docs/registro_pruebas.md con el nº de configuraciones probadas.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.backtest.param_sweep import (  # noqa: E402
    DEFAULT_CACHE,
    DEFAULT_TOL,
    PRESETS,
    parse_axis,
    run_sweep,
)
from tlab.backtest.robust_reports import guard_oos, out_dir_for, write_sweep_outputs  # noqa: E402
from tlab.backtest.runner import OOSGuardError  # noqa: E402
from tlab.backtest.targets import PERIODS, SCORABLE, build_target  # noqa: E402
from tlab.config import ROOT  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Barrido de parámetros con mapa de calor, superficie 3D y puntuación de "
        "robustez (solo in-sample por defecto).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Presets: " + ", ".join(f"{k} ({v['title']})" for k, v in PRESETS.items()),
    )
    p.add_argument("--preset", choices=sorted(PRESETS), help="rejilla preparada")
    p.add_argument("--strategy", help="id de la estrategia (señales o asignación)")
    p.add_argument("--universe", nargs="+", help="activos (asignación: por defecto SPY)")
    p.add_argument(
        "--grid",
        action="append",
        default=None,
        help="eje: nombre=a:b[:paso] o nombre=v1,v2 (1–3 veces)",
    )
    p.add_argument("--metric", default="sharpe", choices=SCORABLE, help="métrica de la puntuación")
    p.add_argument("--tol", type=float, default=DEFAULT_TOL, help="'casi igual' (0.20 = 20 %%)")
    p.add_argument("--period", default="is", choices=PERIODS)
    p.add_argument("--confirm-oos", action="store_true", help="permite oos/full (lo anota)")
    p.add_argument("--force", action="store_true", help="ver runner.check_oos_guard")
    p.add_argument("--no-kill-switch", action="store_true", help="como las baselines informativas")
    p.add_argument("--costs", default="base", choices=["base", "stress", "zero"])
    p.add_argument("--start", help="inicio mínimo del periodo (AAAA-MM-DD)")
    p.add_argument("--n-jobs", type=int, default=-1, help="procesos (-1 = todos los núcleos)")
    p.add_argument("--no-cache", action="store_true", help="recalcula todo")
    p.add_argument("--pbo-blocks", type=int, default=16, help="bloques de CSCV (par)")
    p.add_argument("--title", help="título del informe")
    p.add_argument("--out", help="carpeta de salida (por defecto reports/robustez/...)")
    p.add_argument("--no-png", action="store_true")
    p.add_argument("--no-registry", action="store_true", help="no anotar (solo pruebas)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pre = PRESETS.get(args.preset, {}) if args.preset else {}
    strategy = args.strategy or pre.get("strategy")
    if not strategy:
        print("Falta --strategy o --preset (ver --help)")
        return 2
    grid = args.grid or pre.get("grid")
    if not grid:
        print("Falta al menos un --grid nombre=a:b[:paso]")
        return 2
    kill = not (args.no_kill_switch or pre.get("kill_switch") is False)
    target = build_target(
        strategy,
        args.universe or pre.get("universe"),
        kill_switch=kill,
        costs_mode=args.costs,
        start=args.start or pre.get("start"),
    )
    axes = dict(parse_axis(g, target.params.get(g.split("=")[0].strip())) for g in grid)
    try:
        from tlab.backtest.targets import check_period

        check_period(args.period, args.confirm_oos)
        guard_oos(
            target,
            args.period,
            args.confirm_oos,
            args.force,
            "param_sweep",
            {"rejilla": {k: list(map(str, v)) for k, v in axes.items()}},
        )
    except OOSGuardError as e:
        print(f"PARADO por el guard de OOS: {e}")
        return 3
    a, b = target.window(args.period)
    n = 1
    for v in axes.values():
        n *= len(v)
    ks = ("sí" if kill else "NO") if target.kind == "signals" else "n/a (pesos)"
    print(
        f"{strategy} · {args.period} {a.date()} → {b.date()} · {n} configuraciones · "
        f"kill switch {ks} · costes {args.costs}"
    )
    sw = run_sweep(
        target,
        axes,
        args.period,
        confirm_oos=args.confirm_oos,
        n_jobs=args.n_jobs,
        cache_dir=None if args.no_cache else DEFAULT_CACHE,
        progress=True,
    )
    print(f"  {sw.n_computed} calculadas, {sw.n_cached} de caché")
    out = Path(args.out) if args.out else out_dir_for(target, "sweep", args.period)
    res = write_sweep_outputs(
        sw,
        out,
        metric=args.metric,
        title=args.title or pre.get("title"),
        tol=args.tol,
        registry=None if args.no_registry else ROOT / "docs" / "registro_pruebas.md",
        png=not args.no_png,
    )
    rob, ov = res["robustness"], res["overfit"]
    print(f"Robustez {rob['score']:.0f}/100 → {rob['verdict']}")
    if ov.get("pbo"):
        print(
            f"PBO {ov['pbo']['pbo']:.1%} · DSR {ov['dsr']['dsr']:.3f} (N={ov['dsr']['n_trials']})"
        )
    for k, p in res["paths"].items():
        print(f"  {k}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
