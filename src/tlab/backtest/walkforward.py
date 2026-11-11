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


def fixed_windows(
    train_start, first_test, test_months: int, n_windows: int, last_end=None
) -> list[Window]:
    """Ventanas con FECHAS FIJAS (hipotesis.md §3): entrenamiento creciente anclado en
    `train_start`; pruebas consecutivas de `test_months` meses naturales desde `first_test`.
    Si se da `last_end`, se exige que la última ventana acabe exactamente ahí (control)."""
    s, ft = pd.Timestamp(train_start), pd.Timestamp(first_test)
    if s.tz is not None and ft.tz is None:
        ft = ft.tz_localize(s.tz)
    le = None if last_end is None else pd.Timestamp(last_end)
    if le is not None and s.tz is not None and le.tz is None:
        le = le.tz_localize(s.tz)
    out = []
    for i in range(n_windows):
        ts = ft + pd.DateOffset(months=test_months * i)
        te = ts + pd.DateOffset(months=test_months) - pd.Timedelta(days=1)
        out.append(Window(s, ts - pd.Timedelta(days=1), ts, te))
    if le is not None and out[-1].test_end.normalize() != le.normalize():
        raise ValueError(
            f"La última ventana acaba el {out[-1].test_end.date()}, no el "
            f"{le.date()}: revisa el TOML [walkforward]"
        )
    return out


def param_distance(p: dict, default: dict, keys: list[str]) -> float:
    """Distancia relativa a los parámetros por defecto (para desempatar)."""
    return sum(abs(float(p[k]) - float(default[k])) / abs(float(default[k])) for k in keys)


def pick_best(scored: list[tuple[dict, float]], default: dict, keys: list[str]) -> dict:
    """Combinación con mayor Sharpe de entrenamiento; empate (o NaN en todas) → la más cercana
    a la de por defecto. Los Sharpe NaN cuentan como −inf."""

    def key(item):
        p, sh = item
        sh = sh if sh == sh else float("-inf")  # NaN -> -inf
        return (-sh, param_distance(p, default, keys))

    return sorted(scored, key=key)[0][0]
