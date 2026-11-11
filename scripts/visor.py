"""Visor local de robustez (Streamlit): Monte Carlo, mapa de parámetros y contra el azar.

    uv sync --extra visor
    uv run streamlit run scripts/visor.py
    # (el comando antiguo sigue funcionando y abre lo mismo)
    uv run streamlit run scripts/visor_montecarlo.py

Lee lo ya generado en reports/ y permite lanzar barridos o benchmarks nuevos, SOLO in-sample.
Cada barrido nuevo se anota en docs/registro_pruebas.md (cuenta como variantes probadas).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from tlab.backtest import robust_viz as viz  # noqa: E402
from tlab.backtest.robust_reports import (  # noqa: E402
    list_outputs,
    load_random,
    load_sweep,
    rob_from_meta,
)
from tlab.backtest.targets import METRICS  # noqa: E402
from tlab.config import ROOT  # noqa: E402

TABS = ["🎲 Monte Carlo", "🗺️ Mapa de parámetros", "🐒 Contra el azar"]


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _warns(st, warns: list[str]) -> None:
    with st.expander("⚠️ Avisos (léelos antes de creerte nada)", expanded=True):
        for w in warns:
            st.markdown(f"- {w}")


def render_sweep_tab(st) -> None:
    """Pestaña del mapa de sensibilidad de parámetros."""
    st.caption(
        "¿La estrategia vive en una **meseta** (robusta) o en un **pico** (sobreajuste)? "
        "No elijas parámetros mirando el mapa: sirve para ver la forma."
    )
    with st.expander("➕ Nuevo barrido (in-sample, se anota en el registro)"):
        _new_sweep_form(st)
    runs = list_outputs("sweep")
    if not runs:
        st.info(
            "Aún no hay barridos. Corre `uv run python scripts/param_sweep.py --preset donchian`."
        )
        return
    choice = st.selectbox("Barrido", [_rel(p) for p in runs], key="sweep_run")
    sw, meta = load_sweep(ROOT / choice if not Path(choice).is_absolute() else Path(choice))
    mets = [m for m in meta["robustness"]]
    metric = st.selectbox(
        "Métrica",
        mets,
        index=mets.index(meta["metric"]) if meta["metric"] in mets else 0,
        format_func=lambda m: METRICS[m][0],
        key="sweep_metric",
    )
    rob = rob_from_meta(meta, metric)
    st.subheader(meta["title"])
    c = st.columns(4)
    c[0].metric("Robustez", f"{rob['score']:.0f}/100")
    c[1].metric(f"Mejor {METRICS[metric][0]}", viz.fmt_metric(metric, rob["best"]))
    c[2].metric("Mediana del mapa", viz.fmt_metric(metric, rob["median"]))
    ov = meta.get("overfit", {})
    pbo = (ov.get("pbo") or {}).get("pbo")
    c[3].metric("PBO", f"{pbo:.0%}" if pbo is not None else "—")
    st.write(
        f"**Veredicto:** {rob['verdict']} · {meta['n_configs']} configuraciones · periodo "
        f"{viz.PERIOD_ES.get(meta['period'], meta['period'])}"
    )
    t1, t2 = st.tabs(["Mapa de calor", "Superficie 3D"])
    with t1:
        f = viz.fig_heatmap(sw, metric, rob)
        f.update_layout(height=620)
        st.plotly_chart(f, use_container_width=True)
    with t2:
        f = viz.fig_surface(sw, metric, rob)
        if f is None:
            st.info("Con un solo parámetro no hay superficie.")
        else:
            f.update_layout(height=650)
            st.plotly_chart(f, use_container_width=True)
    top = sw.table.dropna(subset=[metric]).sort_values(metric, ascending=False).head(10)
    st.dataframe(top, use_container_width=True)
    _warns(st, meta.get("warnings", []))
    md = Path(ROOT / choice) / "resumen.md"
    if md.exists():
        with st.expander("resumen.md"):
            st.markdown(md.read_text(encoding="utf-8"))


def _new_sweep_form(st) -> None:
    from tlab.backtest.param_sweep import PRESETS, parse_axis, run_sweep
    from tlab.backtest.robust_reports import out_dir_for, write_sweep_outputs
    from tlab.backtest.targets import build_target

    with st.form("new_sweep"):
        preset = st.selectbox(
            "Preset", list(PRESETS), format_func=lambda k: f"{k} — {PRESETS[k]['title']}"
        )
        pre = PRESETS[preset]
        grid = st.text_area("Rejilla (una línea por parámetro)", "\n".join(pre["grid"]))
        kill = st.checkbox("Kill switch activado", value=pre.get("kill_switch", True))
        metric = st.selectbox("Métrica", ["sharpe", "cagr", "max_dd", "mar", "expectancy_r"])
        go = st.form_submit_button("Ejecutar barrido in-sample", type="primary")
    if not go:
        return
    t = build_target(pre["strategy"], pre.get("universe"), kill_switch=kill, start=pre.get("start"))
    lines = [g.strip() for g in grid.splitlines() if g.strip()]
    axes = dict(parse_axis(g, t.params.get(g.split("=")[0].strip())) for g in lines)
    with st.spinner("Barriendo (en paralelo, con caché)…"):
        sw = run_sweep(t, axes, "is")
        res = write_sweep_outputs(
            sw, out_dir_for(t, "sweep", "is"), metric=metric, title=pre["title"]
        )
    st.success(
        f"Robustez {res['robustness']['score']:.0f}/100 · guardado en "
        f"{_rel(res['paths']['md'].parent)} (elígelo abajo)"
    )


def render_random_tab(st) -> None:
    """Pestaña del benchmark contra estrategias al azar."""
    st.caption(
        "¿Le gana a un mono que opera lo mismo (nº de operaciones, duración, stops, sizing y "
        "costes) pero entrando al azar?"
    )
    with st.expander("➕ Nuevo benchmark (in-sample)"):
        _new_random_form(st)
    runs = list_outputs("azar")
    if not runs:
        st.info(
            "Aún no hay benchmarks. Corre `uv run python scripts/random_benchmark.py "
            "--preset donchian`."
        )
        return
    choice = st.selectbox("Benchmark", [_rel(p) for p in runs], key="rand_run")
    rr, meta = load_random(ROOT / choice)
    mets = [m["metrica"] for m in meta["summary"]]
    metric = st.selectbox(
        "Métrica",
        mets,
        index=mets.index(meta["metric"]) if meta["metric"] in mets else 0,
        format_func=lambda m: METRICS[m][0],
        key="rand_metric",
    )
    st.subheader(meta["title"])
    from tlab.backtest.random_benchmark import p_verdict

    p = rr.p_value(metric)
    c = st.columns(4)
    c[0].metric("Veredicto", p_verdict(p))
    c[1].metric(f"{METRICS[metric][0]} real", viz.fmt_metric(metric, rr.real[metric]))
    c[2].metric("Percentil real", f"{rr.percentile(metric):.0%}")
    c[3].metric("p-valor", f"{p:.3f}")
    t1, t2, t3 = st.tabs(["Distribución", "Violines", "Curvas"])
    with t1:
        f = viz.fig_random_hist(rr, metric)
        if f is not None:
            f.update_layout(height=480)
            st.plotly_chart(f, use_container_width=True)
    with t2:
        f = viz.fig_random_violin(rr)
        f.update_layout(height=480)
        st.plotly_chart(f, use_container_width=True)
    with t3:
        f = viz.fig_random_paths(rr)
        if f is not None:
            f.update_layout(height=560)
            st.plotly_chart(f, use_container_width=True)
    import pandas as pd

    st.dataframe(pd.DataFrame(meta["summary"]), use_container_width=True)
    _warns(st, meta.get("warnings", []))


def _new_random_form(st) -> None:
    from random_benchmark import PRESETS

    from tlab.backtest.random_benchmark import run_random_benchmark
    from tlab.backtest.robust_reports import out_dir_for, write_random_outputs
    from tlab.backtest.targets import build_target

    with st.form("new_random"):
        preset = st.selectbox(
            "Preset", list(PRESETS), format_func=lambda k: f"{k} — {PRESETS[k]['title']}"
        )
        n = st.number_input("Monos (N)", min_value=50, max_value=5000, value=500, step=50)
        seed = st.number_input("Semilla", min_value=0, value=42, step=1)
        go = st.form_submit_button("Ejecutar in-sample", type="primary")
    if not go:
        return
    pre = PRESETS[preset]
    t = build_target(
        pre["strategy"],
        pre.get("universe"),
        kill_switch=pre.get("kill_switch", True),
        start=pre.get("start"),
    )
    with st.spinner("Simulando monos…"):
        rr = run_random_benchmark(t, int(n), int(seed))
        res = write_random_outputs(rr, out_dir_for(t, "azar", "is"), title=pre["title"])
    st.success(
        f"{res['verdict']} (p = {res['p_value']:.3f}) · guardado en "
        f"{_rel(res['paths']['md'].parent)}"
    )


def main() -> None:
    try:
        import streamlit as st
    except ImportError:
        print(
            "Falta Streamlit. Instálalo en este proyecto con:\n"
            "  uv sync --extra visor\n"
            "y lanza:\n"
            "  uv run streamlit run scripts/visor.py"
        )
        sys.exit(1)
    from visor_montecarlo import render_montecarlo_tab

    st.set_page_config(page_title="Robustez — trading-lab", layout="wide")
    st.title("Visor de robustez")
    t_mc, t_sw, t_rb = st.tabs(TABS)
    with t_mc:
        render_montecarlo_tab(st)
    with t_sw:
        render_sweep_tab(st)
    with t_rb:
        render_random_tab(st)


if __name__ == "__main__":
    main()
