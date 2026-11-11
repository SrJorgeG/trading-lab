"""Vistas 3D del Monte Carlo (spaghetti, montaña de densidad, nube de resultados).

La lógica de preparación de datos está separada de los gráficos para poder
testearla sin plotly. Todo se pinta con plotly y se guarda en un único HTML
autocontenido (plotly.js incrustado) pensado para verse bien en el móvil.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tlab.backtest.montecarlo import MCConfig, MCResult, _downsample_idx

# Paleta neón: rojo (peor) → naranja → amarillo → cian → verde (mejor).
NEON_OUTCOME = [
    [0.00, "#ff1744"],
    [0.20, "#ff5e00"],
    [0.40, "#ffd400"],
    [0.65, "#00e5ff"],
    [1.00, "#00ff8c"],
]
# Montaña de densidad: negro → violeta → magenta → naranja → amarillo.
NEON_DENSITY = [
    [0.00, "#05060f"],
    [0.08, "#1a0b3d"],
    [0.25, "#4b0c8a"],
    [0.45, "#b0179e"],
    [0.65, "#ff3d6e"],
    [0.85, "#ff9f1c"],
    [1.00, "#fff36b"],
]
GOLD = "#ffd166"
BG = "#05060f"
GRID = "#1c2346"
FG = "#d7defa"


# ---------------------------------------------------------------- preparación


def time_axis(result: MCResult) -> tuple[np.ndarray, str]:
    """Eje X numérico: años decimales si hay fechas, si no nº de paso."""
    idx = result.index
    if isinstance(idx, pd.DatetimeIndex) and result.method == "block":
        years = idx.year + (idx.dayofyear - 1) / 365.25
        return np.asarray(years, dtype=float), "Año"
    return np.arange(len(idx), dtype=float), "Operación nº"


def select_paths(final: np.ndarray, k: int, seed: int = 42) -> np.ndarray:
    """Elige ``k`` simulaciones estratificadas por equity final, ordenadas de peor a mejor.

    Siempre incluye la peor y la mejor, y reparte el resto por cuantiles para
    que el abanico represente toda la distribución (no solo el centro).
    """
    final = np.asarray(final, dtype=float)
    n = len(final)
    if k >= n:
        return np.argsort(final, kind="stable")
    order = np.argsort(final, kind="stable")
    rng = np.random.default_rng(seed)
    edges = np.linspace(0, n, k + 1)
    picks = []
    for i in range(k):
        lo, hi = int(edges[i]), max(int(edges[i + 1]), int(edges[i]) + 1)
        picks.append(order[rng.integers(lo, hi)])
    picks[0], picks[-1] = order[0], order[-1]
    picks = np.array(picks)
    return picks[np.argsort(final[picks], kind="stable")]


def outcome_percentile(final: np.ndarray) -> np.ndarray:
    """Percentil (0–1) del equity final de cada simulación respecto a todas."""
    final = np.asarray(final, dtype=float)
    ranks = np.argsort(np.argsort(final, kind="stable"), kind="stable")
    return ranks / max(len(final) - 1, 1)


def density_grid(
    paths: np.ndarray,
    n_levels: int = 90,
    *,
    log: bool = True,
    clip: tuple[float, float] = (0.5, 99.5),
    smooth: float = 1.2,
) -> tuple[np.ndarray, np.ndarray]:
    """Histograma por instante: devuelve ``(niveles, densidad)``.

    ``densidad`` tiene forma ``(n_levels, T)``; cada columna suma 1 (probabilidad
    de que un camino esté en ese tramo de equity en ese instante). Con ``log``
    los niveles están en log10($). ``smooth`` es el sigma (en celdas) de un
    suavizado gaussiano vertical, solo estético.
    """
    p = np.asarray(paths, dtype=float)
    if p.ndim != 2 or p.size == 0:
        raise ValueError("paths tiene que ser una matriz N×T no vacía")
    v = np.log10(np.clip(p, 1e-9, None)) if log else p
    lo, hi = np.nanpercentile(v, clip[0]), np.nanpercentile(v, clip[1])
    if hi <= lo:
        hi = lo + 1e-6
    edges = np.linspace(lo, hi, n_levels + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    bins = np.clip(np.searchsorted(edges, v, side="right") - 1, 0, n_levels - 1)
    t = v.shape[1]
    dens = np.zeros((n_levels, t))
    cols = np.broadcast_to(np.arange(t), bins.shape)
    np.add.at(dens, (bins.ravel(), cols.ravel()), 1.0)
    if smooth and smooth > 0:
        r = int(np.ceil(3 * smooth))
        ker = np.exp(-0.5 * (np.arange(-r, r + 1) / smooth) ** 2)
        ker /= ker.sum()
        pad = np.pad(dens, ((r, r), (0, 0)), mode="constant")
        dens = np.stack([np.convolve(pad[:, j], ker, mode="valid") for j in range(t)], axis=1)
    tot = dens.sum(axis=0, keepdims=True)
    tot[tot == 0] = 1.0
    return centers, dens / tot


def first_hit_index(paths: np.ndarray, frac: float) -> np.ndarray:
    """Índice del primer paso con caída > ``frac`` desde el máximo (-1 si nunca)."""
    p = np.asarray(paths, dtype=float)
    peak = np.maximum.accumulate(p, axis=1)
    hit = (1.0 - p / peak) > frac
    first = hit.argmax(axis=1)
    first[~hit.any(axis=1)] = -1
    return first


def money_ticks(lo: float, hi: float, *, log: bool) -> tuple[list[float], list[str]]:
    """Marcas legibles en $ (5k, 10k, 20k, 50k…) entre lo y hi (en $)."""
    cands = []
    for e in range(2, 9):
        for m in (1, 2, 5):
            cands.append(m * 10**e)
    vals = [c for c in cands if lo * 0.95 <= c <= hi * 1.05]
    if len(vals) < 3:
        vals = list(np.linspace(lo, hi, 5))

    def fmt(x):
        if x >= 1e6:
            return f"{x / 1e6:g}M $"
        if x >= 1e3:
            return f"{x / 1e3:g}k $"
        return f"{x:.0f} $"

    pos = [float(np.log10(x)) if log else float(x) for x in vals]
    return pos, [fmt(x) for x in vals]


# ---------------------------------------------------------------- figuras


def _scene(xlab: str, ylab: str, zlab: str, eye=(1.7, -1.5, 0.75), **axes) -> dict:
    def ax(title, extra):
        d = dict(
            title=dict(text=title, font=dict(size=15, color=FG)),
            backgroundcolor=BG,
            gridcolor=GRID,
            zerolinecolor=GRID,
            showbackground=True,
            color=FG,
            tickfont=dict(size=12, color="#9aa6dc"),
            showspikes=False,
        )
        d.update(extra or {})
        return d

    return dict(
        xaxis=ax(xlab, axes.get("x")),
        yaxis=ax(ylab, axes.get("y")),
        zaxis=ax(zlab, axes.get("z")),
        bgcolor=BG,
        camera=dict(eye=dict(x=eye[0], y=eye[1], z=eye[2]), center=dict(x=0, y=0, z=-0.08)),
        aspectmode="manual",
        aspectratio=axes.get("aspect", dict(x=1.6, y=1.0, z=0.8)),
        dragmode="turntable",
    )


def _layout(scene: dict, *, colorbar_title: str | None = None) -> dict:
    return dict(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="Inter, system-ui, sans-serif", color=FG),
        margin=dict(l=0, r=0, t=0, b=0),
        scene=scene,
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor="rgba(5,6,15,0.6)",
            bordercolor=GRID,
            borderwidth=1,
            font=dict(size=11),
        ),
        uirevision="keep",
    )


def _lines_xyz(x: np.ndarray, ys: np.ndarray, zs: np.ndarray, cs: np.ndarray):
    """Une varias polilíneas en una sola traza separada por None (mucho más ligera)."""
    k, t = zs.shape
    X = np.concatenate([np.tile(x, (k, 1)), np.full((k, 1), np.nan)], axis=1).ravel()
    Y = np.concatenate([np.repeat(ys[:, None], t, axis=1), np.full((k, 1), np.nan)], 1).ravel()
    Z = np.concatenate([zs, np.full((k, 1), np.nan)], axis=1).ravel()
    C = np.concatenate([np.repeat(cs[:, None], t + 1, axis=1)], axis=1).ravel()
    r = lambda a: [None if not np.isfinite(v) else round(float(v), 4) for v in a]  # noqa: E731
    return r(X), r(Y), r(Z), [round(float(v), 3) for v in C]


def spaghetti_data(result: MCResult, k: int = 300, max_t: int = 260) -> dict:
    """Datos de la vista spaghetti: caminos elegidos, ordenados y submuestreados."""
    if result.paths is None:
        raise ValueError("Hace falta MCConfig(keep_paths=True)")
    x_full, xlab = time_axis(result)
    ti = _downsample_idx(len(x_full), max_t)
    sel = select_paths(result.final_equity, k, seed=result.seed)
    pct = outcome_percentile(result.final_equity)[sel]
    z = np.log10(result.paths[sel][:, ti])
    y = np.arange(len(sel), dtype=float)
    real = result.real_path.to_numpy(dtype=float)
    real_rank = float(np.searchsorted(np.sort(result.final_equity[sel]), real[-1]))
    return dict(
        x=x_full[ti],
        xlab=xlab,
        sel=sel,
        y=y,
        z=z,
        pct=pct,
        ruin=result.hit_ruin[sel],
        real_z=np.log10(real[ti]),
        real_y=min(real_rank, len(sel) - 1),
        ti=ti,
    )


def fig_spaghetti(result: MCResult, k: int = 300):
    import plotly.graph_objects as go

    d = spaghetti_data(result, k)
    X, Y, Z, C = _lines_xyz(d["x"], d["y"], d["z"], d["pct"])
    traces = [
        # «Glow»: misma geometría, gruesa y casi transparente.
        go.Scatter3d(
            x=X,
            y=Y,
            z=Z,
            mode="lines",
            hoverinfo="skip",
            showlegend=False,
            opacity=0.10,
            line=dict(color=C, colorscale=NEON_OUTCOME, cmin=0, cmax=1, width=7),
        ),
        go.Scatter3d(
            x=X,
            y=Y,
            z=Z,
            mode="lines",
            name="Simulaciones (color = resultado final)",
            hoverinfo="skip",
            opacity=0.85,
            line=dict(
                color=C,
                colorscale=NEON_OUTCOME,
                cmin=0,
                cmax=1,
                width=1.6,
                colorbar=dict(
                    title=dict(text="Percentil<br>final", font=dict(size=11)),
                    tickvals=[0, 0.5, 1],
                    ticktext=["peor", "mediana", "mejor"],
                    len=0.45,
                    thickness=10,
                    x=0.98,
                    y=0.5,
                    outlinewidth=0,
                    tickfont=dict(size=10),
                ),
            ),
        ),
    ]
    ry = np.full(len(d["x"]), d["real_y"])
    for w, op in ((22, 0.10), (12, 0.30)):
        traces.append(
            go.Scatter3d(
                x=d["x"],
                y=ry,
                z=d["real_z"],
                mode="lines",
                hoverinfo="skip",
                showlegend=False,
                opacity=op,
                line=dict(color=GOLD, width=w),
            )
        )
    traces.append(
        go.Scatter3d(
            x=d["x"],
            y=ry,
            z=d["real_z"],
            mode="lines",
            name="Backtest real",
            line=dict(color="#ffffff", width=6),
            text=[f"{10**v:,.0f} $" for v in d["real_z"]],
            hovertemplate="%{x:.1f} · %{text}<extra>Backtest</extra>",
        )
    )
    # Sombra del backtest en el «suelo» para dar profundidad.
    zmin = float(np.nanmin(d["z"]))
    traces.append(
        go.Scatter3d(
            x=d["x"],
            y=np.full(len(d["x"]), len(d["y"]) - 1.0),
            z=d["real_z"],
            mode="lines",
            hoverinfo="skip",
            showlegend=False,
            opacity=0.35,
            line=dict(color=GOLD, width=2, dash="dot"),
        )
    )
    zmax = float(np.nanmax(d["z"]))
    tv, tt = money_ticks(10**zmin, 10**zmax, log=True)
    scene = _scene(
        d["xlab"],
        "Simulación (ordenadas de peor a mejor)",
        "Equity",
        eye=(-1.35, -1.55, 0.5),
        y=dict(showticklabels=False),
        z=dict(tickvals=tv, ticktext=tt, range=[zmin - 0.02, zmax + 0.02]),
        aspect=dict(x=1.8, y=1.15, z=0.85),
    )
    fig = go.Figure(traces, layout=_layout(scene))
    return fig


def relative_density(dens: np.ndarray, time_smooth: int = 3) -> np.ndarray:
    """Cada columna dividida por su máximo (cresta = 1) y suavizada en el tiempo.

    Así se ve cómo se *ensancha* la distribución sin que la aguja inicial
    aplaste el resto. Forma igual a la de ``dens``.
    """
    d = np.asarray(dens, dtype=float)
    if time_smooth and time_smooth > 1 and d.shape[1] > time_smooth:
        ker = np.ones(time_smooth) / time_smooth
        pad = np.pad(
            d, ((0, 0), (time_smooth // 2, time_smooth - 1 - time_smooth // 2)), mode="edge"
        )
        d = np.stack([np.convolve(pad[i], ker, mode="valid") for i in range(d.shape[0])])
    mx = d.max(axis=0, keepdims=True)
    mx[mx == 0] = 1.0
    return d / mx


def fig_density(result: MCResult, n_levels: int = 110, max_t: int = 180):
    import plotly.graph_objects as go

    if result.paths is None:
        raise ValueError("Hace falta MCConfig(keep_paths=True)")
    x_full, xlab = time_axis(result)
    ti = _downsample_idx(len(x_full), max_t)
    ti = ti[ti >= 1]
    sub = result.paths[:, ti]
    levels, dens = density_grid(sub, n_levels, log=True, clip=(0.3, 99.7), smooth=1.5)
    z = relative_density(dens)
    x = x_full[ti]
    cols = np.arange(len(ti))
    real = np.log10(result.real_path.to_numpy(dtype=float)[ti])
    jj = np.clip(np.searchsorted(levels, real), 0, n_levels - 1)
    real_on = z[jj, cols] + 0.04
    med = np.log10(np.median(sub, axis=0))
    jm = np.clip(np.searchsorted(levels, med), 0, n_levels - 1)
    med_on = z[jm, cols] + 0.03
    p5 = np.log10(np.percentile(sub, 5, axis=0))
    p95 = np.log10(np.percentile(sub, 95, axis=0))
    tv, tt = money_ticks(10 ** levels[0], 10 ** levels[-1], log=True)
    r4 = lambda a: np.round(a, 4).tolist()  # noqa: E731
    traces = [
        go.Surface(
            x=r4(x),
            y=r4(levels),
            z=np.round(z, 3).tolist(),
            colorscale=NEON_DENSITY,
            cmin=0,
            cmax=1,
            showscale=False,
            opacity=0.98,
            lighting=dict(ambient=0.5, diffuse=0.75, specular=0.5, roughness=0.35, fresnel=0.6),
            lightposition=dict(x=-5e4, y=-5e4, z=1e5),
            contours=dict(
                z=dict(
                    show=True,
                    usecolormap=True,
                    project=dict(z=False),
                    width=1,
                    start=0.1,
                    end=0.9,
                    size=0.2,
                ),
            ),
            hovertemplate="%{x:.1f}<br>densidad relativa %{z:.2f}<extra></extra>",
            name="Densidad",
        ),
        go.Scatter3d(
            x=x,
            y=med,
            z=med_on,
            mode="lines",
            name="Mediana de las simulaciones",
            line=dict(color="#00e5ff", width=4),
            hoverinfo="skip",
        ),
    ]
    for band, nm in ((p5, "p5 (malo)"), (p95, "p95 (bueno)")):
        traces.append(
            go.Scatter3d(
                x=x,
                y=band,
                z=np.zeros(len(x)),
                mode="lines",
                name=f"Banda {nm}",
                line=dict(color="#7d8cff", width=3, dash="dot"),
                hoverinfo="skip",
                showlegend=nm.startswith("p5"),
            )
        )
    traces[-1].name = "Bandas p5 / p95 (suelo)"
    traces[-2].name = "Bandas p5 / p95 (suelo)"
    traces += [
        go.Scatter3d(
            x=x,
            y=real,
            z=real_on,
            mode="lines",
            hoverinfo="skip",
            showlegend=False,
            opacity=0.3,
            line=dict(color=GOLD, width=16),
        ),
        go.Scatter3d(
            x=x,
            y=real,
            z=real_on,
            mode="lines",
            name="Backtest real",
            line=dict(color="#ffffff", width=6),
            hoverinfo="skip",
        ),
    ]
    scene = _scene(
        xlab,
        "Equity",
        "Densidad (cresta = 1)",
        eye=(-1.35, -1.95, 1.35),
        y=dict(tickvals=tv, ticktext=tt),
        z=dict(range=[0, 1.15], showticklabels=False),
        aspect=dict(x=1.8, y=1.6, z=0.5),
    )
    return go.Figure(traces, layout=_layout(scene))


def outcomes_data(result: MCResult, max_points: int = 3000, seed: int = 7) -> dict:
    n = len(result.final_equity)
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(n, size=min(max_points, n), replace=False))
    pct = outcome_percentile(result.final_equity)
    return dict(
        cagr=result.cagr[idx] * 100,
        dd=result.max_dd[idx] * 100,
        days=result.max_dd_days[idx].astype(float),
        pct=pct[idx],
        idx=idx,
    )


def fig_outcomes(result: MCResult, cfg: MCConfig):
    import plotly.graph_objects as go

    d = outcomes_data(result)
    r = result.real
    traces = [
        go.Scatter3d(
            x=d["cagr"],
            y=d["dd"],
            z=d["days"],
            mode="markers",
            name="Simulaciones",
            marker=dict(
                size=2.6,
                color=d["pct"],
                colorscale=NEON_OUTCOME,
                cmin=0,
                cmax=1,
                opacity=0.85,
                line=dict(width=0),
                colorbar=dict(
                    title=dict(text="Percentil<br>final", font=dict(size=11)),
                    tickvals=[0, 0.5, 1],
                    ticktext=["peor", "mediana", "mejor"],
                    len=0.45,
                    thickness=10,
                    x=0.98,
                    outlinewidth=0,
                    tickfont=dict(size=10),
                ),
            ),
            hovertemplate="CAGR %{x:.1f} %<br>Máx. caída %{y:.1f} %<br>"
            "%{z:.0f} días bajo el agua<extra></extra>",
            projection=dict(z=dict(show=True, opacity=0.18, scale=0.6)),
        ),
    ]
    # Plano del kill switch (caída = -kill).
    xs = [float(np.min(d["cagr"])), float(np.max(d["cagr"]))]
    zs = [0.0, float(np.max(d["days"]))]
    ky = -cfg.kill_switch * 100
    traces.append(
        go.Surface(
            x=[xs, xs],
            y=[[ky, ky], [ky, ky]],
            z=[[zs[0], zs[0]], [zs[1], zs[1]]],
            showscale=False,
            opacity=0.10,
            colorscale=[[0, "#ff1744"], [1, "#ff1744"]],
            name=f"Kill switch −{cfg.kill_switch:.0%}",
            showlegend=True,
            hoverinfo="skip",
        )
    )
    for size, op in ((26, 0.25), (14, 1.0)):
        traces.append(
            go.Scatter3d(
                x=[r["cagr"] * 100],
                y=[r["max_dd"] * 100],
                z=[r["max_dd_days"]],
                mode="markers",
                showlegend=op == 1.0,
                name="Backtest real",
                opacity=op,
                marker=dict(
                    size=size, color=GOLD, symbol="diamond", line=dict(color="#fff6d5", width=2)
                ),
                hovertemplate="Backtest<br>CAGR %{x:.1f} %<br>Caída %{y:.1f} %<br>"
                "%{z:.0f} días<extra></extra>",
            )
        )
    scene = _scene(
        "CAGR (%)",
        "Máx. caída (%)",
        "Días bajo el agua",
        eye=(1.45, 1.4, 0.62),
        aspect=dict(x=1.2, y=1.2, z=0.9),
    )
    return go.Figure(traces, layout=_layout(scene))


def anim_payload(result: MCResult, k: int = 120, max_t: int = 140) -> dict:
    """Datos compactos para la animación en el navegador (JS va recortando los caminos)."""
    d = spaghetti_data(result, k, max_t)
    return dict(
        x=np.round(d["x"], 3).tolist(),
        z=np.round(d["z"], 4).tolist(),
        pct=np.round(d["pct"], 3).tolist(),
        real=np.round(d["real_z"], 4).tolist(),
        real_y=d["real_y"],
        zr=[float(np.nanmin(d["z"])) - 0.02, float(np.nanmax(d["z"])) + 0.02],
        xr=[float(d["x"][0]), float(d["x"][-1])],
        xlab=d["xlab"],
    )


def fig_anim_base(result: MCResult, payload: dict):
    """Figura vacía con los ejes fijos; el JS rellena los caminos fotograma a fotograma."""
    import plotly.graph_objects as go

    tv, tt = money_ticks(10 ** payload["zr"][0], 10 ** payload["zr"][1], log=True)
    k = len(payload["z"])
    traces = [
        go.Scatter3d(
            x=[],
            y=[],
            z=[],
            mode="lines",
            hoverinfo="skip",
            showlegend=False,
            opacity=0.12,
            line=dict(color=[], colorscale=NEON_OUTCOME, cmin=0, cmax=1, width=7),
        ),
        go.Scatter3d(
            x=[],
            y=[],
            z=[],
            mode="lines",
            name="Simulaciones",
            hoverinfo="skip",
            opacity=0.9,
            line=dict(color=[], colorscale=NEON_OUTCOME, cmin=0, cmax=1, width=1.8),
        ),
        go.Scatter3d(
            x=[],
            y=[],
            z=[],
            mode="lines",
            name="Backtest real",
            hoverinfo="skip",
            line=dict(color=GOLD, width=6),
        ),
    ]
    scene = _scene(
        payload["xlab"],
        "Simulación",
        "Equity",
        eye=(-1.55, -1.75, 0.55),
        x=dict(range=payload["xr"]),
        y=dict(range=[-1, k], showticklabels=False),
        z=dict(range=payload["zr"], tickvals=tv, ticktext=tt),
        aspect=dict(x=1.8, y=1.15, z=0.85),
    )
    return go.Figure(traces, layout=_layout(scene))


# ---------------------------------------------------------------- HTML


def header_stats(result: MCResult) -> list[tuple[str, str]]:
    r = result.real
    p = lambda a, q: float(np.percentile(a[np.isfinite(a)], q))  # noqa: E731
    return [
        ("Simulaciones", f"{result.n:,}".replace(",", ".")),
        ("CAGR backtest", f"{r['cagr']:.1%}"),
        ("CAGR sims (p5–p95)", f"{p(result.cagr, 5):.1%} – {p(result.cagr, 95):.1%}"),
        ("Caída backtest", f"{r['max_dd']:.1%}"),
        ("Caída sims (mediana / p5)", f"{p(result.max_dd, 50):.1%} / {p(result.max_dd, 5):.1%}"),
        ("P(kill switch)", f"{result.p_kill:.1%}"),
        ("P(ruina)", f"{result.p_ruin:.1%}"),
        ("P(acabar en pérdidas)", f"{result.p_below_start:.1%}"),
    ]


VIEWS = [
    (
        "spag",
        "🌌 Caminos",
        "Cada hilo es una historia alternativa de tu dinero, ordenadas de peor (rojo, delante) "
        "a mejor (verde, al fondo). El hilo blanco con brillo dorado es lo que pasó de verdad. "
        "Si va por la zona verde, el backtest tuvo suerte; si va por el medio, fue un camino "
        "normal.",
    ),
    (
        "dens",
        "🏔️ Montaña",
        "En cada momento, la altura indica dónde se concentran los caminos (la cresta es el "
        "nivel de dinero más probable). La montaña se ensancha con el tiempo: la "
        "incertidumbre crece. La línea blanca es el backtest; si va por la ladera, fue un "
        "camino poco típico.",
    ),
    (
        "out",
        "💎 Resultados",
        "Cada punto es una simulación entera: cuánto ganó al año, su peor caída y cuánto tardó "
        "en recuperarse. El plano rojo es el kill switch: casi todo lo que está a su izquierda "
        "lo habría disparado. El diamante dorado es el backtest.",
    ),
    (
        "anim",
        "▶️ Animación",
        "Los caminos crecen a la vez desde el mismo punto y el abanico se abre. Pulsa ▶ y "
        "gira con el dedo mientras se mueve.",
    ),
]


_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>__TITLE__ — Monte Carlo 3D</title>
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
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(108px,1fr));gap:5px;
margin-top:10px}
.st{background:rgba(20,26,60,.55);border:1px solid var(--line);border-radius:10px;
padding:7px 9px;box-shadow:0 0 14px rgba(0,229,255,.05) inset}
.st b{display:block;font-size:14px;color:#fff}.st span{font-size:10px;color:var(--mut)}
nav{scrollbar-width:none}nav::-webkit-scrollbar{display:none}
@media(max-width:600px){.st{padding:5px 7px}.st b{font-size:13px}.sub{font-size:11px}}
.st.warn b{color:#ff5277;text-shadow:0 0 10px rgba(255,23,68,.5)}
.st.gold b{color:var(--gold);text-shadow:0 0 10px rgba(255,209,102,.4)}
nav{display:flex;gap:6px;padding:8px 14px;position:sticky;top:0;z-index:5;
background:rgba(5,6,15,.85);backdrop-filter:blur(8px);overflow-x:auto}
nav button{flex:1 0 auto;background:#0d1230;color:var(--fg);border:1px solid var(--line);
border-radius:999px;padding:8px 12px;font-size:13px;cursor:pointer;white-space:nowrap}
nav button.on{border-color:var(--acc);color:#fff;box-shadow:0 0 12px rgba(0,229,255,.45),
0 0 2px var(--acc) inset}
.how{padding:2px 14px 6px;font-size:12.5px;color:var(--mut);line-height:1.35;min-height:34px}
.how b{color:var(--fg)}
.plot{width:100%;height:calc(100svh - 150px);min-height:360px}
.ctl{display:flex;gap:8px;padding:4px 14px 10px;flex-wrap:wrap}
.ctl button{background:#0d1230;color:var(--fg);border:1px solid var(--line);border-radius:8px;
padding:7px 11px;font-size:12.5px}
.ctl button.on{border-color:var(--gold);color:var(--gold)}
footer{padding:10px 14px 24px;font-size:11px;color:#5d6796}
</style></head><body>
<header><h1>__TITLE__</h1>
<div class="sub">Monte Carlo 3D · __METHOD__ · generado __DATE__ (hora de Madrid) ·
arrastra para girar, pellizca para zoom</div>
<div class="stats">__STATS__</div></header>
<nav>__TABS__</nav>
<div class="how" id="how"></div>
<div class="ctl"><button id="spin">🌀 Giro automático</button>
<button id="play" style="display:none">▶ Reproducir</button>
<button id="reset">🎯 Vista inicial</button></div>
<div id="plot" class="plot"></div>
<footer>Simulaciones sobre el backtest histórico; no es una predicción. Solo paper trading.
</footer>
<script>__PLOTLYJS__</script>
<script>
const FIGS=__FIGS__;const HOW=__HOW__;const ANIM=__ANIM__;
const el=document.getElementById('plot');const cfg={responsive:true,displaylogo:false,
modeBarButtonsToRemove:['toImage','resetCameraLastSave3d','hoverClosest3d'],
scrollZoom:true};
let cur=null,spinT=null,playT=null,ang=0;
function show(id){stopPlay();cur=id;document.querySelectorAll('nav button').forEach(b=>
b.classList.toggle('on',b.dataset.id===id));document.getElementById('how').innerHTML=HOW[id];
const f=JSON.parse(JSON.stringify(FIGS[id]));if(innerWidth<700){f.layout.showlegend=false;
f.data.forEach(t=>{if(t.line)t.line.showscale=false;if(t.marker)t.marker.showscale=false;});
cfg.displayModeBar=false;}Plotly.react(el,f.data,f.layout,cfg);
document.getElementById('play').style.display=id==='anim'?'':'none';
const e=f.layout.scene.camera.eye;ang=Math.atan2(e.y,e.x);if(id==='anim')play();}
function spin(){if(spinT){clearInterval(spinT);spinT=null;
document.getElementById('spin').classList.remove('on');return;}
document.getElementById('spin').classList.add('on');spinT=setInterval(()=>{
const c=el._fullLayout.scene.camera;const e=c.eye;const r=Math.hypot(e.x,e.y);ang+=0.012;
Plotly.relayout(el,{'scene.camera.eye':{x:r*Math.cos(ang),y:r*Math.sin(ang),z:e.z}});},40);}
function frame(n){const k=ANIM.z.length,T=ANIM.x.length;const X=[],Y=[],Z=[],C=[];
for(let i=0;i<k;i++){for(let t=0;t<n;t++){X.push(ANIM.x[t]);Y.push(i);Z.push(ANIM.z[i][t]);
C.push(ANIM.pct[i]);}X.push(null);Y.push(null);Z.push(null);C.push(ANIM.pct[i]);}
const rx=ANIM.x.slice(0,n),ry=rx.map(()=>ANIM.real_y),rz=ANIM.real.slice(0,n);
Plotly.restyle(el,{x:[X,X,rx],y:[Y,Y,ry],z:[Z,Z,rz],'line.color':[C,C,'#ffd166']},[0,1,2]);}
function stopPlay(){if(playT){clearInterval(playT);playT=null;}
document.getElementById('play').textContent='▶ Reproducir';}
function play(){stopPlay();let n=2;const T=ANIM.x.length;
document.getElementById('play').textContent='⏸ Pausa';playT=setInterval(()=>{
if(cur!=='anim'){stopPlay();return;}frame(n);n+=2;if(n>T){frame(T);stopPlay();}},70);}
document.getElementById('spin').onclick=spin;
document.getElementById('play').onclick=()=>{playT?stopPlay():play();};
document.getElementById('reset').onclick=()=>show(cur);
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>show(b.dataset.id));
show('spag');
</script></body></html>
"""


