"""Monte Carlo en 3D: HTML interactivo (móvil incluido) + previews PNG.

Ejemplos:

    uv run python scripts/montecarlo_3d.py --run donchian_nokill --method block
    uv run python scripts/montecarlo_3d.py --run tsmom_12m_1n --method block --png
    uv run python scripts/montecarlo_3d.py --run donchian_nokill --png --spin /tmp/giro.mp4

El HTML se guarda junto al backtest como ``montecarlo_<método>_3d.html`` y
funciona sin internet (plotly.js va dentro). Ábrelo en el navegador del móvil:
arrastra para girar y pellizca para hacer zoom.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from montecarlo import resolve_run  # noqa: E402

from tlab.backtest.montecarlo import (  # noqa: E402
    DEFAULT_BLOCK,
    DEFAULT_KILL,
    DEFAULT_N,
    DEFAULT_RUIN,
    DEFAULT_SEED,
    METHODS,
    MCConfig,
    load_run,
    run_montecarlo,
)
from tlab.backtest.montecarlo3d import (  # noqa: E402
    BG,
    FG,
    fig_density,
    fig_outcomes,
    fig_spaghetti,
    header_stats,
    write_html_3d,
)
from tlab.config import ROOT  # noqa: E402


def _titled(fig, title: str, subtitle: str):
    fig.update_layout(
        margin=dict(l=0, r=0, t=70, b=0),
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:14px;color:#8f9bd0'>{subtitle}</span>",
            x=0.02,
            y=0.97,
            font=dict(size=24, color=FG),
        ),
        paper_bgcolor=BG,
    )
    return fig


def write_pngs(result, cfg, title: str, out_prefix: Path, width=1600, height=1000) -> list[Path]:
    import plotly.io as pio

    s = dict(header_stats(result))
    sub = (
        f"{result.n:,} simulaciones".replace(",", ".")
        + f" · CAGR backtest {s['CAGR backtest']} · caída backtest {s['Caída backtest']}"
        + f" · P(kill switch) {s['P(kill switch)']}"
    )
    figs = [
        _titled(fig_spaghetti(result), f"{title} — caminos alternativos", sub),
        _titled(fig_density(result), f"{title} — montaña de probabilidad", sub),
        _titled(fig_outcomes(result, cfg), f"{title} — nube de resultados", sub),
    ]
    paths = [Path(f"{out_prefix}_{i}.png") for i in range(1, 4)]
    pio.write_images(figs, paths, width=width, height=height, scale=1)
    return paths


def write_spin(result, title: str, out: Path, seconds: float = 10.0, fps: int = 24) -> Path:
    """Vídeo girando la vista spaghetti (plotly → PNG por fotograma → ffmpeg)."""
    import numpy as np
    import plotly.io as pio

    base = fig_spaghetti(result, k=260)
    _titled(base, f"{title} — Monte Carlo 3D", f"{result.n:,} simulaciones".replace(",", "."))
    base.update_layout(showlegend=False)
    eye = base.layout.scene.camera.eye
    r = float(np.hypot(eye.x, eye.y))
    a0 = float(np.arctan2(eye.y, eye.x))
    n = int(seconds * fps)
    with tempfile.TemporaryDirectory() as tmp:
        figs, files = [], []
        for i in range(n):
            a = a0 + 2 * np.pi * i / n
            z = float(eye.z) + 0.25 * np.sin(2 * np.pi * i / n)
            f = pio.from_json(base.to_json())
            f.update_layout(scene_camera_eye=dict(x=r * np.cos(a), y=r * np.sin(a), z=z))
            figs.append(f)
            files.append(Path(tmp) / f"f{i:04d}.png")
        pio.write_images(figs, files, width=1280, height=720, scale=1)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                str(fps),
                "-i",
                str(Path(tmp) / "f%04d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "23",
                "-movflags",
                "+faststart",
                str(out),
            ],
            check=True,
        )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="carpeta, id o slug (ver montecarlo.py --list)")
    ap.add_argument("--method", choices=METHODS, default="block")
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--block", type=int, default=DEFAULT_BLOCK)
    ap.add_argument("--kill", type=float, default=DEFAULT_KILL)
    ap.add_argument("--ruin", type=float, default=DEFAULT_RUIN)
    ap.add_argument("--paths", type=int, default=300, help="caminos en la vista spaghetti")
    ap.add_argument("--title", default=None, help="título corto (por defecto, el del resumen.md)")
    ap.add_argument("--out", default=None, help="ruta del HTML (por defecto junto al backtest)")
    ap.add_argument("--png", action="store_true", help="guarda también 3 previews PNG")
    ap.add_argument("--png-prefix", default=None, help="prefijo de los PNG (…_1.png, _2, _3)")
    ap.add_argument("--spin", default=None, help="ruta .mp4 de un vídeo girando (tarda ~1 min)")
    a = ap.parse_args(argv)

    folder = resolve_run(a.run)
    equity, trades, meta = load_run(folder)
    cfg = MCConfig(
        n=a.n,
        seed=a.seed,
        method=a.method,
        block_length=a.block,
        kill_switch=a.kill,
        ruin_threshold=a.ruin,
        keep_paths=True,
    )
    result = run_montecarlo(equity, trades, cfg)
    title = a.title or meta.get("title", folder.name)
    out = Path(a.out) if a.out else folder / f"montecarlo_{a.method}_3d.html"
    write_html_3d(result, cfg, out, title, k=a.paths)
    size = out.stat().st_size / 1e6

    def rel(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(ROOT))
        except ValueError:
            return str(p)

    print(f"HTML 3D: {rel(out)} ({size:.1f} MB)")
    if a.png:
        prefix = Path(a.png_prefix) if a.png_prefix else out.with_suffix("")
        for p in write_pngs(result, cfg, title, prefix):
            print(f"PNG: {rel(p)}")
    if a.spin:
        print(f"Vídeo: {rel(write_spin(result, title, Path(a.spin)))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
