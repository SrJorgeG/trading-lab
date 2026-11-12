"""Tramos de la escalera de la ronda 2 y candado de un solo uso (R2-5, E2, E11, E20, E21).

Tramos: `is` (libre mientras no se congele), y tras congelar, en este orden obligado:
`replica` → `holdout_old` → `holdout_new` → `full`. Cada tramo se mira UNA vez por
(estrategia, hash de parámetros y riesgo, costes, retraso, tipo). No hay `--force`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tlab.backtest.costs import CostModel, CostSchedule, cost_models
from tlab.backtest.guards import (
    OOSGuardError,
    append_log_row,
    params_hash,
    read_log,
)

TRANCHE_ORDER = ("replica", "holdout_old", "holdout_new", "full")  # tras el IS
IS_MODES = ("is", "wf", "robust")
RUN_KINDS = ("candidata", "monos_rank", "monos_persist", "monos_window", "combo")
ALLOWED_STRESS = {("base", 0), ("stress", 0), ("base", 1)}  # (costes, retraso)
COMBO_TRANCHES = ("holdout_old", "holdout_new", "full")  # E12


class TrancheGuardError(OOSGuardError):
    """Un tramo se salta, se repite o se pide en un estado que no toca."""


@dataclass(frozen=True)
class Tranche:
    name: str
    start: pd.Timestamp  # UTC
    end: pd.Timestamp  # UTC, inclusive
    universe: list[str]
    slippage_bps: float | None  # coste único…
    schedule: tuple[tuple[pd.Timestamp, float], ...] | None  # …o calendario (solo `full`)


def _utc(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def is_round2(sc: dict) -> bool:
    """True si el TOML define [tranches]."""
    return "tranches" in sc


def load_tranche(sc: dict, name: str) -> Tranche:
    """Lee [tranches.<name>]. Errores (ValueError): tramo desconocido; start > end; ni
    `slippage_bps` ni `slippage_schedule` (o los dos); calendario desordenado o cuya primera
    fecha es posterior a `start`; `is` distinto de (sc["start"], sc["is_end"]); cualquier
    tramo con `end` posterior a sc["end"]."""
    raw = sc.get("tranches", {})
    if name not in raw:
        raise ValueError(f"tramo desconocido: {name}")
    t = raw[name]
    start, end = _utc(t["start"]), _utc(t["end"])
    if start > end:
        raise ValueError(f"tramo {name}: start > end")
    has_bps, has_sched = "slippage_bps" in t, "slippage_schedule" in t
    if has_bps == has_sched:
        raise ValueError(f"tramo {name}: define slippage_bps o slippage_schedule (uno solo)")
    schedule = None
    if has_sched:
        schedule = tuple((_utc(d), float(b)) for d, b in t["slippage_schedule"])
        dates = [d for d, _ in schedule]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            raise ValueError(f"tramo {name}: calendario de costes desordenado")
        if dates[0] > start:
            raise ValueError(f"tramo {name}: el calendario empieza después de `start`")
    if name == "is" and (start, end) != (_utc(sc["start"]), _utc(sc["is_end"])):
        raise ValueError("el tramo `is` debe ser exactamente (start, is_end) de la estrategia")
    if end > _utc(sc["end"]):
        raise ValueError(f"tramo {name}: `end` posterior al fin de datos pre-registrado")
    uni_key = t.get("universe", "universe")
    if uni_key not in sc:
        raise ValueError(f"tramo {name}: universo `{uni_key}` no existe en el TOML")
    return Tranche(
        name=name,
        start=start,
        end=end,
        universe=list(sc[uni_key]),
        slippage_bps=None if has_sched else float(t["slippage_bps"]),
        schedule=schedule,
    )


def tranche_costs(
    settings: dict, tr: Tranche, costs_mode: str = "base"
) -> tuple[dict[str, CostModel], CostSchedule | None]:
    """Costes del tramo: slippage del tramo (× multiplicador si `stress`), comisión por acción
    de settings. Con calendario devuelve además el CostSchedule (y el dict = primer paso)."""
    base = cost_models(settings, "base")
    mult = settings["costs"]["stress"]["multiplier"] if costs_mode == "stress" else 1.0

    def models(bps: float) -> dict[str, CostModel]:
        eq = CostModel(
            slippage_bps=bps,
            commission_per_share=base["equity"].commission_per_share,
        ).scaled(mult)
        return {"equity": eq, "crypto": base["crypto"].scaled(mult)}

    if tr.schedule is None:
        return models(float(tr.slippage_bps)), None
    sched = CostSchedule(tuple((d, models(b)) for d, b in tr.schedule))
    return sched.steps[0][1], sched


def tranche_hash(params: dict, risk_per_trade: float) -> str:
    """params_hash({**params, "risk_per_trade": risk_per_trade}) (D4: el riesgo cuenta)."""
    return params_hash({**params, "risk_per_trade": risk_per_trade})


def assert_is_allowed(sc: dict, a: pd.Timestamp, b: pd.Timestamp) -> None:
    """Para is/wf/robust de la ronda 2: error si `frozen` es true (E2: tras congelar no hay
    más IS) o si [a, b] se sale de [start, is_end]."""
    if sc.get("frozen"):
        raise TrancheGuardError("La candidata está congelada (E2): no hay más pruebas IS.")
    lo, hi = _utc(sc["start"]), _utc(sc["is_end"])
    if a < lo or b > hi:
        raise TrancheGuardError(f"Una prueba IS debe quedar dentro de {lo.date()} → {hi.date()}.")


def check_tranche_guard(
    log_path: Path,
    strategy: str,
    tranche: str,
    h: str,
    costs_mode: str,
    entry_delay: int,
    kind: str,
    frozen: bool,
    confirm: bool,
    report: str = "",
    commit: str = "",
) -> None:
    """Valida y ANOTA (antes de simular) una ejecución de los peldaños 1–3 o de `full`.
    Lanza TrancheGuardError si no procede. Reglas en este orden (R2-5.2)."""
    # 1
    if not confirm:
        raise TrancheGuardError("El tramo se mira una vez: usa `--confirm-tranche`.")
    # 2
    if not frozen:
        raise TrancheGuardError("Falta el commit de congelación (E2): `frozen = false`.")
    if tranche not in TRANCHE_ORDER:
        raise TrancheGuardError(f"`{tranche}` no es un tramo guardado ({TRANCHE_ORDER}).")
    if kind not in RUN_KINDS:
        raise TrancheGuardError(f"tipo de ejecución desconocido: {kind}")
    # 3
    if (costs_mode, int(entry_delay)) not in ALLOWED_STRESS:
        raise TrancheGuardError(
            f"Combinación de costes/retraso no anunciada: ({costs_mode}, {entry_delay})."
        )
    rows = read_log(log_path)
    mine = [r for r in rows if r["strategy"] == strategy and r["tranche"] == tranche]
    # 4
    if any(r["params_hash"] != h for r in mine):
        raise TrancheGuardError(
            "Tramo ya gastado con otros parámetros: no hay `--force` en la ronda 2."
        )
    # 5 (el commit NO relaja la clave: la misma ejecución nunca se repite)
    key = (costs_mode, str(int(entry_delay)), kind)
    if any((r["costs"], r["entry_delay"], r["kind"]) == key for r in mine):
        raise TrancheGuardError("Ya ejecutado: ese tramo con esos costes/retraso/tipo ya se miró.")
    # 8 (combo) — la cadena de combos empieza en holdout_old
    order = TRANCHE_ORDER
    if kind == "combo":
        if tranche not in COMBO_TRANCHES:
            raise TrancheGuardError("`combo` solo en holdout_old, holdout_new o full (E12).")
        order = COMBO_TRANCHES
    base_kind = "combo" if kind == "combo" else "candidata"

    def has_base(tr: str) -> bool:
        return any(
            r["strategy"] == strategy
            and r["tranche"] == tr
            and r["params_hash"] == h
            and (r["costs"], r["entry_delay"], r["kind"]) == ("base", "0", base_kind)
            for r in rows
        )

    # 6
    i = order.index(tranche)
    if i > 0 and not has_base(order[i - 1]):
        raise TrancheGuardError(
            f"Orden obligado: antes de `{tranche}` falta la ejecución base de `{order[i - 1]}`."
        )
    # 7
    is_base = (costs_mode, int(entry_delay), kind) in (
        ("base", 0, "candidata"),
        ("base", 0, "combo"),
    )
    if not is_base and not has_base(tranche):
        raise TrancheGuardError(f"Falta la ejecución base de `{tranche}` antes de esta variante.")
    # 9: se anota antes de simular. Si la simulación falla, la fila se queda.
    from datetime import datetime

    from tlab.report import MADRID

    append_log_row(
        log_path,
        {
            "date_madrid": datetime.now(MADRID).isoformat(timespec="minutes"),
            "strategy": strategy,
            "params_hash": h,
            "forced": "False",
            "tranche": tranche,
            "costs": costs_mode,
            "entry_delay": str(int(entry_delay)),
            "kind": kind,
            "report": report,
            "commit": commit,
        },
    )