def write_html_3d(result: MCResult, cfg: MCConfig, path, title: str, *, k: int = 300) -> Path:
    """HTML autocontenido con las 4 vistas (plotly.js incrustado, sin red)."""
    import plotly.offline as off

    from tlab.report import MADRID

    payload = anim_payload(result)
    figs = {
        "spag": fig_spaghetti(result, k),
        "dens": fig_density(result),
        "out": fig_outcomes(result, cfg),
        "anim": fig_anim_base(result, payload),
    }
    figs_json = "{" + ",".join(f'"{n}":{f.to_json()}' for n, f in figs.items()) + "}"
    stats = []
    for label, val in header_stats(result):
        cls = "warn" if label.startswith("P(kill") else "gold" if "backtest" in label else ""
        stats.append(f'<div class="st {cls}"><b>{val}</b><span>{label}</span></div>')
    tabs = "".join(f'<button data-id="{i}">{t}</button>' for i, t, _ in VIEWS)
    how = {i: f"<b>Cómo leerlo:</b> {h}" for i, _, h in VIEWS}
    method = {
        "block": f"bloques de {result.block_length} días",
        "shuffle": "barajar operaciones",
        "bootstrap": "bootstrap de operaciones",
    }.get(result.method, result.method)
    html = (
        _HTML.replace("__PLOTLYJS__", off.get_plotlyjs())
        .replace("__FIGS__", figs_json)
        .replace("__HOW__", json.dumps(how, ensure_ascii=False))
        .replace("__ANIM__", json.dumps(payload))
        .replace("__STATS__", "".join(stats))
        .replace("__TABS__", tabs)
        .replace("__TITLE__", title)
        .replace("__METHOD__", f"{method}, semilla {result.seed}")
        .replace("__DATE__", pd.Timestamp.now(tz=MADRID).strftime("%Y-%m-%d %H:%M"))
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path
