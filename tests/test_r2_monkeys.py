"""R2-9 y R2-16: monos a medida (`rank` y `persist`). Casos M1, M3–M7, M11–M14 de la
especificación. Los monos `window` (H6) no existen: H6 está aparcada (E15)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from test_r2_panel import A_SPECIAL, BASE, D0201, P, make_panel
from test_r2_tranches import mini_data, mini_sc

from tlab.backtest.custom_monkeys import (
    MODES,
    derangement,
    make_order_key,
    p_and_percentile,
    persist_order_key,
    run_custom_monkeys,
)
from tlab.backtest.targets import build_target
from tlab.strategies.sector_rank import (
    generate_signals_panel,
    panel_features,
    signals_from_order,
)


def target(settings, sc=None, data=None, **params):
    sc = sc or mini_sc()
    sc = {**sc, "params": {**sc["params"], **params}}
    return build_target(
        "sector_mom", data=data or mini_data(), settings=settings, strat_cfg=sc,
        kill_switch=False, tranche="is",
    )  # fmt: skip


def trades_key(df):
    d = df.sort_values(["symbol", "entry_date"]).reset_index(drop=True)
    return d[["symbol", "entry_date", "exit_date", "qty"]], d["pnl_usd"].to_numpy()


# ---------------------------------------------------------------- M1: identidad
def test_m1_identidad_rank_y_mismas_operaciones(settings):
    t = target(settings)
    feats = panel_features(t.bars, t.params)
    ident = signals_from_order(t.bars, feats, feats.key, t.params)
    ref = generate_signals_panel(t.bars, t.params)
    for s in ref:
        pd.testing.assert_frame_equal(ident[s], ref[s])
    a = t.run_with_signals(ident, "is").trades
    b = t.run(t.params, "is").trades
    (ka, pa), (kb, pb) = trades_key(a), trades_key(b)
    pd.testing.assert_frame_equal(ka, kb)
    assert pa == pytest.approx(pb)


# ---------------------------------------------------------------- M3 / M4 (tabla S1)
def _feats_s1():
    bars = make_panel(BASE, overrides=A_SPECIAL)
    return bars, panel_features(bars, P)


def _flags(out, s):
    r = out[s].loc[D0201]
    return bool(r["entry"]), bool(r["exit"])


def test_m3_orden_inyectado():
    bars, feats = _feats_s1()
    key = pd.DataFrame([[0.1, 0.9, 0.5, 0.99]], index=feats.key.index, columns=feats.key.columns)
    out = signals_from_order(bars, feats, key, P)
    assert _flags(out, "B") == (True, False) and _flags(out, "C") == (True, False)
    assert _flags(out, "A") == (False, False)  # puesto 3 <= keep_n
    assert _flags(out, "D") == (False, True)  # no apto aunque su clave sea la mayor


def test_m4_persistente():
    bars, feats = _feats_s1()
    perm = {"A": "D", "B": "A", "C": "B", "D": "C"}
    key = persist_order_key(feats, perm)
    row = key.loc[D0201]
    assert row["A"] == pytest.approx(-0.03) and row["B"] == pytest.approx(0.10)
    assert row["C"] == pytest.approx(0.05)
    out = signals_from_order(bars, feats, key, P)
    assert _flags(out, "B") == (True, False) and _flags(out, "C") == (True, False)
    assert _flags(out, "A") == (False, False) and _flags(out, "D") == (False, True)


# ---------------------------------------------------------------- M5: derangement
def test_m5_derangement():
    syms = list("ABCDEFGHI")
    for seed in range(200):
        d = derangement(syms, np.random.default_rng(seed))
        assert all(k != v for k, v in d.items())
        assert sorted(d.values()) == syms  # biyección
    seen = {tuple(derangement(list("ABC"), np.random.default_rng(s)).values()) for s in range(100)}
    assert seen == {("B", "C", "A"), ("C", "A", "B")}
    with pytest.raises(ValueError):
        derangement(["A"], np.random.default_rng(0))


# ---------------------------------------------------------------- M6: persistente estable
def test_m6_persistente_estable_y_apto_igual(settings):
    t = target(settings)
    feats = panel_features(t.bars, t.params)
    key = make_order_key("persist", feats, np.random.default_rng(5))
    perm = {}
    for s in key.columns:  # recupera la permutación mirando TODAS las revisiones
        cands = [
            u
            for u in feats.key.columns
            if np.allclose(key[s].to_numpy(), feats.key[u].to_numpy(), equal_nan=True)
        ]
        assert len(cands) == 1  # la misma columna durante toda la simulación
        perm[s] = cands[0]
    assert all(k != v for k, v in perm.items())
    sig = signals_from_order(t.bars, feats, key, t.params)
    for s, df in sig.items():  # el filtro apto no cambia: solo entra quien lo es
        el = feats.eligible[s].reindex(df.index).fillna(False).astype(bool)
        assert not (df["entry"] & ~el).any()


# ---------------------------------------------------------------- M7: ≤ 3 aptos
@pytest.mark.parametrize("mode", MODES)
def test_m7_con_3_aptos_el_mono_es_la_candidata(settings, mode):
    # 3 símbolos y top_n = 3: todos los aptos entran, sea cual sea el orden. ATR grande para que
    # la caja no limite ninguna compra (D8).
    t = target(settings, top_n=3, keep_n=5, atr_mult=10.0)
    ref = t.run(t.params, "is").trades
    assert len(ref) > 0
    kr, pr = trades_key(ref)
    feats = panel_features(t.bars, t.params)
    for i in range(20):
        rng = np.random.default_rng(np.random.SeedSequence([42, i]))
        sig = signals_from_order(t.bars, feats, make_order_key(mode, feats, rng), t.params)
        km, pm = trades_key(t.run_with_signals(sig, "is").trades)
        pd.testing.assert_frame_equal(km, kr)
        assert pm == pytest.approx(pr)


# ---------------------------------------------------------------- M11–M13
def test_m11_reproducible_y_no_depende_de_procesos(settings):
    t = target(settings)
    a = run_custom_monkeys(t, "rank", n=30, seed=42, n_jobs=1)
    b = run_custom_monkeys(t, "rank", n=30, seed=42, n_jobs=1)
    c = run_custom_monkeys(t, "rank", n=30, seed=42, n_jobs=2)
    pd.testing.assert_frame_equal(a.table, b.table)
    pd.testing.assert_frame_equal(a.table, c.table)
    d = run_custom_monkeys(t, "persist", n=30, seed=42, n_jobs=1)
    assert len(d.table) == 30 and d.mode == "persist"


def test_m12_p_y_percentil():
    k, p, pct = p_and_percentile(np.array([0.1, 0.5, np.nan, 0.9]), 0.5)
    assert k == 2 and p == pytest.approx(3 / 5) and pct == pytest.approx(3 / 4)


def test_m13_umbral_n_1000():
    x = np.concatenate([np.full(19, 1.0), np.full(981, 0.0)])
    k, p, _ = p_and_percentile(x, 1.0)
    assert k == 19 and p == pytest.approx(0.01998, abs=1e-5) and p < 0.02
    x = np.concatenate([np.full(20, 1.0), np.full(980, 0.0)])
    k, p, _ = p_and_percentile(x, 1.0)
    assert k == 20 and p == pytest.approx(0.02098, abs=1e-5) and p >= 0.02


def test_monos_sin_sharpe_cuentan_en_n():
    # Todos NaN: nadie supera y el denominador sigue siendo n + 1.
    k, p, pct = p_and_percentile(np.array([np.nan] * 9), 0.5)
    assert k == 0 and p == pytest.approx(1 / 10) and pct == 1.0


def test_modo_window_no_existe(settings):
    with pytest.raises(ValueError, match="window"):
        run_custom_monkeys(target(settings), "window", n=2)


# ---------------------------------------------------------------- M14: ventaja conocida
def test_m14_con_ventaja_conocida_la_candidata_supera_al_percentil_90(settings):
    names = ["AAA", "BBB", "CCC", "RRR", "SSS", "TTT"]
    drift = [0.0012, 0.0009, 0.0006, -0.0002, -0.0004, -0.0006]
    rng = np.random.default_rng(7)
    idx = pd.date_range("2017-01-02", periods=1500, freq="B", tz="UTC")
    data = {}
    for s, mu in zip(names, drift, strict=True):
        close = 100 * np.exp(np.cumsum(rng.normal(mu, 0.006, len(idx))))
        o = np.r_[100.0, close[:-1]]
        data[s] = pd.DataFrame(
            {
                "open": o,
                "high": np.maximum(o, close) * 1.002,
                "low": np.minimum(o, close) * 0.998,
                "close": close,
                "volume": 1000.0,
            },
            index=idx,
        )
    sc = mini_sc(universe=names, params={**mini_sc()["params"], "lookback": 60, "top_n": 2})
    t = build_target(
        "sector_mom", data=data, settings=settings, strat_cfg=sc, kill_switch=False, tranche="is"
    )
    res = run_custom_monkeys(t, "rank", n=100, seed=42, n_jobs=1)
    assert res.percentile >= 0.9


# ---------------------------------------------------------------- script guardado (aceptación)
def test_script_monos_rechaza_holdout_y_full(tmp_path, settings):
    from test_r2_tranches import clean_probe

    from tlab.backtest.monkeys_r2 import run_monkeys_r2
    from tlab.backtest.tranches import TrancheGuardError

    for tr in ("holdout_old", "holdout_new", "full"):
        with pytest.raises(TrancheGuardError):
            run_monkeys_r2(
                "sector_mom", "rank", tr, n=2, confirm_tranche=True, settings=settings,
                strat_cfg=mini_sc(frozen=True), data=mini_data(), reports_dir=tmp_path / "r",
                registry=tmp_path / "reg.md", git_probe=clean_probe,
            )  # fmt: skip


def test_script_monos_replica_exige_confirmacion_y_is_funciona(tmp_path, settings):
    from test_r2_tranches import clean_probe

    from tlab.backtest.monkeys_r2 import run_monkeys_r2
    from tlab.backtest.tranches import TrancheGuardError

    kw = dict(
        settings=settings, data=mini_data(), reports_dir=tmp_path / "r",
        registry=tmp_path / "reg.md", git_probe=clean_probe, n=20, n_jobs=1,
    )  # fmt: skip
    with pytest.raises(TrancheGuardError):
        run_monkeys_r2("sector_mom", "rank", "replica", strat_cfg=mini_sc(frozen=True), **kw)
    out = run_monkeys_r2("sector_mom", "persist", "is", strat_cfg=mini_sc(), **kw)
    assert (out / "monos.csv").exists() and "p = (1 + k)" in (out / "resumen.md").read_text(
        encoding="utf-8"
    )
    assert not (tmp_path / "r" / "oos_log.csv").exists()  # el IS no gasta tramos
