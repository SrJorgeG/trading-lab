"""Visor local de Monte Carlo (Streamlit).

Pensado como pestaña futura del visualizador de estrategias: la lógica útil
está en ``render_montecarlo_tab``. Hoy se lanza solo:

    uv sync --extra visor
    uv run streamlit run scripts/visor_montecarlo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tlab.backtest.montecarlo import (  # noqa: E402
    DEFAULT_BLOCK,
    DEFAULT_N,
    DEFAULT_SEED,
    METHODS,
    MCConfig,
    load_run,
    luck_comment,
    run_montecarlo,
    stats_table,
)
from tlab.config import ROOT  # noqa: E402


def list_runs() -> list[Path]:
    reports = ROOT / "reports"
    if not reports.exists():
        return []
    return sorted({p.parent for p in reports.rglob("equity.csv")})


def render_montecarlo_tab(st, run_dir: Path | None = None) -> None:
    """Cuerpo reutilizable (una pestaña del visor de estrategias, cuando exista)."""
    st.caption(
        "Esto es un visor mínimo de robustez. Más adelante podrá ser una pestaña "
        "del visualizador de estrategias."
    )
    runs = list_runs()
    if not runs:
        st.warning(
            "No hay backtests con equity.csv en reports/. Corre uno o usa --prepare-baselines."
        )
        return
    labels = []
    for p in runs:
        try:
            labels.append(str(p.relative_to(ROOT)))
        except ValueError:
            labels.append(str(p))
    default = 0
    if run_dir is not None:
        for i, p in enumerate(runs):
            if p.resolve() == Path(run_dir).resolve():
                default = i
                break
    choice = st.selectbox("Backtest", labels, index=default)
    folder = runs[labels.index(choice)]
    c1, c2, c3, c4 = st.columns(4)
    method = c1.selectbox("Método", METHODS, index=0)
    n = c2.number_input(
        "Simulaciones (N)", min_value=100, max_value=20_000, value=DEFAULT_N, step=100
    )
    seed = c3.number_input("Semilla", min_value=0, value=DEFAULT_SEED, step=1)
    block = c4.number_input("Longitud de bloque", min_value=1, value=DEFAULT_BLOCK, step=1)
    if not st.button("Simular", type="primary"):
        st.info("Elige parámetros y pulsa Simular. Con N=5000 tarda unos segundos.")
        return
    equity, trades, meta = load_run(folder)
    cfg = MCConfig(n=int(n), seed=int(seed), method=method, block_length=int(block))
    try:
        result = run_montecarlo(equity, trades, cfg)
    except ValueError as e:
        st.error(str(e))
        return
    st.subheader(meta.get("title", folder.name))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("P(kill switch)", f"{result.p_kill:.1%}")
    k2.metric("P(bajo el inicio)", f"{result.p_below_start:.1%}")
    k3.metric("P(ruina 20 %)", f"{result.p_ruin:.1%}")
    k4.metric("CAGR backtest", f"{result.real['cagr']:.1%}")
    st.write(luck_comment(result))
    try:
        import plotly.graph_objects as go

        from tlab.backtest.montecarlo import _x_values

        x = _x_values(result)
        fig = go.Figure()
        b = result.bands
        fig.add_trace(
            go.Scatter(
                x=list(x) + list(x[::-1]),
                y=list(b["p95"]) + list(b["p5"][::-1]),
                fill="toself",
                fillcolor="rgba(31,119,180,0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name="p5–p95",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=list(x) + list(x[::-1]),
                y=list(b["p75"]) + list(b["p25"][::-1]),
                fill="toself",
                fillcolor="rgba(31,119,180,0.3)",
                line=dict(color="rgba(0,0,0,0)"),
                name="p25–p75",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(x=x, y=b["p50"], mode="lines", name="mediana", line=dict(dash="dash"))
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=result.real_path.to_numpy(),
                mode="lines",
                name="backtest",
                line=dict(color="rgb(214,39,40)", width=2),
            )
        )
        fig.update_layout(height=420, template="plotly_white", margin=dict(l=40, r=20, t=30, b=40))
        st.plotly_chart(fig, use_container_width=True)
        c1, c2 = st.columns(2)
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Histogram(x=result.max_dd * 100, nbinsx=40, name="DD"))
        fig_dd.add_vline(x=-cfg.kill_switch * 100, line_dash="dash", line_color="red")
        fig_dd.update_layout(title="Máx. drawdown (%)", height=320, template="plotly_white")
        c1.plotly_chart(fig_dd, use_container_width=True)
        fig_cg = go.Figure()
        fig_cg.add_trace(go.Histogram(x=result.cagr * 100, nbinsx=40, name="CAGR"))
        fig_cg.add_vline(x=result.real["cagr"] * 100, line_dash="dot", line_color="green")
        fig_cg.update_layout(title="CAGR (%)", height=320, template="plotly_white")
        c2.plotly_chart(fig_cg, use_container_width=True)
    except ImportError:
        st.write("Instala plotly para ver los gráficos.")
    st.dataframe(stats_table(result), use_container_width=True)
    with st.expander("Advertencias"):
        for n in result.notes:
            st.markdown(f"- {n}")


def main() -> None:
    try:
        import streamlit as st
    except ImportError:
        print(
            "Falta Streamlit. Instálalo en este proyecto con:\n"
            "  uv sync --extra visor\n"
            "y lanza:\n"
            "  uv run streamlit run scripts/visor_montecarlo.py"
        )
        sys.exit(1)
    st.set_page_config(page_title="Monte Carlo — trading-lab", layout="wide")
    st.title("Visor Monte Carlo")
    render_montecarlo_tab(st)


if __name__ == "__main__":
    main()
