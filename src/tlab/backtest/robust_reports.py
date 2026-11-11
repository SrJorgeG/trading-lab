"""Salidas de las herramientas de robustez: CSV, JSON, HTML, PNG, resumen.md en español y
anotación en ``docs/registro_pruebas.md``. También relee lo guardado (para el visor)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from tlab.backtest import robust_viz as viz
from tlab.backtest.param_sweep import (
    DEFAULT_TOL,
    SweepResult,
    overfit_stats,
    score_metric,
    warnings_for,
)
from tlab.backtest.random_benchmark import (
    COMPARE,
    RandomResult,
    p_verdict,
    summary_table,
)
from tlab.backtest.runner import check_oos_guard
from tlab.backtest.targets import METRICS, SCORABLE, Target
from tlab.config import ROOT
from tlab.report import MADRID, append_registry, now_madrid

REGISTRY = ROOT / "docs" / "registro_pruebas.md"
SWEEP_VIEWS_METRICS = ["sharpe", "cagr", "max_dd", "mar", "expectancy_r", "trades"]


def stamp() -> str:
    return pd.Timestamp.now(tz=MADRID).strftime("%Y%m%d-%H%M")


def out_dir_for(target: Target, tool: str, period: str, base: Path | None = None) -> Path:
    base = base or ROOT / "reports" / "robustez"
    return base / target.slug / f"{tool}_{period}_{stamp()}"


def registry_label(target: Target) -> str:
    if target.kind == "weights":
        return f"{target.strategy} ({', '.join(target.universe)})"
    return target.strategy


def registry_trials(path: Path, label: str) -> int:
    """Intentos ya anotados para esta estrategia: 1 por fila normal + N por cada barrido."""
    if not Path(path).exists():
        return 0
    n = 0
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if not ln.startswith("|") or f"| {label} |" not in ln:
            continue
        m = re.search(r"N=(\d+) configuraciones", ln)
        n += int(m.group(1)) if m else 1
    return n


def guard_oos(
    target: Target, period: str, confirm: bool, force: bool, tool: str, extra: dict
) -> None:
    """Si se usa OOS (ya confirmado), lo anota en reports/oos_log.csv con el guard del runner."""
    if period == "is":
        return
    check_oos_guard(
        ROOT / "reports" / "oos_log.csv",
        target.strategy,
        {"herramienta": tool, "periodo": period, **extra},
        confirm,
        force,
    )


def _pct(x, nd=0) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x * 100:.{nd}f} %"


def _f(x, nd=2) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x:.{nd}f}"


def _thousands(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


def _vclass(score: float) -> str:
    return "good" if score >= 70 else "mid" if score >= 40 else "bad"


def axes_text(axes: dict) -> str:
    parts = []
    for k, v in axes.items():
        parts.append(f"{k}={viz._fmt_val(v[0])}..{viz._fmt_val(v[-1])} ({len(v)})")
    return " × ".join(parts)


def _params_txt(axes: dict, row) -> str:
    return ", ".join(f"{k}={viz._fmt_val(row[k])}" for k in axes)


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.ndarray):
        return _jsonable(o.tolist())
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    return o


def _costs_txt(t: Target) -> str:
    return "; ".join(
        f"{k}: slippage {v.slippage_bps:g} pb/lado, comisión {v.fee_rate * 100:.3f} %/lado"
        for k, v in sorted(t.cfg.costs.items())
    )


def _rules_txt(t: Target) -> str:
    if t.kind == "weights":
        return (
            "asignación mensual por pesos (allocation_sim): decide con el cierre de fin de mes y "
            "ejecuta en la apertura siguiente; **sin** stop, sin 1 % de riesgo y sin kill switch"
        )
    c = t.cfg
    ks = (
        f"kill switch {c.kill_switch_drawdown:.0%}"
        if c.kill_switch_drawdown
        else "**SIN kill switch**"
    )
    return (
        f"portfolio_sim con reglas duras: riesgo {c.risk_per_trade:.0%} por operación con stop, "
        f"máx. {c.max_positions} posiciones, exposición ≤ {c.max_gross_exposure:.0%}, {ks}"
    )


# ====================================================================== barrido


def write_sweep_outputs(
    sw: SweepResult,
    out: Path,
    *,
    metric: str = "sharpe",
    title: str | None = None,
    tol: float = DEFAULT_TOL,
    registry: Path | None = REGISTRY,
    png: bool = True,
    html: bool = True,
    pbo_blocks: int = 16,
) -> dict:
    """Escribe todo y anota el barrido en el registro. Devuelve rutas y cifras clave."""
    t = sw.target
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    title = title or f"{t.strategy} — mapa de parámetros"
    label = registry_label(t)
    prev = registry_trials(registry, label) if registry else 0
    robs = {m: score_metric(sw, m, tol) for m in SCORABLE if sw.table[m].notna().any()}
    rob = robs[metric]
    ov = overfit_stats(sw, pbo_blocks, registry_trials=prev + sw.n_configs)
    warns = warnings_for(sw, metric, rob, ov)
    a, b = t.window(sw.period)
    paths = {"csv": out / "sweep.csv", "json": out / "robustez.json", "md": out / "resumen.md"}
    sw.table.to_csv(paths["csv"], index=False)
    meta = {
        "tool": "param_sweep",
        "title": title,
        "strategy": t.strategy,
        "kind": t.kind,
        "universe": t.universe,
        "period": sw.period,
        "window": [str(a), str(b)],
        "axes": sw.axes,
        "defaults": {k: t.params.get(k) for k in sw.axes},
        "default_idx": sw.default_idx,
        "params_base": t.params,
        "metric": metric,
        "tol": tol,
        "kill_switch": t.kill_switch,
        "costs_mode": t.costs_mode,
        "n_configs": sw.n_configs,
        "registry_trials_before": prev,
        "robustness": robs,
        "overfit": {k: v for k, v in ov.items() if k != "pbo_logits"},
        "warnings": warns,
        "generated": now_madrid(),
    }
    paths["json"].write_text(json.dumps(_jsonable(meta), indent=2, ensure_ascii=False), "utf-8")
    if registry:
        bi = rob.get("best_idx")
        best_row = (
            sw.table.iloc[int(np.ravel_multi_index(bi, sw.shape))] if bi is not None else None
        )
        pbo = ov.get("pbo", {}).get("pbo")
        key = (
            f"N={sw.n_configs} configuraciones; robustez {rob['score']:.0f}/100 en "
            f"{METRICS[metric][0]} ({rob['verdict'].split(':')[0]}); mejor "
            f"{viz.fmt_metric(metric, rob['best'])}"
            + (f" en {_params_txt(sw.axes, best_row)}" if best_row is not None else "")
            + (f"; PBO {pbo:.0%}" if pbo is not None else "")
        )
        mode = f"sweep-{sw.period}/{t.costs_mode}" + (
            "" if t.kill_switch or t.kind == "weights" else "/sin kill switch"
        )
        try:
            rel = str(paths["md"].relative_to(ROOT))
        except ValueError:
            rel = str(paths["md"])
        append_registry(registry, label, {"rejilla": axes_text(sw.axes)}, mode, key, rel)
    md = sweep_markdown(sw, meta, robs, ov, warns)
    paths["md"].write_text(md, encoding="utf-8")
    if html:
        paths["html"] = out / "mapa.html"
        write_sweep_html(sw, meta, robs, ov, warns, paths["html"])
    if png:
        try:
            fig = viz.fig_sweep_png(sw, metric, rob, title)
            paths["png"] = out / "mapa.png"
            fig.write_image(
                str(paths["png"]), width=fig.layout.width, height=fig.layout.height, scale=1
            )
        except Exception as e:  # kaleido/Chrome no disponibles
            meta["png_error"] = str(e)
    return {"paths": paths, "robustness": rob, "overfit": ov, "warnings": warns, "meta": meta}


def _row_at(sw: SweepResult, idx) -> pd.Series:
    return sw.table.iloc[int(np.ravel_multi_index(idx, sw.shape))]


def sweep_markdown(sw: SweepResult, meta: dict, robs: dict, ov: dict, warns: list[str]) -> str:
    t, metric = sw.target, meta["metric"]
    rob = robs[metric]
    a, b = t.window(sw.period)
    lab = METRICS[metric][0]
    tol = meta["tol"]
    L = [
        f"# Mapa de parámetros — {meta['title']}",
        f"Generado: {meta['generated']}",
        "",
        "> Herramienta de **robustez**, no de optimización. Enseña si el resultado aguanta "
        "al mover "
        "los parámetros (meseta) o si solo sale bien en un punto (pico). **No elijas los "
        "parámetros mirando este mapa**: eso sería sobreajustar. Todas las cifras salen de "
        "`scripts/param_sweep.py` ejecutado con el motor real.",
        "",
        "## Veredicto",
        f"**Robustez {rob['score']:.0f}/100 → {rob['verdict']}** (métrica: {lab}; «casi igual» = "
        f"dentro del {tol:.0%} del mejor).",
        "",
        "| indicador | valor | qué significa |",
        "|---|---|---|",
        f"| Mejor {lab} | {viz.fmt_metric(metric, rob['best'])} | en "
        f"{_params_txt(sw.axes, _row_at(sw, rob['best_idx']))} |",
        f"| Mediana del mapa | {viz.fmt_metric(metric, rob['median'])} | lo típico al mover los "
        "parámetros |",
        f"| Mejor / mediana | {_f(rob['best_median_ratio'])} | cerca de 1 = todo el mapa parecido; "
        "> 2 = el mejor es excepcional (sospechoso) |",
        f"| Vecinos del mejor dentro del {tol:.0%} | {_pct(rob['neighbor_share'])} "
        f"({rob['n_neighbors']} vecinos) | si se tuerce un poco un parámetro, ¿sigue bien? |",
        f"| Meseta conectada al mejor | {_pct(rob['plateau_share'])} del mapa "
        f"({rob['plateau_cells']} celdas) | tamaño de la zona buena alrededor del mejor |",
        "| Ancho de la meseta por parámetro | "
        + ", ".join(f"{k}: {_pct(rob['plateau_width'][i])}" for i, k in enumerate(sw.axes))
        + " | qué parte de cada eje cubre la zona buena |",
        f"| Combinaciones con {lab} > 0 | {_pct(rob['share_positive'])} | |",
    ]
    if "default_value" in rob:
        L.append(
            f"| Parámetros por defecto ({_params_txt(sw.axes, meta['defaults'])}) | "
            f"{viz.fmt_metric(metric, rob['default_value'])} (percentil "
            f"{_pct(rob['default_pct_rank'])}) | "
            f"{'dentro' if rob['default_in_plateau'] else 'fuera'} de la meseta del mejor; vecinos "
            f"dentro del {tol:.0%} de su valor: {_pct(rob['default_neighbor_share'])} |"
        )
    L += [
        "",
        "Fórmula de la puntuación: 100 × (0,5 · vecinos + 0,3 · min(1, meseta / 30 %) + 0,2 · "
        "mediana/mejor). ≥ 70 meseta, 40–70 mixto, < 40 pico. Es una regla práctica, no un test "
        "estadístico.",
        "",
        "### La misma prueba con otras métricas",
        "| métrica | robustez | veredicto | mejor | mediana |",
        "|---|---|---|---|---|",
    ]
    for m, r in robs.items():
        L.append(
            f"| {METRICS[m][0]} | {r['score']:.0f}/100 | {r['verdict'].split(':')[0]} | "
            f"{viz.fmt_metric(m, r.get('best'))} | {viz.fmt_metric(m, r.get('median'))} |"
        )
    L += ["", "## Sobreajuste: Deflated Sharpe y PBO"]
    d = ov.get("dsr")
    if d:
        L += [
            f"- **Deflated Sharpe Ratio (DSR) = {_f(d['dsr'], 3)}** con N = {d['n_trials']} "
            f"intentos. Probabilidad de que el Sharpe del mejor sea real y no fruto de elegir el "
            f"máximo de {d['n_trials']}. Regla habitual: fiarse solo si DSR ≥ 0,95.",
            f"  - Sharpe diario del mejor {_f(d['sr'], 4)} (anualizado ≈ "
            f"{_f(d['sr'] * np.sqrt(t.ppy))}); "
            f"Sharpe que se esperaría solo por suerte al elegir el máximo: {_f(d['sr0'], 4)} "
            f"(anualizado ≈ {_f(d['sr0'] * np.sqrt(t.ppy))}). Asimetría {_f(d['skew'])}, curtosis "
            f"{_f(d['kurt'], 1)}, {d['t']} días.",
        ]
        dr = ov.get("dsr_registry")
        if dr:
            L.append(
                f"  - Contando también lo anotado antes en el registro (N = {dr['n_trials']}): "
                f"DSR = {_f(dr['dsr'], 3)}."
            )
        L.append(
            "  - Ojo: las configuraciones vecinas están muy correladas, así que N exagera el nº de "
            "intentos independientes (el DSR sale conservador)."
        )
    p = ov.get("pbo")
    if p:
        L += [
            f"- **PBO (probabilidad de sobreajuste, CSCV) = {_pct(p['pbo'])}** sobre "
            f"{_thousands(p['n_combos'])} particiones de {p['n_blocks']} bloques. "
            "Es la frecuencia con la que la mejor configuración en una mitad de la historia "
            "queda por debajo de la mediana en la otra mitad. < 10 % bien, 10–50 % regular, "
            "≥ 50 % elegir 'la mejor' no sirve.",
            "  - Sharpe diario mediano fuera de muestra del elegido: "
            f"{_f(p['oos_sr_of_best_median'], 4)}.",
        ]
    elif ov.get("pbo_error"):
        L.append(f"- PBO no calculado: {ov['pbo_error']}")
    L += ["", f"## Las 10 mejores combinaciones por {lab}"]
    cols = list(sw.axes) + ["sharpe", "cagr", "max_dd", "mar", "expectancy_r", "trades", "exposure"]
    top = sw.table.dropna(subset=[metric]).sort_values(metric, ascending=False).head(10)
    L += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in top.iterrows():
        cells = [viz._fmt_val(r[c]) for c in sw.axes] + [
            viz.fmt_metric(c, r[c]) for c in cols[len(sw.axes) :]
        ]
        L.append("| " + " | ".join(cells) + " |")
    L += ["", "## Avisos"] + [f"- {w}" for w in warns]
    L += [
        "",
        "## Datos y configuración",
        f"- Estrategia: `{t.strategy}` ({t.label}), universo {', '.join(t.universe)}.",
        f"- Periodo: **{viz.PERIOD_ES.get(sw.period, sw.period)}** {a.date()} → {b.date()} "
        "(corte IS/OOS como `runner.py`).",
        f"- Rejilla: {axes_text(sw.axes)} = **{sw.n_configs} configuraciones** "
        f"({sw.n_computed} calculadas, {sw.n_cached} de caché). Resto de parámetros: "
        + ", ".join(f"{k}={v}" for k, v in t.params.items() if k not in sw.axes),
        f"- Reglas: {_rules_txt(t)}.",
        f"- Costes ({t.costs_mode}): {_costs_txt(t)}.",
        f"- Fuente de datos: {t.meta.get('data_source', '?')}.",
        f"- Intentos ya anotados en el registro para `{registry_label(t)}` antes de este barrido: "
        f"{meta['registry_trials_before']}.",
        "",
        "## Archivos",
        "- `sweep.csv`: una fila por combinación con todas las métricas.",
        "- `robustez.json`: puntuaciones, DSR, PBO y avisos.",
        "- `mapa.html`: interactivo (mapa de calor, superficie 3D, PBO). Ábrelo en el navegador; "
        "funciona sin internet.",
        "- `mapa.png`: preview.",
        "",
    ]
    return "\n".join(L)


def write_sweep_html(sw, meta, robs, ov, warns, path) -> Path:
    metric = meta["metric"]
    rob = robs[metric]
    figs = {}
    mets = [m for m in SWEEP_VIEWS_METRICS if sw.table[m].notna().any()]
    for m in mets:
        r = robs.get(m) or {**rob, "best_idx": None, "best": np.nan}
        figs[f"heat|{m}"] = viz.fig_heatmap(sw, m, r)
        if len(sw.axes) >= 2:
            figs[f"surf|{m}"] = viz.fig_surface(sw, m, r)
    pf = viz.fig_pbo(ov)
    if pf is not None:
        figs["pbo"] = pf
    views = [
        dict(
            id="heat",
            label="🗺️ Mapa de calor",
            per_metric=True,
            how="cada celda es una combinación de parámetros; más brillo = mejor. Recuadro "
            f"cian = <b>meseta</b> (dentro del {meta['tol']:.0%} del mejor), recuadro verde "
            "= <b>mejor</b>, recuadro blanco punteado = <b>parámetros por defecto</b>. Una "
            "mancha brillante grande = robusto; un punto suelto = pico."
            + (" Usa el deslizador de abajo para el 3.er parámetro." if len(sw.axes) == 3 else ""),
        ),
    ]
    if len(sw.axes) >= 2:
        views.append(
            dict(
                id="surf",
                label="🏔️ Superficie 3D",
                per_metric=True,
                is3d=True,
                how="la misma rejilla como un terreno. Lo que asoma por encima del plano "
                "cian es «casi tan bueno como el mejor». Una <b>meseta</b> ancha es "
                "buena señal; una <b>aguja</b> aislada es sobreajuste. Rombo verde = "
                "mejor, punto blanco = por defecto. Arrastra para girar.",
            )
        )
    if pf is not None:
        views.append(
            dict(
                id="pbo",
                label="🎲 PBO",
                how="se parte la historia en bloques; en cada partición se elige la mejor "
                "combinación en una mitad y se mira su puesto en la otra. Magenta = "
                "quedó por debajo de la mediana fuera (sobreajuste). PBO = % magenta.",
            )
        )
    best_row = _row_at(sw, rob["best_idx"])
    stats = [
        ("Robustez", f"{rob['score']:.0f}/100", _vclass(rob["score"])),
        (f"Mejor {METRICS[metric][0]}", viz.fmt_metric(metric, rob["best"]), "gold"),
        ("en", _params_txt(sw.axes, best_row), ""),
    ]
    if "default_value" in rob:
        stats.append(("Por defecto", viz.fmt_metric(metric, rob["default_value"]), ""))
    stats += [
        ("Mediana del mapa", viz.fmt_metric(metric, rob["median"]), ""),
        (f"Vecinos ≤{meta['tol']:.0%}", _pct(rob["neighbor_share"]), ""),
        ("Meseta", _pct(rob["plateau_share"]), ""),
        ("Configuraciones", str(sw.n_configs), ""),
    ]
    if ov.get("pbo"):
        pb = ov["pbo"]["pbo"]
        stats.append(("PBO", _pct(pb), "warn" if pb >= 0.5 else "good" if pb < 0.1 else ""))
    if ov.get("dsr"):
        ds = ov["dsr"]["dsr"]
        stats.append(("Deflated Sharpe", _f(ds), "good" if ds >= 0.95 else "warn"))
    a, b = sw.target.window(sw.period)
    return viz.write_tabbed_html(
        path,
        title=meta["title"],
        sub=f"Mapa de parámetros · {viz.PERIOD_ES.get(sw.period, sw.period)} "
        f"{a.date()} → {b.date()} · "
        f"{axes_text(sw.axes)} · generado {viz.now_label()} (hora de Madrid)",
        verdict=f"Robustez {rob['score']:.0f}/100 · {rob['verdict']}",
        vclass=_vclass(rob["score"]),
        stats=stats,
        views=views,
        figs=figs,
        metrics=mets,
        metric0=metric,
        warns=warns,
        footer="Backtest histórico con costes; no es una predicción. Solo paper trading. "
        "Generado con scripts/param_sweep.py.",
    )


def load_sweep(folder) -> tuple[SweepResult, dict]:
    """Relee un barrido guardado (sin re-ejecutar). ``target`` queda en None."""
    folder = Path(folder)
    meta = json.loads((folder / "robustez.json").read_text(encoding="utf-8"))
    table = pd.read_csv(folder / "sweep.csv")
    di = tuple(meta["default_idx"]) if meta.get("default_idx") is not None else None
    sw = SweepResult(
        target=None,
        axes=meta["axes"],
        period=meta["period"],
        table=table,
        returns=pd.DataFrame(),
        default_idx=di,
    )
    return sw, meta


# ====================================================================== azar


def write_random_outputs(
    rr: RandomResult,
    out: Path,
    *,
    metric: str = "sharpe",
    title: str | None = None,
    registry: Path | None = REGISTRY,
    png: bool = True,
    html: bool = True,
) -> dict:
    t = rr.target
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    title = title or f"{t.strategy} — contra el azar"
    summ = summary_table(rr)
    p = rr.p_value(metric)
    ver = p_verdict(p)
    a, b = t.window(rr.period)
    paths = {
        "csv": out / "azar.csv",
        "summary": out / "azar_resumen.csv",
        "json": out / "azar.json",
        "curves": out / "curvas.csv.gz",
        "md": out / "resumen.md",
    }
    rr.table.to_csv(paths["csv"], index=False)
    summ.to_csv(paths["summary"], index=False)
    P = rr.paths
    if not P.empty:
        from tlab.backtest.montecarlo import _downsample_idx

        idx = _downsample_idx(len(P.index), 600)
        cur = P.iloc[idx].copy()
        cur.columns = [f"mono_{c:04d}" for c in cur.columns]
        cur.insert(0, "real", rr.real_equity.reindex(P.index).ffill().iloc[idx].to_numpy())
        cur.round(2).to_csv(paths["curves"], compression="gzip")
    warns = random_warnings(rr, metric)
    meta = {
        "tool": "random_benchmark",
        "title": title,
        "strategy": t.strategy,
        "kind": t.kind,
        "universe": t.universe,
        "params": t.params,
        "period": rr.period,
        "window": [str(a), str(b)],
        "n": rr.n,
        "seed": rr.seed,
        "metric": metric,
        "kill_switch": t.kill_switch,
        "costs_mode": t.costs_mode,
        "real": rr.real,
        "p_value": p,
        "percentile": rr.percentile(metric),
        "verdict": ver,
        "match": rr.match,
        "summary": summ.to_dict(orient="records"),
        "warnings": warns,
        "generated": now_madrid(),
    }
    paths["json"].write_text(json.dumps(_jsonable(meta), indent=2, ensure_ascii=False), "utf-8")
    if registry:
        key = (
            f"{rr.n} monos (semilla {rr.seed}); {METRICS[metric][0]} real "
            f"{viz.fmt_metric(metric, rr.real[metric])}, percentil {rr.percentile(metric):.0%}, "
            f"p={p:.3f} → {ver}"
        )
        mode = f"azar-{rr.period}/{t.costs_mode}" + (
            "" if t.kill_switch or t.kind == "weights" else "/sin kill switch"
        )
        try:
            rel = str(paths["md"].relative_to(ROOT))
        except ValueError:
            rel = str(paths["md"])
        params = {k: v for k, v in t.params.items() if not isinstance(v, (list, dict))}
        append_registry(
            registry,
            f"{registry_label(t)} [benchmark azar, no es variante]",
            params,
            mode,
            key,
            rel,
        )
    paths["md"].write_text(random_markdown(rr, meta, summ, warns), encoding="utf-8")
    if html:
        paths["html"] = out / "azar.html"
        write_random_html(rr, meta, warns, paths["html"])
    if png:
        try:
            fig = viz.fig_random_png(rr, metric, title)
            paths["png"] = out / "azar.png"
            fig.write_image(
                str(paths["png"]), width=fig.layout.width, height=fig.layout.height, scale=1
            )
        except Exception as e:
            meta["png_error"] = str(e)
    return {"paths": paths, "p_value": p, "verdict": ver, "summary": summ, "meta": meta}


def random_warnings(rr: RandomResult, metric: str) -> list[str]:
    t = rr.target
    w = []
    if rr.period != "is":
        w.append(f"⚠️ Periodo **{rr.period}**: incluye out-of-sample.")
    w.append(
        "Ganarle al azar es condición **necesaria, no suficiente**: una estrategia puede batir a "
        "los monos y aun así no ganarle a comprar y mantener, o no sobrevivir al kill switch."
    )
    w.append(
        f"El p-valor es para **una** métrica ({METRICS[metric][0]}). Si miras cinco métricas, "
        "alguna saldrá 'significativa' por suerte; decide la métrica antes de mirar."
    )
    if t.kind == "signals":
        m = rr.match
        if "trades" in m and m["trades"]["azar_media"] < 0.9 * m["trades"]["real"]:
            w.append(
                f"Los monos hacen menos operaciones ({m['trades']['azar_media']:.0f}) que la real "
                f"({m['trades']['real']:.0f}): algunas entradas al azar no se pueden abrir "
                "(gap por "
                "debajo del stop o sin hueco). Compáralo con cuidado."
            )
        if (
            "exposure" in m
            and abs(m["exposure"]["azar_media"] / max(m["exposure"]["real"], 1e-9) - 1) > 0.15
        ):
            w.append(
                f"La exposición media de los monos ({m['exposure']['azar_media']:.0%}) "
                "difiere de la "
                f"real ({m['exposure']['real']:.0%}) en más de un 15 %: el CAGR no es del todo "
                "comparable; fíjate más en Sharpe y expectancy."
            )
        w.append(
            "Los monos usan las mismas duraciones (calibradas para que, tras los stops, la "
            "duración "
            "media se parezca a la real), el mismo stop que daría la estrategia ese día y el mismo "
            "sizing del 1 %. Solo cambia CUÁNDO entran."
        )
        if not t.kill_switch:
            w.append("Comparación SIN kill switch (como en las baselines).")
    else:
        w.append(
            "Los monos de una estrategia mensual tienen exactamente los mismos meses invertidos y "
            "el mismo nº de cambios; con un solo activo y pocos cambios hay pocas combinaciones "
            "distintas, así que el p-valor es grueso."
        )
    w.append("Un p-valor in-sample no garantiza nada fuera de muestra (ni en paper).")
    return w


def random_markdown(rr: RandomResult, meta: dict, summ: pd.DataFrame, warns: list[str]) -> str:
    t, metric = rr.target, meta["metric"]
    a, b = t.window(rr.period)
    L = [
        f"# ¿Mejor que el azar? — {meta['title']}",
        f"Generado: {meta['generated']}",
        "",
        f"> Se comparan los resultados de la estrategia con los de **{rr.n} estrategias al azar** "
        f"(semilla {rr.seed}) que operan lo mismo, con las mismas reglas y costes, pero entrando "
        "en momentos aleatorios. Cifras de `scripts/random_benchmark.py`.",
        "",
        "## Veredicto",
        f"**{meta['verdict'].upper()}** en {METRICS[metric][0]}: real "
        f"{viz.fmt_metric(metric, rr.real[metric])}, por encima del "
        f"{meta['percentile']:.0%} de los "
        f"monos, p-valor empírico = {meta['p_value']:.3f}.",
        "",
        "Umbrales (fijados antes de mirar): p < 0,05 → «ventaja probable»; 0,05 ≤ p < 0,10 → "
        "«indicio débil»; p ≥ 0,10 → «indistinguible del azar». p = (1 + nº de monos ≥ real) / "
        "(N + 1), una cola.",
        "",
        "## Todas las métricas",
        "| métrica | real | azar p5 | azar mediana | azar p95 | percentil real | p-valor | "
        "veredicto |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in summ.iterrows():
        m = r["metrica"]
        L.append(
            f"| {METRICS[m][0]} | {viz.fmt_metric(m, r['real'])} | "
            f"{viz.fmt_metric(m, r['azar_p5'])} | "
            f"{viz.fmt_metric(m, r['azar_mediana'])} | {viz.fmt_metric(m, r['azar_p95'])} | "
            f"{r['percentil_real']:.0%} | {r['p_valor']:.3f} | {r['veredicto']} |"
        )
    L += [
        "",
        "En la caída máxima, «mejor» = caer menos (percentil alto = el real cayó menos que "
        "los monos).",
        "",
        "## ¿Se parecen los monos a la estrategia real?",
        "| qué | real | monos (media) | monos p5–p95 |",
        "|---|---|---|---|",
    ]
    names = {
        "trades": "Nº operaciones" if t.kind == "signals" else "Nº órdenes",
        "avg_hold": "Duración media (velas)",
        "exposure": "Exposición media",
        "changes": "Cambios de asignación (rotación)",
    }
    for k, v in rr.match.items():
        if k.startswith("_"):
            continue
        fmt = (lambda x: f"{x:.0%}") if k == "exposure" else (lambda x: f"{x:.1f}")
        L.append(
            f"| {names.get(k, k)} | {fmt(v['real'])} | {fmt(v['azar_media'])} | "
            f"{fmt(v['azar_p5'])} – {fmt(v['azar_p95'])} |"
        )
    cal = rr.match.get("_calibracion", {})
    if t.kind == "signals" and cal:
        L.append(
            f"\nFactor de duración calibrado: {cal.get('factor_duracion', 1):.2f} "
            "(duración media de los pilotos: "
            f"{', '.join(f'{x:.1f}' for x in cal.get('pilotos_duracion_media', []))})."
        )
    L += ["", "## Cómo se construyen los monos"]
    if t.kind == "signals":
        L += [
            "- Mismo universo y mismo nº de operaciones por activo que la estrategia real "
            "en el periodo.",
            "- Cada operación dura lo que dura una operación real (sorteada entre las "
            "duraciones reales "
            "que no acabaron en stop), alargada por un factor calibrado con monos piloto "
            "para que la "
            "duración media **después** de los stops se parezca a la real.",
            "- Entradas colocadas al azar sin solaparse; stop = el `stop_price` que la estrategia "
            "daría ese día (cierre − k·ATR); mismo sizing al 1 %, máx. posiciones, costes y "
            "kill switch (si está activado) vía `portfolio_sim`.",
        ]
    else:
        L += [
            "- Se trocea la asignación real en tramos de meses con la misma cartera.",
            "- Cada mono usa las mismas carteras, el mismo nº de tramos (misma rotación) y los "
            "mismos meses en cada cartera; solo cambia el orden y la longitud de los tramos.",
            "- Se simula con `allocation_sim` (decisión a fin de mes, ejecución en la apertura "
            "siguiente, mismos costes).",
        ]
    L += ["", "## Avisos"] + [f"- {w}" for w in warns]
    L += [
        "",
        "## Datos y configuración",
        f"- Estrategia: `{t.strategy}`, universo {', '.join(t.universe)}, parámetros "
        + ", ".join(f"{k}={v}" for k, v in t.params.items())
        + ".",
        f"- Periodo: **{viz.PERIOD_ES.get(rr.period, rr.period)}** {a.date()} → {b.date()}.",
        f"- Reglas: {_rules_txt(t)}.",
        f"- Costes ({t.costs_mode}): {_costs_txt(t)}.",
        f"- Fuente de datos: {t.meta.get('data_source', '?')}.",
        "",
        "## Archivos",
        "- `azar.csv`: métricas de cada mono · `azar_resumen.csv`: la tabla de arriba.",
        "- `curvas.csv.gz`: equity real y de los primeros monos (submuestreada).",
        "- `azar.html`: interactivo (histograma, violines, espaguetis) · `azar.png`: preview.",
        "",
    ]
    return "\n".join(L)


def write_random_html(rr: RandomResult, meta: dict, warns: list[str], path) -> Path:
    metric = meta["metric"]
    mets = [
        m
        for m in COMPARE
        if m in rr.table and rr.table[m].notna().any() and np.isfinite(rr.real.get(m, np.nan))
    ]
    figs = {f"hist|{m}": viz.fig_random_hist(rr, m) for m in mets}
    figs["violin"] = viz.fig_random_violin(rr)
    figs["paths"] = viz.fig_random_paths(rr)
    views = [
        dict(
            id="hist",
            label="📊 Distribución",
            per_metric=True,
            how="cada barra cuenta cuántos monos sacaron ese resultado. La línea dorada es la "
            "estrategia real. Si está a la derecha del todo (percentil alto, p pequeño), le "
            "gana al azar; si cae en medio del montón, no se distingue.",
        ),
        dict(
            id="violin",
            label="🎻 Violines",
            how="la forma de cada violín es el reparto de los monos en esa métrica; el diamante "
            "dorado es la real. Arriba del violín = mejor que casi todos.",
        ),
        dict(
            id="paths",
            label="🍝 Curvas",
            how="cada hilo es la cuenta de un mono (rojo = peor final, verde = mejor). La línea "
            "dorada es la estrategia real. Escala logarítmica.",
        ),
    ]
    p, pr = meta["p_value"], meta["percentile"]
    vc = "good" if p < 0.05 else "mid" if p < 0.10 else "bad"
    stats = [
        ("Veredicto", meta["verdict"], vc),
        (f"{METRICS[metric][0]} real", viz.fmt_metric(metric, rr.real[metric]), "gold"),
        ("Percentil real", f"{pr:.0%}", ""),
        ("p-valor", f"{p:.3f}", vc),
        ("Mediana azar", viz.fmt_metric(metric, float(rr.table[metric].median())), ""),
        ("Monos", f"{rr.n:,}".replace(",", "."), ""),
    ]
    for k in ("trades", "avg_hold", "exposure", "changes"):
        if k in rr.match:
            v = rr.match[k]
            f = (lambda x: f"{x:.0%}") if k == "exposure" else (lambda x: f"{x:.0f}")
            lab = {
                "trades": "Operaciones",
                "avg_hold": "Duración (velas)",
                "exposure": "Exposición",
                "changes": "Cambios",
            }[k]
            stats.append((f"{lab} real / azar", f"{f(v['real'])} / {f(v['azar_media'])}", ""))
    a, b = rr.target.window(rr.period) if rr.target is not None else (None, None)
    per = f"{a.date()} → {b.date()}" if a is not None else ""
    return viz.write_tabbed_html(
        path,
        title=meta["title"],
        sub=f"Contra {rr.n} estrategias al azar · {viz.PERIOD_ES.get(rr.period, rr.period)} "
        f"{per} · semilla {rr.seed} · "
        f"generado {viz.now_label()} (hora de Madrid)",
        verdict=f"{meta['verdict']} · p = {p:.3f} en {METRICS[metric][0]}",
        vclass=vc,
        stats=stats,
        views=views,
        figs=figs,
        metrics=mets,
        metric0=metric,
        warns=warns,
        footer="Backtest histórico con costes; no es una predicción. Solo paper trading. "
        "Generado con scripts/random_benchmark.py.",
    )


def load_random(folder) -> tuple[RandomResult, dict]:
    """Relee un benchmark guardado (sin re-ejecutar). ``target`` queda en None."""
    folder = Path(folder)
    meta = json.loads((folder / "azar.json").read_text(encoding="utf-8"))
    table = pd.read_csv(folder / "azar.csv")
    real_eq, paths = pd.Series(dtype=float), pd.DataFrame()
    cp = folder / "curvas.csv.gz"
    if cp.exists():
        cur = pd.read_csv(cp, index_col=0, parse_dates=True, compression="gzip")
        real_eq = cur.pop("real")
        paths = cur
        paths.columns = range(paths.shape[1])
    real = {k: (np.nan if v is None else v) for k, v in meta["real"].items()}
    rr = RandomResult(
        target=None,
        period=meta["period"],
        n=meta["n"],
        seed=meta["seed"],
        real=real,
        real_equity=real_eq,
        table=table,
        paths=paths,
        match=meta.get("match", {}),
    )
    return rr, meta


def rob_from_meta(meta: dict, metric: str) -> dict:
    """Robustez guardada en robustez.json, con ``best_idx`` como tupla (para los gráficos)."""
    rob = dict(meta["robustness"][metric])
    if rob.get("best_idx") is not None:
        rob["best_idx"] = tuple(rob["best_idx"])
    for k in ("best", "median", "best_median_ratio", "neighbor_share", "plateau_share"):
        if rob.get(k) is None:
            rob[k] = float("nan")
    rob["plateau_width"] = {int(k): v for k, v in rob.get("plateau_width", {}).items()}
    return rob


def list_outputs(kind: str, root: Path | None = None) -> list[Path]:
    """Carpetas de barridos (``sweep``) o benchmarks al azar (``azar``) en reports/robustez."""
    root = root or ROOT / "reports" / "robustez"
    name = {"sweep": "robustez.json", "azar": "azar.json"}[kind]
    if not root.exists():
        return []
    return sorted({p.parent for p in root.rglob(name)}, key=lambda p: p.name, reverse=True)
