"""Piezas comunes del candado del OOS (rondas 1 y 2): excepción, hash, registro CSV y
comprobación de trazabilidad con git (E20/E21). Sin dependencias de runner (evita ciclos)."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from tlab.config import ROOT

LOG_COLUMNS = [
    "date_madrid",
    "strategy",
    "params_hash",
    "forced",
    "tranche",
    "costs",
    "entry_delay",
    "kind",
    "report",
    "commit",
]
GUARDED_DIRS = ("config", "src", "scripts")  # E21: ninguna ejecución con cambios sin commitear
BLOCKED_STATUS = ("rechazada", "aparcada")  # E21: solo se pueden ejecutar en IS


class OOSGuardError(RuntimeError):
    """Uso indebido del out-of-sample."""


def params_hash(params: dict) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]


def read_log(path: Path) -> list[dict]:
    """Filas del registro (vacío si no existe). Las celdas que falten salen como ''."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return [{c: (r.get(c) or "") for c in LOG_COLUMNS} for r in csv.DictReader(f)]


def migrate_oos_log(path: Path) -> None:
    """Si la cabecera no es la actual (p. ej. la de 4 columnas de la ronda 1), reescribe el
    fichero con todas las columnas y las celdas nuevas vacías en las filas viejas. Idempotente.
    No borra ni reordena filas."""
    if not path.exists():
        return
    with open(path, encoding="utf-8", newline="") as f:
        header = next(csv.reader(f), [])
    if header == LOG_COLUMNS:
        return
    rows = read_log(path)
    write_log(path, rows)


def write_log(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def append_log_row(path: Path, row: dict) -> None:
    """Añade una fila (migrando antes la cabecera si hace falta)."""
    migrate_oos_log(path)
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if new:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in LOG_COLUMNS})


GitProbe = Callable[[], tuple[list[str], str]]


def git_probe(root: Path = ROOT) -> tuple[list[str], str]:
    """(líneas de `git status --porcelain -- config src scripts`, hash completo de HEAD)."""
    st = subprocess.run(
        ["git", "status", "--porcelain", "--", *GUARDED_DIRS],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    return [ln for ln in st.splitlines() if ln.strip()], head


def require_clean_tree(probe: GitProbe | None = None) -> str:
    """Aborta (OOSGuardError) si hay cambios sin commitear en config/, src/ o scripts/.
    Devuelve el hash completo de HEAD para anotarlo en el registro (E20/E21)."""
    dirty, head = (probe or git_probe)()
    if dirty:
        raise OOSGuardError(
            "Hay cambios sin commitear en config/, src/ o scripts/ (E21): commitea antes de "
            "ejecutar. Archivos: " + ", ".join(ln[3:] for ln in dirty[:5])
        )
    return head


def require_not_blocked(sc: dict, mode_is_is: bool) -> None:
    """E21: las estrategias `rechazada` o `aparcada` solo pueden ejecutar modos de IS."""
    if sc.get("status") in BLOCKED_STATUS and not mode_is_is:
        raise OOSGuardError(
            f"La estrategia {sc.get('id', '?')} está {sc['status']}: solo se permiten los "
            "modos de IS (E21). Retomarla exige una decisión de Jorge en persona (E17)."
        )
