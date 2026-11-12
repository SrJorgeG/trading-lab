"""Monos a medida de H5/H7 (R2-9, E4): controles al azar que usan EL MISMO código de señales,
motor, costes, tope y huecos que la candidata y solo cambian el ORDEN de los aptos.

- `rank`: sorteo mensual (un uniforme por revisión y símbolo).
- `persist` (E4): una permutación sin puntos fijos, la misma durante toda la simulación; el
  símbolo `s` recibe la clave verdadera de `perm[s]`. El filtro `apto` no cambia.
- `window` (H6 `tom_etf`): NO está implementado, H6 está aparcada (E15).

p = (1 + k) / (n + 1), con k = monos con Sharpe >= el real. Un mono sin Sharpe (sin operaciones)
cuenta como «no supera» y sigue contando en n (D7). No se reutiliza `empirical_p`, que descarta
esos monos.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.backtest.random_benchmark import DEFAULT_N, DEFAULT_SEED
from tlab.backtest.targets import Target, extract_metrics
from tlab.strategies.sector_rank import PanelFeatures, panel_features, signals_from_order

MODES = ("rank", "persist")  # `window` aparcado con H6 (E15)


def derangement(symbols: list[str], rng: np.random.Generator) -> dict[str, str]:
    """Permutación sin puntos fijos: baraja y repite hasta que ningún símbolo quede en su
    sitio. Con un solo símbolo → ValueError."""
    syms = sorted(symbols)
    if len(syms) < 2:
        raise ValueError("una permutación sin puntos fijos necesita >= 2 símbolos")
    while True:
        perm = [syms[i] for i in rng.permutation(len(syms))]
        if all(a != b for a, b in zip(syms, perm, strict=True)):
            return dict(zip(syms, perm, strict=True))


def rank_order_key(feats: PanelFeatures, rng: np.random.Generator) -> pd.DataFrame:
    """Mono de sorteo mensual: un uniforme [0, 1) por (revisión, símbolo)."""
    return pd.DataFrame(
        rng.random(feats.key.shape), index=feats.key.index, columns=feats.key.columns
    )


def persist_order_key(feats: PanelFeatures, perm: dict[str, str]) -> pd.DataFrame:
    """Mono persistente (E4): la columna de `s` es feats.key[perm[s]]."""
    return pd.DataFrame(
        {s: feats.key[perm[s]].to_numpy() for s in feats.key.columns},
        index=feats.key.index,
    )


def p_and_percentile(sharpes: np.ndarray, real: float) -> tuple[int, float, float]:
    """(k_ge, p, percentil). k_ge: monos con Sharpe >= el real (NaN no cuenta). p = (1 + k)/(n + 1).
    percentil = monos con Sharpe <= el real sobre n (NaN cuenta como «<=»)."""
    x = np.asarray(sharpes, float)
    n = len(x)
    if not np.isfinite(real):
        return 0, float("nan"), float("nan")
    k = int(np.sum(np.where(np.isfinite(x), x >= real, False)))
    below = int(np.sum(np.where(np.isfinite(x), x <= real, True)))
    return k, (1 + k) / (n + 1), below / n


@dataclass
class MonkeyResult:
    strategy: str
    mode: str
    tranche: str
    n: int
    seed: int
    real: dict  # métricas de la candidata (extract_metrics)
    table: pd.DataFrame  # una fila por mono
    k_ge: int  # monos con Sharpe >= el real (NaN no cuenta)
    p_value: float  # (1 + k_ge) / (n + 1)
    percentile: float  # monos con Sharpe <= el real, sobre n (NaN cuenta como <=)


def make_order_key(mode: str, feats: PanelFeatures, rng: np.random.Generator) -> pd.DataFrame:
    if mode == "rank":
        return rank_order_key(feats, rng)
    if mode == "persist":
        return persist_order_key(feats, derangement(list(feats.key.columns), rng))
    raise ValueError(f"modo de mono desconocido: {mode} (usa {MODES}; `window` está aparcado)")


def one_monkey(target: Target, feats: PanelFeatures, mode: str, seed: int, i: int, period: str):
    """Mono `i`: semilla propia, así el resultado no depende del nº de procesos."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, i]))
    key = make_order_key(mode, feats, rng)
    sigs = signals_from_order(target.bars, feats, key, target.params)
    run = target.run_with_signals(sigs, period)
    return extract_metrics(run, target.ppy, target.bars)


