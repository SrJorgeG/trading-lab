"""Informes markdown/CSV de los backtests."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

MADRID = ZoneInfo("Europe/Madrid")
REQUIRED_SECTIONS = [
    "## Métricas: estrategia vs benchmark",
    "## Datos",
    "## Costes",
    "## Parámetros",
    "## Variantes probadas",
]
METRIC_ROWS = [
    ("cagr", "CAGR", "pct"),
    ("total_return", "Rentabilidad total", "pct"),
    ("vol", "Volatilidad anual", "pct"),
    ("sharpe", "Sharpe", "f2"),
    ("sortino", "Sortino", "f2"),
    ("max_dd", "Máx. drawdown", "pct"),
    ("max_dd_days", "Máx. días bajo el agua", "int"),
    ("calmar", "Calmar", "f2"),
    ("trades", "Nº operaciones", "int"),
    ("win_rate", "Win rate", "pct"),
    ("expectancy_usd", "Expectancy ($)", "f2"),
    ("expectancy_r", "Expectancy (R)", "f2"),
    ("profit_factor", "Profit factor", "f2"),
    ("avg_exposure", "Exposición media", "pct"),
    ("avg_days", "Duración media (días)", "f1"),
]


def fmt(v, kind: str) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if kind == "pct":
        return f"{v * 100:.2f} %"
    if kind == "int":
        return f"{int(v)}"
    return f"{v:.{kind[1]}f}"


def metrics_table(strat: dict, bench: dict) -> str:
    lines = ["| Métrica | Estrategia | Benchmark |", "|---|---|---|"]
    for k, label, kind in METRIC_ROWS:
        if k in strat or k in bench:
            lines.append(f"| {label} | {fmt(strat.get(k), kind)} | {fmt(bench.get(k), kind)} |")
    return "\n".join(lines)


def now_madrid() -> str:
    return datetime.now(MADRID).strftime("%Y-%m-%d %H:%M (hora de Madrid)")


def write_report(
    out_dir: Path,
    title: str,
    strat: dict,
    bench: dict,
    data_info: str,
    costs_info: str,
    params: dict,
    n_variants: int,
    equity: pd.Series,
    trades: pd.DataFrame,
    extra: str = "",
) -> Path:
    """Escribe resumen.md, trades.csv y equity.csv. Devuelve la ruta de resumen.md."""
    out_dir.mkdir(parents=True, exist_ok=True)
    md = [
        f"# {title}",
        f"Generado: {now_madrid()}",
        "",
        "## Métricas: estrategia vs benchmark",
        metrics_table(strat, bench),
        "",
        "## Datos",
        data_info,
        "",
        "## Costes",
        costs_info,
        "",
        "## Parámetros",
        "```",
        *[f"{k} = {v!r}" for k, v in params.items()],
        "```",
        "",
        "## Variantes probadas",
        f"Ejecuciones registradas para esta estrategia: {n_variants}",
        "",
    ]
    if extra:
        md += [extra, ""]
    p = out_dir / "resumen.md"
    p.write_text("\n".join(md), encoding="utf-8")
    trades.to_csv(out_dir / "trades.csv", index=False)
    equity.to_csv(out_dir / "equity.csv", header=True)
    return p


REGISTRY_HEADER = (
    "| fecha | hipótesis | variante/parámetros | conjunto (IS/WF/OOS) | "
    "resultado clave | archivo de informe |\n|---|---|---|---|---|---|\n"
)


def append_registry(
    path: Path, strategy: str, params: dict, mode: str, key: str, report: str
) -> int:
    """Añade una línea al registro y devuelve cuántas tiene ya esta estrategia."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Registro de pruebas\n\n" + REGISTRY_HEADER, encoding="utf-8")
    ptxt = ", ".join(f"{k}={v}" for k, v in params.items())
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"| {now_madrid()} | {strategy} | {ptxt} | {mode} | {key} | {report} |\n")
    return sum(
        1
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.startswith("|") and f"| {strategy} |" in ln
    )
