"""Ejecución guardada de los monos de la ronda 2 (R2-9): solo IS y réplica.

Los monos NUNCA se ejecutan sobre `holdout_*` ni `full`. En la réplica hace falta
`confirm_tranche`, que la candidata esté congelada y que ya exista la ejecución base de la
réplica; la guarda lo anota (`monos_<modo>`)."""

from __future__ import annotations

from pathlib import Path

from tlab.backtest.custom_monkeys import MODES, run_custom_monkeys, write_monkey_outputs
from tlab.backtest.guards import GitProbe, require_clean_tree
from tlab.backtest.robust_reports import stamp
from tlab.backtest.targets import build_target
from tlab.backtest.tranches import (
    TrancheGuardError,
    assert_is_allowed,
    check_tranche_guard,
    load_tranche,
    tranche_hash,
)
from tlab.config import ROOT, load_settings, load_strategy_config
from tlab.report import append_registry

ALLOWED_TRANCHES = ("is", "replica")


def run_monkeys_r2(
    strategy: str,
    mode: str,
    tranche: str = "is",
    n: int = 1000,
    seed: int = 42,
    confirm_tranche: bool = False,
    data: dict | None = None,
    settings: dict | None = None,
    strat_cfg: dict | None = None,
    reports_dir: Path | None = None,
    registry: Path | None = None,
    git_probe: GitProbe | None = None,
    n_jobs: int = -1,
) -> Path:
    """Devuelve la carpeta con `monos.csv` y `resumen.md`."""
    if mode not in MODES:
        raise ValueError(f"modo de mono desconocido: {mode} (usa {MODES})")
    if tranche not in ALLOWED_TRANCHES:
        raise TrancheGuardError(
            f"Los monos solo se usan en IS y réplica; `{tranche}` no está permitido."
        )
    s = settings or load_settings()
    sc = strat_cfg or load_strategy_config(strategy)
    reports_dir = reports_dir or ROOT / "reports"
    registry = registry or ROOT / "docs" / "registro_pruebas.md"
    commit = require_clean_tree(git_probe)
    tr = load_tranche(sc, tranche)
    params = dict(sc["params"])
    risk = float(sc.get("risk_per_trade", s["risk"]["risk_per_trade"]))
    h = tranche_hash(params, risk)
    out = reports_dir / "robustez" / strategy / f"monos_{mode}_{tranche}_{stamp()}"
    if tranche == "is":
        assert_is_allowed(sc, tr.start, tr.end)
    else:
        check_tranche_guard(
            reports_dir / "oos_log.csv",
            strategy,
            tranche,
            h,
            "base",
            0,
            f"monos_{mode}",
            bool(sc.get("frozen")),
            confirm_tranche,
            report=str(out.relative_to(reports_dir.parent)) + "/resumen.md",
            commit=commit,
        )
    target = build_target(
        strategy, data=data, settings=s, strat_cfg=sc, kill_switch=False, tranche=tranche
    )
    res = run_custom_monkeys(target, mode, n=n, seed=seed, tranche=tranche, n_jobs=n_jobs)
    write_monkey_outputs(res, out)
    append_registry(
        registry,
        strategy,
        {**params, "risk_per_trade": risk},
        f"monos {mode}/{tranche} [monos, no es variante]/commit {commit}",
        f"k={res.k_ge}, p={res.p_value:.5f}, n={res.n}",
        str(out.relative_to(reports_dir.parent)) + "/resumen.md",
    )
    return out
