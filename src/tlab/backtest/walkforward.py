"""Ventanas walk-forward cronológicas (entreno/prueba), sin solape en la prueba."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Window:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def make_windows(
    start, end, n_windows: int, train_frac: float = 0.5, anchored: bool = False
) -> list[Window]:
    """Divide [start, end]: los primeros `train_frac` para el primer entreno y el resto en
    `n_windows` bloques de prueba consecutivos. Entreno = ventana móvil de igual longitud
    (o anclada al inicio si anchored=True)."""
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    total = e - s
    train_len = total * train_frac
    test_len = (total - train_len) / n_windows
    out = []
    for i in range(n_windows):
        ts = s + train_len + test_len * i
        te = e if i == n_windows - 1 else ts + test_len
        trs = s if anchored else ts - train_len
        out.append(Window(trs, ts, ts, te))
    return out
