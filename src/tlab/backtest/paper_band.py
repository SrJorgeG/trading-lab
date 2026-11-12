"""Banda de resultados esperables para el paper (R2-11, hipotesis_ronda2 §3.6 b).

Remuestreo por bloques contiguos de rentabilidades diarias. No reutiliza
`montecarlo.block_bootstrap_returns` (genera trayectorias tan largas como toda la historia).
Solo la herramienta: no se genera ninguna banda real hasta tener la ejecución completa."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

HORIZONS = {"6m": 126, "12m": 252}  # sesiones


def _block_indices(T: int, length: int, block: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """Índices (n, length): ceil(length/block) bloques contiguos (sin envolver) con inicio
    uniforme en [0, T − block], recortados a `length`."""
    n_blocks = math.ceil(length / block)
    # Se sortea bloque a bloque (filas = nº de bloque): los primeros k bloques de cada
    # trayectoria no dependen de cuántos bloques se pidan en total (caso B6).
    starts = rng.integers(0, T - block + 1, size=(n_blocks, n)).T
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)
    return idx[:, :length]


def paper_band(
    daily_returns: np.ndarray,
    horizons: dict[str, int] = HORIZONS,
    block: int = 21,
    n: int = 10_000,
    seed: int = 42,
    percentiles: tuple[int, ...] = (5, 50, 95),
) -> pd.DataFrame:
    """Remuestreo por bloques contiguos de las rentabilidades diarias. Cada trayectoria tiene
    max(horizontes) sesiones; la rentabilidad a `h` sesiones es el producto de las `h`
    primeras. Filas = horizontes, columnas = p5, p50, p95 (rentabilidad acumulada).
    ValueError si T < bloque o si hay NaN."""
    r = np.asarray(daily_returns, dtype=float)
    if np.isnan(r).any():
        raise ValueError("las rentabilidades diarias contienen NaN")
    if len(r) < block:
        raise ValueError(f"hacen falta al menos {block} rentabilidades (hay {len(r)})")
    longest = max(horizons.values())
    rng = np.random.default_rng(seed)
    idx = _block_indices(len(r), longest, block, n, rng)
    growth = np.cumprod(1.0 + r[idx], axis=1)
    rows = {
        name: np.percentile(growth[:, h - 1] - 1.0, percentiles) for name, h in horizons.items()
    }
    return pd.DataFrame(rows, index=[f"p{p}" for p in percentiles]).T


def band_markdown(band: pd.DataFrame, source: str) -> str:
    """Tabla para STRATEGY.md, con la procedencia (informe de la ejecución completa)."""
    lines = [
        f"Banda de resultados esperables (remuestreo por bloques; procedencia: {source}).",
        "",
        "| horizonte | " + " | ".join(band.columns) + " |",
        "|---|" + "---|" * len(band.columns),
    ]
    for h, row in band.iterrows():
        lines.append(f"| {h} | " + " | ".join(f"{v * 100:.2f} %" for v in row) + " |")
    return "\n".join(lines)