def _chunk(target, feats, mode, seed, ids, period):
    return [(i, one_monkey(target, feats, mode, seed, i, period)) for i in ids]


def run_custom_monkeys(
    target: Target,
    mode: str,
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
    tranche: str = "is",
    n_jobs: int = -1,
) -> MonkeyResult:
    """Ejecuta `n` monos del tipo `mode` sobre el tramo del objetivo (periodo `"is"` del
    objetivo; ver `build_target(..., tranche=...)`). Mismo motor, costes, `f`, tope y huecos
    que la candidata."""
    if mode not in MODES:
        raise ValueError(f"modo de mono desconocido: {mode} (usa {MODES}; `window` está aparcado)")
    if target.cfg.entry_delay != 0:
        raise ValueError("los monos se ejecutan con entry_delay = 0")
    period = "is"
    feats = panel_features(target.bars, target.params)
    real = extract_metrics(target.run(target.params, period), target.ppy, target.bars)
    ids = list(range(n))
    nj = 1
    if n_jobs != 1 and n >= 20:
        from joblib import effective_n_jobs

        nj = max(1, min(effective_n_jobs(n_jobs), n // 10))
    if nj == 1:
        rows = _chunk(target, feats, mode, seed, ids, period)
    else:
        from joblib import Parallel, delayed

        parts = Parallel(n_jobs=nj, backend="loky")(
            delayed(_chunk)(target, feats, mode, seed, ids[j::nj], period) for j in range(nj)
        )
        rows = sorted((r for p in parts for r in p), key=lambda x: x[0])
    table = pd.DataFrame([m for _, m in rows], index=[i for i, _ in rows])
    k, p, pct = p_and_percentile(table["sharpe"].to_numpy(float), real["sharpe"])
    return MonkeyResult(target.strategy, mode, tranche, n, seed, real, table, k, p, pct)


def comparison_lines(res: MonkeyResult) -> list[str]:
    """Nº de operaciones y exposición media de los monos frente a la candidata (E22/M2)."""
    t = res.table
    return [
        "| | candidata | monos (media) | monos (p5 – p95) |",
        "|---|---|---|---|",
        f"| nº de operaciones | {res.real['trades']:.0f} | {t['trades'].mean():.1f} | "
        f"{np.percentile(t['trades'], 5):.0f} – {np.percentile(t['trades'], 95):.0f} |",
        f"| exposición media | {res.real['exposure'] * 100:.1f} % | "
        f"{t['exposure'].mean() * 100:.1f} % | "
        f"{np.percentile(t['exposure'], 5) * 100:.1f} – "
        f"{np.percentile(t['exposure'], 95) * 100:.1f} % |",
    ]


def write_monkey_outputs(res: MonkeyResult, out_dir) -> dict:
    """monos.csv (una fila por mono) y resumen.md. No dice «apta»: muestra cifras."""
    from pathlib import Path

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    res.table.to_csv(out / "monos.csv", index_label="mono")
    md = [
        f"# Monos `{res.mode}` — {res.strategy} — tramo {res.tranche}",
        f"n = {res.n}, semilla {res.seed}. Mismo motor, costes, riesgo y huecos que la candidata.",
        "",
        f"- Sharpe de la candidata: {res.real['sharpe']:.3f}",
        f"- Monos con Sharpe >= el real (k): {res.k_ge}",
        f"- p = (1 + k) / (n + 1) = {res.p_value:.5f}",
        f"- Percentil de la candidata entre los monos: {res.percentile * 100:.1f} %",
        "",
        "## Operaciones y exposición (E22)",
        *comparison_lines(res),
        "",
    ]
    (out / "resumen.md").write_text("\n".join(md), encoding="utf-8")
    return {"monos": out / "monos.csv", "resumen": out / "resumen.md"}
