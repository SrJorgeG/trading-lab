"""Gráficos (tema oscuro neón, como el Monte Carlo 3D) del mapa de parámetros y del benchmark
al azar, y un HTML autocontenido con pestañas que se ve bien en el móvil."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tlab.backtest.montecarlo3d import BG, FG, GOLD, GRID, NEON_OUTCOME
from tlab.backtest.targets import METRICS

PERIOD_ES = {"is": "in-sample", "oos": "out-of-sample", "full": "periodo completo"}
CYAN = "#00e5ff"
BEST = "#00ff8c"  # verde neón: se distingue de la paleta del mapa
MAGENTA = "#ff3d9a"
VIOLET = "#a46bff"
MUTED = "#8f9bd0"
# Mapa de calor: violeta oscuro (peor) → magenta → naranja → amarillo (mejor). Sin negro puro
# para que las celdas malas no se confundan con el fondo.
NEON_HEAT = [
    [0.00, "#1b0f45"],
    [0.18, "#3d0f7a"],
    [0.38, "#8e1aa8"],
    [0.58, "#ff2e88"],
    [0.78, "#ff9f1c"],
    [1.00, "#fff36b"],
]
FONT = "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"

PARAM_ES = {
    "entry_n": "Ventana de entrada (velas)",
    "exit_n": "Ventana de salida (velas)",
    "atr_mult": "Stop (× ATR)",
    "atr_n": "ATR (velas)",
    "months": "Lookback (meses)",
    "skip": "Meses saltados",
    "fast": "Media rápida",
    "slow": "Media lenta",
}


def pname(k: str) -> str:
    return PARAM_ES.get(k, k)


def fmt_metric(metric: str, v) -> str:
    if v is None or not np.isfinite(v):
        return "—"
    kind = METRICS.get(metric, ("", "f2", True))[1]
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "int":
        return f"{int(round(v))}"
    return f"{v:.{kind[1]}f}"


def _fmt_val(v) -> str:
    return f"{v:g}" if isinstance(v, (int, float, np.floating, np.integer)) else str(v)


def _base_layout(**kw) -> dict:
    d = dict(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family=FONT, color=FG, size=13),
        margin=dict(l=60, r=20, t=40, b=55),
        legend=dict(
            bgcolor="rgba(5,6,15,0.6)", bordercolor=GRID, borderwidth=1, font=dict(size=11)
        ),
        hoverlabel=dict(bgcolor="#0d1230", bordercolor=CYAN, font=dict(color="#fff")),
        uirevision="keep",
    )
    d.update(kw)
    return d


def _axis(title: str, **kw) -> dict:
    d = dict(
        title=dict(text=title, font=dict(size=14, color=FG)),
        gridcolor=GRID,
        zerolinecolor=GRID,
        linecolor=GRID,
        tickfont=dict(size=12, color="#9aa6dc"),
    )
    d.update(kw)
    return d


# ====================================================================== barrido de parámetros


def _cat_axis(title: str, vals, **kw) -> dict:
    """Eje con posiciones 0..n-1 y etiquetas = valores del parámetro (sin ambigüedad)."""
    return _axis(
        title,
        tickmode="array",
        tickvals=list(range(len(vals))),
        ticktext=[_fmt_val(v) for v in vals],
        range=[-0.5, len(vals) - 0.5],
        showgrid=False,
        zeroline=False,
        **kw,
    )


def _slices(sw) -> list[tuple[str, tuple | None]]:
    """Cortes a pintar: uno (2D/1D) o uno por valor del 3.er parámetro."""
    names = list(sw.axes)
    if len(names) < 3:
        return [("", None)]
    k = names[2]
    return [(f"{pname(k)} = {_fmt_val(v)}", (2, i)) for i, v in enumerate(sw.axes[k])]


def _slice2d(arr: np.ndarray, sl) -> np.ndarray:
    return arr if sl is None else np.take(arr, sl[1], axis=sl[0])


def _default_slice(sw, rob) -> int:
    if len(sw.axes) < 3:
        return 0
    if sw.default_idx is not None:
        return sw.default_idx[2]
    return rob["best_idx"][2] if rob.get("best_idx") else 0


def _plateau_mask(sw, metric: str, rob: dict) -> np.ndarray:
    raw = sw.grid(metric)
    if rob.get("best_idx") is None:
        return np.zeros_like(raw, bool)
    best, tol = rob["best"], rob["tol"]
    if metric == "max_dd":
        return np.isfinite(raw) & (np.abs(raw) <= abs(best) / (1 - tol))
    return np.isfinite(raw) & (raw >= best - tol * abs(best))


def fig_heatmap(sw, metric: str, rob: dict, *, big: bool = False):
    """Mapa de calor 2D (filas = 1.er parámetro, columnas = 2.º); con 3 parámetros, un
    deslizador elige el valor del 3.º. 1 parámetro → barras.

    Marcas (rectángulos sobre la celda): cian = meseta (dentro del tol del mejor), dorado
    grueso = mejor, blanco discontinuo = parámetros por defecto.
    """
    import plotly.graph_objects as go

    names = list(sw.axes)
    if len(names) == 1:
        return _fig_line(sw, metric, rob)
    raw = sw.grid(metric)
    label = METRICS[metric][0]
    ya, xa = sw.axes[names[0]], sw.axes[names[1]]
    plateau = _plateau_mask(sw, metric, rob)
    finite = raw[np.isfinite(raw)]
    zmin, zmax = (float(finite.min()), float(finite.max())) if len(finite) else (0.0, 1.0)
    span = zmax - zmin if zmax > zmin else 1e-9
    ncell = raw.shape[0] * raw.shape[1]
    fs = 17 if big else (11 if ncell <= 120 else 9)
    slices = _slices(sw)
    d0 = _default_slice(sw, rob)
    fig = go.Figure()
    layouts = []
    for si, (_title, sl) in enumerate(slices):
        z = _slice2d(raw, sl)
        pm = _slice2d(plateau, sl)
        txt = [[fmt_metric(metric, v) for v in row] for row in z]
        fig.add_trace(
            go.Heatmap(
                z=z,
                x=list(range(len(xa))),
                y=list(range(len(ya))),
                zmin=zmin,
                zmax=zmax,
                colorscale=NEON_HEAT,
                xgap=2,
                ygap=2,
                text=txt,
                customdata=[[[_fmt_val(yv), _fmt_val(xv)] for xv in xa] for yv in ya],
                hovertemplate=(
                    f"{pname(names[0])}: %{{customdata[0]}}<br>"
                    f"{pname(names[1])}: %{{customdata[1]}}<br>"
                    f"{label}: %{{text}}<extra></extra>"
                ),
                colorbar=dict(
                    title=dict(text=label, side="right", font=dict(size=12)),
                    thickness=12,
                    tickfont=dict(size=11, color="#9aa6dc"),
                    outlinewidth=0,
                    tickformat=".0%" if METRICS[metric][1] == "pct" else None,
                ),
                visible=si == d0,
                name=label,
            )
        )
        shapes, anns = [], []

        def rect(r, c, color, width, inset, dash="solid", shapes=shapes):
            shapes.append(
                dict(
                    type="rect",
                    xref="x",
                    yref="y",
                    x0=c - 0.5 + inset,
                    x1=c + 0.5 - inset,
                    y0=r - 0.5 + inset,
                    y1=r + 0.5 - inset,
                    line=dict(color=color, width=width, dash=dash),
                    layer="above",
                )
            )

        for r, c in zip(*np.nonzero(pm), strict=True):
            rect(int(r), int(c), CYAN, 2, 0.06)
        bi = rob.get("best_idx")
        if bi is not None and (sl is None or bi[2] == sl[1]):
            rect(bi[0], bi[1], BEST, 5 if big else 4, 0.02)
        di = sw.default_idx
        if di is not None and (sl is None or di[2] == sl[1]):
            rect(di[0], di[1], "#ffffff", 3 if big else 2.5, 0.14, "dot")
        for r in range(len(ya)):
            for c in range(len(xa)):
                v = z[r, c]
                if not np.isfinite(v):
                    continue
                bright = (v - zmin) / span > 0.62
                anns.append(
                    dict(
                        x=c,
                        y=r,
                        text=fmt_metric(metric, v),
                        showarrow=False,
                        font=dict(size=fs, color="#14092e" if bright else "#e9ecff"),
                    )
                )
        layouts.append({"shapes": shapes, "annotations": anns})
    # Entradas de leyenda (trazas vacías con el estilo de cada marca).
    for name, color, _dash in (
        (f"meseta (≥ {1 - rob['tol']:.0%} del mejor)", CYAN, "solid"),
        ("mejor", BEST, "solid"),
        ("por defecto", "#ffffff", "dot"),
    ):
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=name,
                hoverinfo="skip",
                marker=dict(
                    symbol="square-open", size=14, color=color, line=dict(width=3, color=color)
                ),
            )
        )
    n = len(slices)
    fig.update_layout(
        **_base_layout(
            xaxis=_cat_axis(pname(names[1]), xa),
            yaxis=_cat_axis(pname(names[0]), ya),
            shapes=layouts[d0]["shapes"],
            annotations=layouts[d0]["annotations"],
            legend=dict(
                orientation="h",
                x=0,
                y=1.02,
                yanchor="bottom",
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=11),
            ),
            margin=dict(l=70, r=10, t=50, b=60 if n == 1 else 120),
        )
    )
    if n > 1:
        nleg = 3
        steps = []
        for si in range(n):
            vis = [i == si for i in range(n)] + [True] * nleg
            steps.append(
                dict(
                    method="update",
                    label=_fmt_val(sw.axes[names[2]][si]),
                    args=[{"visible": vis}, layouts[si]],
                )
            )
        fig.update_layout(sliders=[_slider(steps, d0, pname(names[2]), pad=45)])
    return fig


def _slider(steps, active, prefix, pad=35) -> dict:
    return dict(
        active=active,
        steps=steps,
        currentvalue=dict(prefix=f"{prefix}: ", font=dict(color=GOLD, size=13)),
        pad=dict(t=pad),
        bgcolor="#0d1230",
        activebgcolor=CYAN,
        bordercolor=GRID,
        font=dict(color=FG),
    )


def _fig_line(sw, metric: str, rob: dict):
    import plotly.graph_objects as go

    name = list(sw.axes)[0]
    xs = sw.axes[name]
    y = sw.grid(metric)
    pm = _plateau_mask(sw, metric, rob)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[_fmt_val(v) for v in xs],
            y=y,
            marker=dict(color=[CYAN if p else VIOLET for p in pm], line=dict(width=0)),
            text=[fmt_metric(metric, v) for v in y],
            textposition="outside",
            name=METRICS[metric][0],
        )
    )
    bi, di = rob.get("best_idx"), sw.default_idx
    if bi is not None:
        fig.add_trace(
            go.Scatter(
                x=[_fmt_val(xs[bi[0]])],
                y=[y[bi]],
                mode="markers",
                marker=dict(symbol="diamond", size=16, color=GOLD),
                name="mejor",
            )
        )
    if di is not None:
        fig.add_trace(
            go.Scatter(
                x=[_fmt_val(xs[di[0]])],
                y=[y[di]],
                mode="markers",
                marker=dict(symbol="circle-open", size=20, color="#fff", line=dict(width=3)),
                name="por defecto",
            )
        )
    fig.update_layout(
        **_base_layout(xaxis=_axis(pname(name), type="category"), yaxis=_axis(METRICS[metric][0]))
    )
    return fig


def fig_surface(sw, metric: str, rob: dict):
    """Superficie 3D: una meseta ancha = robusto; una aguja = sobreajuste. El plano cian marca
    el umbral de "casi tan bueno como el mejor"."""
    import plotly.graph_objects as go

    from tlab.backtest.montecarlo3d import _scene

    names = list(sw.axes)
    if len(names) < 2:
        return None
    raw = sw.grid(metric)
    ya, xa = sw.axes[names[0]], sw.axes[names[1]]
    finite = raw[np.isfinite(raw)]
    zmin, zmax = (float(finite.min()), float(finite.max())) if len(finite) else (0, 1)
    best, tol = rob.get("best", np.nan), rob["tol"]
    thr = (
        (best / (1 - tol) if metric == "max_dd" else best - tol * abs(best))
        if np.isfinite(best)
        else np.nan
    )
    pct = METRICS[metric][1] == "pct"
    mult = 100.0 if pct else 1.0
    zlab = METRICS[metric][0] + (" (%)" if pct else "")
    fig = go.Figure()
    slices = _slices(sw)
    d0 = _default_slice(sw, rob)
    per = 4
    for si, (_t, sl) in enumerate(slices):
        z = _slice2d(raw, sl) * mult
        vis = si == d0
        fig.add_trace(
            go.Surface(
                x=np.asarray(xa, float),
                y=np.asarray(ya, float),
                z=z,
                cmin=zmin * mult,
                cmax=zmax * mult,
                colorscale=NEON_HEAT,
                opacity=0.97,
                showscale=False,
                contours=dict(
                    z=dict(show=True, usecolormap=True, project=dict(z=True), width=2),
                    x=dict(show=True, color="rgba(215,222,250,0.18)", width=1),
                    y=dict(show=True, color="rgba(215,222,250,0.18)", width=1),
                ),
                lighting=dict(ambient=0.55, diffuse=0.7, specular=0.35, roughness=0.5, fresnel=0.2),
                hovertemplate=(
                    f"{pname(names[1])}: %{{x}}<br>{pname(names[0])}: %{{y}}<br>"
                    f"{METRICS[metric][0]}: %{{z:.2f}}<extra></extra>"
                ),
                name=METRICS[metric][0],
                visible=vis,
            )
        )
        fig.add_trace(
            go.Surface(
                x=[float(min(xa)), float(max(xa))],
                y=[float(min(ya)), float(max(ya))],
                z=np.full((2, 2), thr * mult),
                colorscale=[[0, CYAN], [1, CYAN]],
                opacity=0.22,
                showscale=False,
                hoverinfo="skip",
                name=f"umbral meseta ({1 - tol:.0%} del mejor)",
                showlegend=si == d0,
                visible=vis,
            )
        )
        bi = rob.get("best_idx")
        on = bi is not None and (sl is None or bi[2] == sl[1])
        fig.add_trace(
            go.Scatter3d(
                x=[float(xa[bi[1]])] if on else [],
                y=[float(ya[bi[0]])] if on else [],
                z=[float(raw[bi]) * mult + 0.03 * (zmax - zmin) * mult] if on else [],
                mode="markers",
                marker=dict(symbol="diamond", size=9, color=BEST, line=dict(width=2, color="#fff")),
                name="mejor",
                visible=vis,
            )
        )
        di = sw.default_idx
        on = di is not None and (sl is None or di[2] == sl[1])
        fig.add_trace(
            go.Scatter3d(
                x=[float(xa[di[1]])] if on else [],
                y=[float(ya[di[0]])] if on else [],
                z=[float(raw[di]) * mult + 0.03 * (zmax - zmin) * mult] if on else [],
                mode="markers",
                marker=dict(
                    symbol="circle", size=8, color="#ffffff", line=dict(width=2, color=CYAN)
                ),
                name="por defecto",
                visible=vis,
            )
        )

    def ticks(vals) -> dict:
        vals = list(vals)
        step = max(1, int(np.ceil(len(vals) / 7)))
        return dict(
            tickvals=[float(v) for v in vals[::step]], ticktext=[_fmt_val(v) for v in vals[::step]]
        )

    scene = _scene(
        pname(names[1]),
        pname(names[0]),
        zlab,
        eye=(1.35, -1.4, 0.8),
        aspect=dict(x=1.0, y=1.25, z=0.75),
        x=ticks(xa),
        y=ticks(ya),
    )
    fig.update_layout(
        **_base_layout(
            scene=scene,
            margin=dict(l=0, r=0, t=10, b=0 if len(slices) == 1 else 70),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(5,6,15,0.6)", font=dict(size=11)),
        )
    )
    if len(slices) > 1:
        st = []
        for si in range(len(slices)):
            vis = [False] * (len(slices) * per)
            for j in range(per):
                vis[si * per + j] = True
            st.append(
                dict(
                    method="restyle", label=_fmt_val(sw.axes[names[2]][si]), args=[{"visible": vis}]
                )
            )
        fig.update_layout(sliders=[_slider(st, d0, pname(names[2]), pad=5)])
    return fig


def fig_pbo(ov: dict):
    """Histograma de los logits λ de CSCV: a la izquierda de 0 = el elegido falla fuera."""
    import plotly.graph_objects as go

    lg = ov.get("pbo_logits")
    if lg is None or not len(lg):
        return None
    lg = np.asarray(lg)
    lg = lg[np.isfinite(lg)]
    pbo = ov["pbo"]["pbo"]
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=lg[lg <= 0],
            marker_color=MAGENTA,
            opacity=0.85,
            name="falla fuera (λ ≤ 0)",
            xbins=dict(size=0.25),
        )
    )
    fig.add_trace(
        go.Histogram(
            x=lg[lg > 0],
            marker_color=CYAN,
            opacity=0.85,
            name="aguanta fuera (λ > 0)",
            xbins=dict(size=0.25),
        )
    )
    fig.add_vline(x=0, line=dict(color=GOLD, dash="dash", width=2))
    fig.update_layout(
        **_base_layout(
            barmode="overlay",
            xaxis=_axis("λ = logit del puesto fuera de muestra del 'mejor' dentro"),
            yaxis=_axis("nº de combinaciones"),
            title=dict(
                text=f"PBO = {pbo:.0%} de {ov['pbo']['n_combos']:,} particiones".replace(",", "."),
                font=dict(size=15, color=GOLD),
                x=0.02,
            ),
            legend=dict(orientation="h", x=0, y=-0.25),
            margin=dict(l=60, r=20, t=50, b=110),
        )
    )
    return fig


def fig_sweep_png(sw, metric: str, rob: dict, title: str):
    """Figura combinada (mapa arriba, superficie abajo) para el PNG de preview, en vertical."""
    from plotly.subplots import make_subplots

    names = list(sw.axes)
    heat = fig_heatmap(sw, metric, rob, big=True)
    if len(names) == 1:
        heat.update_layout(width=1080, height=900, title=dict(text=title, font=dict(size=24)))
        return heat
    surf = fig_surface(sw, metric, rob)
    d0 = _default_slice(sw, rob)
    fig = make_subplots(
        rows=2,
        cols=1,
        specs=[[{"type": "xy"}], [{"type": "scene"}]],
        row_heights=[0.5, 0.5],
        vertical_spacing=0.085,
    )
    per = 4
    hm = heat.data[d0]
    hm.visible = True
    hm.colorbar.update(
        len=0.4, y=0.78, thickness=18, tickfont=dict(size=16), title=dict(font=dict(size=17))
    )
    fig.add_trace(hm, row=1, col=1)
    for t in heat.data[-3:]:
        fig.add_trace(t, row=1, col=1)
    for j in range(per):
        t = surf.data[d0 * per + j]
        t.visible = True
        t.showlegend = False
        fig.add_trace(t, row=2, col=1)
    anns = []
    for a in heat.layout.annotations:
        a = a.to_plotly_json()
        a.update(xref="x", yref="y")
        anns.append(a)
    sub = f"{pname(names[2])} = {_fmt_val(sw.axes[names[2]][d0])} · " if len(names) == 3 else ""
    score_col = CYAN if rob["score"] >= 70 else GOLD if rob["score"] >= 40 else MAGENTA
    head = (
        f"<b>{title}</b><br><span style='font-size:19px;color:{MUTED}'>{sub}"
        f"{METRICS[metric][0]} · {sw.n_configs} configuraciones · "
        f"{PERIOD_ES.get(sw.period, sw.period)}</span><br>"
        f"<span style='font-size:23px;color:{score_col}'><b>Robustez {rob['score']:.0f}/100</b>"
        f" · {rob['verdict']}</span>"
    )
    anns.append(
        dict(
            text=head,
            x=0.0,
            y=1.0,
            yshift=36,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            align="left",
            font=dict(size=26, color="#fff"),
        )
    )
    anns.append(
        dict(
            text="<b>Superficie 3D</b>: lo que asoma por encima del plano cian es «casi tan "
            "bueno como el mejor».<br>Meseta ancha = robusto; aguja aislada = sobreajuste.",
            x=0.0,
            y=0.462,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            align="left",
            font=dict(size=17, color=FG),
        )
    )
    scene = surf.layout.scene.to_plotly_json()
    scene["domain"] = fig.layout.scene.domain.to_plotly_json()
    for ax in ("xaxis", "yaxis", "zaxis"):
        scene[ax]["title"]["font"]["size"] = 21
        scene[ax]["tickfont"]["size"] = 16
    fig.update_layout(
        **_base_layout(
            width=1080,
            height=1760,
            margin=dict(l=110, r=30, t=190, b=20),
            annotations=anns,
            shapes=[sh.to_plotly_json() for sh in heat.layout.shapes],
            xaxis=_cat_axis(
                pname(names[1]), sw.axes[names[1]], tickfont=dict(size=16, color="#c4ccf0")
            ),
            yaxis=_cat_axis(
                pname(names[0]), sw.axes[names[0]], tickfont=dict(size=16, color="#c4ccf0")
            ),
            legend=dict(orientation="h", x=0, y=0.495, font=dict(size=16), bgcolor="rgba(0,0,0,0)"),
            scene=scene,
        )
    )
    fig.update_xaxes(title_font_size=19)
    fig.update_yaxes(title_font_size=19)
    return fig


# ====================================================================== benchmark al azar


def _downsample(series_index_len: int, k: int = 500) -> np.ndarray:
    from tlab.backtest.montecarlo import _downsample_idx

    return _downsample_idx(series_index_len, k)


def money_ticks(lo: float, hi: float) -> tuple[list[float], list[str]]:
    """Marcas legibles en $ para un eje logarítmico (10k, 15k, 20k, 30k, 50k…)."""
    vals = [m * 10**e for e in range(2, 9) for m in (1, 1.5, 2, 3, 5, 7)]
    vals = [v for v in vals if lo * 0.97 <= v <= hi * 1.03]
    if len(vals) > 9:
        vals = [v for v in vals if str(v / 10 ** int(np.log10(v)))[0] in "125"]

    def fmt(x):
        return f"{x / 1e6:g}M $" if x >= 1e6 else f"{x / 1e3:g}k $" if x >= 1e3 else f"{x:.0f} $"

    return vals, [fmt(v) for v in vals]


def fig_random_hist(rr, metric: str):
    import plotly.graph_objects as go

    x = rr.table[metric].dropna().to_numpy(float)
    real = rr.real.get(metric, np.nan)
    if not len(x) or not np.isfinite(real):
        return None
    pct = METRICS[metric][1] == "pct"
    mult = 100.0 if pct else 1.0
    lab = METRICS[metric][0] + (" (%)" if pct else "")
    above = x >= real
    fig = go.Figure()
    rng = np.ptp(np.r_[x, real]) or 1.0
    size = rng / 45
    fig.add_trace(
        go.Histogram(
            x=x[~above] * mult,
            xbins=dict(size=size * mult),
            marker_color=VIOLET,
            opacity=0.85,
            name="azar por debajo del real",
        )
    )
    fig.add_trace(
        go.Histogram(
            x=x[above] * mult,
            xbins=dict(size=size * mult),
            marker_color=MAGENTA,
            opacity=0.9,
            name="azar ≥ real",
        )
    )
    for q, dash in ((5, "dot"), (50, "dash"), (95, "dot")):
        fig.add_vline(
            x=float(np.percentile(x, q)) * mult, line=dict(color=MUTED, dash=dash, width=1)
        )
    fig.add_vline(x=real * mult, line=dict(color=GOLD, width=4))
    p, pr = rr.p_value(metric), rr.percentile(metric)
    lo_x, hi_x = float(min(x.min(), real)), float(max(x.max(), real))
    right = (real - lo_x) / ((hi_x - lo_x) or 1.0) > 0.5
    fig.add_annotation(
        x=real * mult,
        y=1.0,
        yref="paper",
        text=f"<b>real {fmt_metric(metric, real)}</b><br>percentil {pr:.0%} · p = {p:.3f}",
        showarrow=False,
        yanchor="bottom",
        xanchor="right" if right else "left",
        align="right" if right else "left",
        font=dict(color=GOLD, size=13),
        bgcolor="rgba(5,6,15,0.75)",
    )
    fig.update_layout(
        **_base_layout(
            barmode="overlay",
            xaxis=_axis(lab),
            yaxis=_axis("nº de monos"),
            legend=dict(orientation="h", x=0, y=-0.22),
            margin=dict(l=60, r=20, t=60, b=100),
        )
    )
    return fig


def fig_random_violin(rr):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    from tlab.backtest.random_benchmark import COMPARE

    ms = [
        m
        for m in COMPARE
        if m in rr.table and rr.table[m].notna().any() and np.isfinite(rr.real.get(m, np.nan))
    ]
    fig = make_subplots(
        rows=1, cols=len(ms), subplot_titles=[METRICS[m][0] for m in ms], horizontal_spacing=0.06
    )
    for i, m in enumerate(ms, start=1):
        pct = METRICS[m][1] == "pct"
        mult = 100.0 if pct else 1.0
        x = rr.table[m].dropna().to_numpy(float) * mult
        fig.add_trace(
            go.Violin(
                y=x,
                line_color=CYAN,
                fillcolor="rgba(164,107,255,0.35)",
                box_visible=True,
                meanline_visible=True,
                points=False,
                name="azar",
                showlegend=i == 1,
                spanmode="hard",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=["azar"],
                y=[rr.real[m] * mult],
                mode="markers",
                marker=dict(
                    symbol="diamond", size=16, color=GOLD, line=dict(width=2, color="#fff")
                ),
                name="estrategia real",
                showlegend=i == 1,
                hovertemplate=(
                    f"real: {fmt_metric(m, rr.real[m])}<br>p = {rr.p_value(m):.3f}<extra></extra>"
                ),
            ),
            row=1,
            col=i,
        )
        fig.update_yaxes(
            gridcolor=GRID,
            zerolinecolor=GRID,
            tickfont=dict(size=11, color="#9aa6dc"),
            ticksuffix="%" if pct else "",
            row=1,
            col=i,
        )
        fig.update_xaxes(showticklabels=False, row=1, col=i)
    for a in fig.layout.annotations:
        a.font = dict(size=12, color=FG)
    fig.update_layout(
        **_base_layout(
            legend=dict(orientation="h", x=0, y=-0.08), margin=dict(l=40, r=10, t=40, b=60)
        )
    )
    return fig


def fig_random_paths(rr, *, big: bool = False):
    """Espaguetis: curvas de los monos (color por resultado final) contra la real (dorada)."""
    import plotly.graph_objects as go

    P = rr.paths
    if P.empty:
        return None
    real = rr.real_equity.reindex(P.index).ffill()
    idx = _downsample(len(P.index), 500)
    x = P.index[idx]
    final = P.iloc[-1].to_numpy(float)
    ranks = np.argsort(np.argsort(final)) / max(len(final) - 1, 1)
    fig = go.Figure()
    allp = P.to_numpy(float)
    lo, hi = np.nanpercentile(allp, 5, axis=1)[idx], np.nanpercentile(allp, 95, axis=1)[idx]
    med = np.nanmedian(allp, axis=1)[idx]
    fig.add_trace(
        go.Scatter(
            x=list(x) + list(x[::-1]),
            y=list(hi) + list(lo[::-1]),
            fill="toself",
            fillcolor="rgba(0,229,255,0.07)",
            line=dict(width=0),
            hoverinfo="skip",
            name="azar p5–p95",
        )
    )
    bins = np.linspace(0, 1, 11)
    from plotly.colors import sample_colorscale

    for b in range(10):
        sel = np.nonzero((ranks >= bins[b]) & ((ranks < bins[b + 1]) | (b == 9)))[0]
        if not len(sel):
            continue
        col = sample_colorscale(NEON_OUTCOME, [(bins[b] + bins[b + 1]) / 2])[0]
        xs, ys = [], []
        for j in sel:
            xs += list(x) + [None]
            ys += list(allp[idx, j]) + [None]
        fig.add_trace(
            go.Scattergl(
                x=xs,
                y=ys,
                mode="lines",
                line=dict(color=col, width=1),
                opacity=0.33,
                hoverinfo="skip",
                showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=med,
            mode="lines",
            line=dict(color="#d7defa", dash="dot", width=1.5),
            name="mediana del azar",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=real.to_numpy(float)[idx],
            mode="lines",
            line=dict(color="rgba(255,209,102,0.35)", width=10 if big else 8),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=real.to_numpy(float)[idx],
            mode="lines",
            line=dict(color=GOLD, width=3.5 if big else 2.8),
            name="estrategia real",
        )
    )
    tv, tt = money_ticks(float(np.nanmin(lo)), float(np.nanmax(np.r_[hi, real.max(), allp.max()])))
    fig.update_layout(
        **_base_layout(
            xaxis=_axis(""),
            yaxis=_axis("Equity (escala log)", type="log", tickvals=tv, ticktext=tt),
            legend=dict(orientation="h", x=0, y=1.08, bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=70, r=15, t=50, b=40),
        )
    )
    return fig


def fig_random_png(rr, metric: str, title: str):
    """PNG vertical: histograma de la métrica arriba, espaguetis abajo."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    h = fig_random_hist(rr, metric)
    s = fig_random_paths(rr, big=True)
    fig = make_subplots(rows=2, cols=1, row_heights=[0.42, 0.58], vertical_spacing=0.1)
    for t in h.data:
        fig.add_trace(t, row=1, col=1)
    for t in s.data:
        if isinstance(t, go.Scattergl):
            t = go.Scatter(t.to_plotly_json())
        fig.add_trace(t, row=2, col=1)
    real = rr.real[metric]
    p, pr = rr.p_value(metric), rr.percentile(metric)
    from tlab.backtest.random_benchmark import p_verdict

    pct = METRICS[metric][1] == "pct"
    mult = 100.0 if pct else 1.0
    x = rr.table[metric].dropna().to_numpy(float)
    shapes = [
        dict(
            type="line",
            xref="x",
            yref="y domain",
            x0=real * mult,
            x1=real * mult,
            y0=0,
            y1=1,
            line=dict(color=GOLD, width=5),
        )
    ]
    for q, dash in ((5, "dot"), (50, "dash"), (95, "dot")):
        v = float(np.percentile(x, q)) * mult
        shapes.append(
            dict(
                type="line",
                xref="x",
                yref="y domain",
                x0=v,
                x1=v,
                y0=0,
                y1=1,
                line=dict(color=MUTED, width=1.5, dash=dash),
            )
        )
    ver = p_verdict(p)
    col = CYAN if p < 0.05 else GOLD if p < 0.10 else MAGENTA
    nm = f"{rr.n:,}".replace(",", ".")
    anns = [
        dict(
            text=f"<b>{title}</b><br><span style='font-size:20px;color:{MUTED}'>{nm} monos al azar "
            f"(semilla {rr.seed}) · mismas reglas y costes · "
            f"{PERIOD_ES.get(rr.period, rr.period)}</span>",
            x=0,
            y=1.205,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            align="left",
            yanchor="top",
            font=dict(size=28, color="#fff"),
        ),
        dict(
            text=f"<b>{ver}</b><br><span style='font-size:21px'>{METRICS[metric][0]} real "
            f"{fmt_metric(metric, real)} · mejor que el {pr:.0%} de los monos · p = {p:.3f}</span>",
            x=0,
            y=1.115,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            align="left",
            yanchor="top",
            font=dict(size=27, color=col),
        ),
        dict(
            text=f"<b>{METRICS[metric][0]}</b> de cada mono · línea dorada = estrategia real",
            x=0,
            y=1.012,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(size=18, color=FG),
        ),
        dict(
            text="<b>Curvas de equity</b>: monos (rojo = peor, verde = mejor) vs real (dorada)",
            x=0,
            y=0.53,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(size=18, color=FG),
        ),
    ]
    fig.update_layout(
        **_base_layout(
            width=1080,
            height=1720,
            barmode="overlay",
            shapes=shapes,
            annotations=anns,
            margin=dict(l=120, r=30, t=300, b=70),
            font=dict(family=FONT, color=FG, size=18),
            legend=dict(
                orientation="h",
                x=0,
                y=-0.045,
                yanchor="top",
                font=dict(size=18),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
    )
    lab = METRICS[metric][0] + (" (%)" if pct else "")
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(size=18, color="#c4ccf0"))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(size=18, color="#c4ccf0"))
    fig.update_xaxes(title=dict(text=lab, font=dict(size=20)), row=1, col=1)
    fig.update_yaxes(title=dict(text="nº de monos", font=dict(size=20)), row=1, col=1)
    yax = s.layout.yaxis
    fig.update_yaxes(
        type="log",
        tickvals=yax.tickvals,
        ticktext=yax.ticktext,
        title=dict(text="Equity (escala log)", font=dict(size=20)),
        row=2,
        col=1,
    )
    return fig


# ====================================================================== HTML con pestañas

_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#05060f;--fg:#d7defa;--mut:#8f9bd0;--acc:#00e5ff;--gold:#ffd166;--line:#1c2346}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--fg);
font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;overflow-x:hidden}
body{background:radial-gradient(1200px 600px at 70% -10%,#1a1150 0%,transparent 60%),
radial-gradient(900px 500px at -10% 110%,#03303a 0%,transparent 60%),var(--bg)}
header{padding:14px 14px 6px}
h1{margin:0;font-size:clamp(17px,4.6vw,26px);letter-spacing:.3px;
background:linear-gradient(90deg,#00e5ff,#a46bff,#ff3d9a);-webkit-background-clip:text;
background-clip:text;color:transparent;text-shadow:0 0 22px rgba(0,229,255,.25)}
.sub{color:var(--mut);font-size:12px;margin-top:3px}
.verdict{margin-top:8px;font-size:15px;font-weight:600}
.verdict.good{color:#00ff8c;text-shadow:0 0 10px rgba(0,255,140,.4)}
.verdict.mid{color:var(--gold);text-shadow:0 0 10px rgba(255,209,102,.4)}
.verdict.bad{color:#ff5277;text-shadow:0 0 10px rgba(255,23,68,.45)}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:5px;
margin-top:10px}
.st{background:rgba(20,26,60,.55);border:1px solid var(--line);border-radius:10px;
padding:7px 9px;box-shadow:0 0 14px rgba(0,229,255,.05) inset}
.st b{display:block;font-size:14px;color:#fff}.st span{font-size:10px;color:var(--mut)}
.st.warn b{color:#ff5277;text-shadow:0 0 10px rgba(255,23,68,.5)}
.st.gold b{color:var(--gold);text-shadow:0 0 10px rgba(255,209,102,.4)}
.st.good b{color:#00ff8c;text-shadow:0 0 10px rgba(0,255,140,.4)}
nav,.mets{display:flex;gap:6px;padding:8px 14px;overflow-x:auto;scrollbar-width:none}
nav::-webkit-scrollbar,.mets::-webkit-scrollbar{display:none}
nav{position:sticky;top:0;z-index:5;background:rgba(5,6,15,.85);backdrop-filter:blur(8px)}
nav button{flex:1 0 auto;background:#0d1230;color:var(--fg);border:1px solid var(--line);
border-radius:999px;padding:8px 12px;font-size:13px;cursor:pointer;white-space:nowrap}
nav button.on{border-color:var(--acc);color:#fff;box-shadow:0 0 12px rgba(0,229,255,.45),
0 0 2px var(--acc) inset}
.mets{padding-top:0}
.mets button{background:#0d1230;color:var(--fg);border:1px solid var(--line);border-radius:8px;
padding:6px 10px;font-size:12px;white-space:nowrap;cursor:pointer}
.mets button.on{border-color:var(--gold);color:var(--gold)}
.how{padding:2px 14px 6px;font-size:12.5px;color:var(--mut);line-height:1.35;min-height:34px}
.how b{color:var(--fg)}
.plot{width:100%;height:calc(100svh - 190px);min-height:420px}
.ctl{display:flex;gap:8px;padding:0 14px 6px}
.ctl button{background:#0d1230;color:var(--fg);border:1px solid var(--line);border-radius:8px;
padding:6px 10px;font-size:12px}.ctl button.on{border-color:var(--gold);color:var(--gold)}
.warns{padding:4px 14px 6px;font-size:12.5px;line-height:1.4}
.warns li{margin:3px 0;color:#c4ccf0}.warns b{color:#fff}
details{margin:6px 14px;border:1px solid var(--line);border-radius:10px;padding:6px 10px;
background:rgba(13,18,48,.5)}summary{cursor:pointer;color:var(--gold);font-size:13px}
footer{padding:10px 14px 24px;font-size:11px;color:#5d6796}
@media(max-width:600px){.st{padding:5px 7px}.st b{font-size:13px}.sub{font-size:11px}}
</style></head><body>
<header><h1>__TITLE__</h1>
<div class="sub">__SUB__</div>
<div class="verdict __VCLASS__">__VERDICT__</div>
<div class="stats">__STATS__</div></header>
<nav>__TABS__</nav>
<div class="mets" id="mets">__METS__</div>
<div class="how" id="how"></div>
<div class="ctl" id="ctl" style="display:none"><button id="spin">🌀 Giro automático</button>
<button id="reset">🎯 Vista inicial</button></div>
<div id="plot" class="plot"></div>
<details open><summary>⚠️ Avisos (léelos antes de creerte nada)</summary>
<ul class="warns">__WARNS__</ul></details>
<footer>__FOOTER__</footer>
<script>__PLOTLYJS__</script>
<script>
const FIGS=__FIGS__;const HOW=__HOW__;const VIEWS=__VIEWS__;
const el=document.getElementById('plot');const cfg={responsive:true,displaylogo:false,
modeBarButtonsToRemove:['toImage','resetCameraLastSave3d','hoverClosest3d','lasso2d','select2d'],
scrollZoom:false};
let view=VIEWS[0].id,metric=__METRIC0__,spinT=null,ang=0;
function key(){const v=VIEWS.find(x=>x.id===view);return v.per_metric?view+'|'+metric:view;}
function show(){const v=VIEWS.find(x=>x.id===view);
document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.id===view));
document.querySelectorAll('#mets button').forEach(b=>{b.classList.toggle('on',b.dataset.m===metric);
b.style.display=(v.per_metric&&FIGS[view+'|'+b.dataset.m])?'':'none';});
document.getElementById('mets').style.display=v.per_metric?'':'none';
document.getElementById('how').innerHTML=HOW[view]||'';
document.getElementById('ctl').style.display=v.is3d?'':'none';
if(spinT){clearInterval(spinT);spinT=null;document.getElementById('spin').classList.remove('on');}
const fj=FIGS[key()];if(!fj){Plotly.purge(el);
el.innerHTML='<p style="padding:14px">Sin datos.</p>';return;}
el.innerHTML='';const f=JSON.parse(JSON.stringify(fj));
if(innerWidth<700){cfg.displayModeBar=false;if(f.layout.legend){f.layout.legend.font={size:10};}}
Plotly.react(el,f.data,f.layout,cfg);
if(v.is3d){const e=f.layout.scene.camera.eye;ang=Math.atan2(e.y,e.x);}}
function spin(){if(spinT){clearInterval(spinT);spinT=null;
document.getElementById('spin').classList.remove('on');return;}
document.getElementById('spin').classList.add('on');spinT=setInterval(()=>{
const e=el._fullLayout.scene.camera.eye;const r=Math.hypot(e.x,e.y);ang+=0.012;
Plotly.relayout(el,{'scene.camera.eye':{x:r*Math.cos(ang),y:r*Math.sin(ang),z:e.z}});},40);}
document.getElementById('spin').onclick=spin;
document.getElementById('reset').onclick=show;
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{view=b.dataset.id;show();});
document.querySelectorAll('#mets button').forEach(b=>b.onclick=()=>{metric=b.dataset.m;show();});
show();
</script></body></html>
"""


def write_tabbed_html(
    path,
    *,
    title: str,
    sub: str,
    verdict: str,
    vclass: str,
    stats: list[tuple[str, str, str]],
    views: list[dict],
    figs: dict,
    metrics: list[str],
    metric0: str,
    warns: list[str],
    footer: str,
) -> Path:
    """HTML autocontenido (plotly.js incrustado, sin red) con pestañas y selector de métrica.

    ``views``: [{"id", "label", "how", "per_metric", "is3d"}]; ``figs``: {"id|métrica" o "id": fig}.
    """
    import re

    import plotly.offline as off

    figs_json = (
        "{" + ",".join(f'"{k}":{f.to_json()}' for k, f in figs.items() if f is not None) + "}"
    )
    st = "".join(f'<div class="st {c}"><b>{v}</b><span>{lab}</span></div>' for lab, v, c in stats)
    tabs = "".join(f'<button data-id="{v["id"]}">{v["label"]}</button>' for v in views)
    mets = "".join(f'<button data-m="{m}">{METRICS[m][0]}</button>' for m in metrics)
    how = {v["id"]: f"<b>Cómo leerlo:</b> {v['how']}" for v in views}
    vjson = [
        {"id": v["id"], "per_metric": bool(v.get("per_metric")), "is3d": bool(v.get("is3d"))}
        for v in views
    ]

    def md(s: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

    html = (
        _HTML.replace("__PLOTLYJS__", off.get_plotlyjs())
        .replace("__FIGS__", figs_json)
        .replace("__HOW__", json.dumps(how, ensure_ascii=False))
        .replace("__VIEWS__", json.dumps(vjson))
        .replace("__METRIC0__", json.dumps(metric0))
        .replace("__STATS__", st)
        .replace("__TABS__", tabs)
        .replace("__METS__", mets)
        .replace("__WARNS__", "".join(f"<li>{md(w)}</li>" for w in warns))
        .replace("__VERDICT__", verdict)
        .replace("__VCLASS__", vclass)
        .replace("__FOOTER__", footer)
        .replace("__SUB__", sub)
        .replace("__TITLE__", title)
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def now_label() -> str:
    from tlab.report import MADRID

    return pd.Timestamp.now(tz=MADRID).strftime("%Y-%m-%d %H:%M")
