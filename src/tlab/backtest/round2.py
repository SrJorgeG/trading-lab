"""Ejecución de un tramo de la ronda 2 (R2-5.6): candado de git y de tramos, universo, costes por
fecha y salida de informes. Las secciones de criterios (R2-10) las añade `r2_report`.

Nunca decide «apta»/«aprobada»: el informe muestra cifras; el veredicto es de Fable."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from functools import partial
from pathlib import Path

import pandas as pd

from tlab import metrics
from tlab.backtest.guards import GitProbe, require_clean_tree
from tlab.backtest.runner import (
    _key,
    asset_entry_dates,
    benchmark_equity,
    candidate_sections,
    info_benchmark_section,
    make_cfg,
    periods_per_year,
    robust_section,
    run_signals,
    wf_fixed_section,
)
from tlab.backtest.tranches import (
    IS_MODES,
    assert_is_allowed,
    check_tranche_guard,
    load_tranche,
    tranche_costs,
    tranche_hash,
)
from tlab.config import ROOT
from tlab.data.loader import load_bars
from tlab.report import MADRID, append_registry, write_report
from tlab.strategies import resolve_signal_fn

BLIND_NOTE = "NO ABRIR hasta que la candidata termine los peldaños 2–3 o muera (E3)."


def _symbols(sc: dict, tr_universe: list[str]) -> list[str]:
    extra = {sc.get("benchmark", tr_universe[0])} | set(sc.get("benchmark_info", {}))
    if sc.get("fixed_income"):
        extra.add(sc["fixed_income"])
    return sorted(set(tr_universe) | extra)


def run_round2(
    strategy: str,
    mode: str,
    sc: dict,
    s: dict,
    params: dict,
    *,
    costs_mode: str,
    entry_delay: int,
    confirm_tranche: bool,
    data: dict | None,
    reports_dir: Path,
    registry: Path,
    git_probe: GitProbe | None = None,
    cash_rate: pd.Series | None = None,
) -> Path:
    """Backtest de un tramo. Devuelve resumen.md (o criterio15.md en `replica`)."""
    if mode == "oos":
        raise ValueError(
            "`oos` no existe para la ronda 2: usa replica/holdout_old/holdout_new/full"
        )
    is_mode = mode in IS_MODES
    tr = load_tranche(sc, "is" if is_mode else mode)
    risk = float(sc.get("risk_per_trade", s["risk"]["risk_per_trade"]))
    # E20/E21: ninguna ejecución (IS incluido) con cambios sin commitear.
    commit = require_clean_tree(git_probe)
    stamp = datetime.now(MADRID).strftime("%Y%m%d-%H%M")
    tag = ("_stress" if costs_mode == "stress" else "") + (
        f"_delay{entry_delay}" if entry_delay else ""
    )
    out = reports_dir / strategy / f"{tr.name if not is_mode else mode}{tag}_{stamp}"
    blind = mode == "replica"
    main_file = "criterio15.md" if blind else "resumen.md"
    rep_rel = str(out.relative_to(reports_dir.parent)) + "/" + main_file
    h = tranche_hash(params, risk)
    if is_mode:
        assert_is_allowed(sc, tr.start, tr.end)
    else:
        check_tranche_guard(
            reports_dir / "oos_log.csv",
            strategy,
            tr.name,
            h,
            costs_mode,
            entry_delay,
            "candidata",
            bool(sc.get("frozen")),
            confirm_tranche,
            report=rep_rel,
            commit=commit,
        )
    # --- datos
    bench = sc.get("benchmark", tr.universe[0])
    bench_info = dict(sc.get("benchmark_info", {}))
    syms = _symbols(sc, tr.universe)
    if data is None:
        from tlab.data.loader import pick_source

        src = pick_source(sc.get("data_source", s["data"]["source"]))
        data_src = f"{src.name} (ajuste: {src.adjustment})"
        data = load_bars(
            syms,
            "1Day",
            start=sc.get("history_start", s["data"]["history_start"]),
            source=src,
            cache_dir=ROOT / s["data"]["cache_dir"],
        )
        if cash_rate is None:  # R2-4: letras a 3 meses (datos de mercado, no un backtest)
            from tlab.data.cash import load_tbill_rate

            cash_rate, _info = load_tbill_rate(s, ROOT / s["data"]["cache_dir"])
    else:
        data_src = "datos pasados por el llamador (tests)"
    end_ts = pd.Timestamp(sc["end"], tz="UTC")
    data = {k: v[v.index <= end_ts] for k, v in data.items()}
    bars = {k: data[k] for k in tr.universe}
    entry_from = asset_entry_dates(bars, int(sc.get("min_history_bars", 365)))
    if sc.get("require_full_universe"):  # D10: no se rebaraja el universo
        late = sorted(k for k, v in entry_from.items() if v > tr.start)
        if late:
            raise ValueError(
                "D10: sin 365 velas al inicio del tramo "
                f"{tr.name} ({tr.start.date()}): {', '.join(late)}. Se anota para Fable."
            )
    # --- simulación
    costs, schedule = tranche_costs(s, tr, costs_mode)
    cfg = replace(make_cfg(s, sc, costs), cost_schedule=schedule)
    if entry_delay:
        cfg = replace(cfg, entry_delay=int(entry_delay))
    fn = resolve_signal_fn(strategy)
    run = partial(run_signals, entry_from=entry_from)
    a, b = tr.start, tr.end
    res = run(bars, params, fn, cfg, a, b)
    assert res.equity.index[-1] <= tr.end, "la curva pasa del fin del tramo"
    if is_mode:
        assert res.equity.index[-1] <= pd.Timestamp(sc["is_end"], tz="UTC")
    ppy = periods_per_year(tr.universe)
    st = metrics.summary(res.equity, res.trades, ppy, res.exposure)
    # D12: benchmarks con el coste vigente en su fecha de compra (= primer paso del tramo).
    beq = benchmark_equity(data, bench, costs, a, b, cfg.initial_equity)
    bm = metrics.summary(beq, None, 252)
    extra = [
        f"Tramo **{tr.name}**: {a.date()} → {b.date()}. Commit: `{commit}`. "
        f"Hash de parámetros y riesgo: `{h}`."
    ]
    if bench_info:
        extra.append(info_benchmark_section(data, bench_info, costs, a, b, cfg.initial_equity))
    if mode == "wf":
        extra.append(wf_fixed_section(bars, params, sc, fn, cfg, a, b, ppy, entry_from))
    if mode == "robust":
        extra.append(
            robust_section(
                bars,
                params,
                sc.get("robust_keys", []),
                fn,
                cfg,
                a,
                b,
                s,
                ppy,
                res,
                run=run,
                sc=sc,
                registry=registry,
                strategy=strategy,
                rep_rel=rep_rel,
            )
        )
    if mode in ("is", "holdout_old", "holdout_new", "full"):
        extra.append(
            candidate_sections(
                res,
                bars,
                params,
                sc,
                s,
                fn,
                costs,
                a,
                b,
                ppy,
                run,
                registry,
                strategy,
                rep_rel,
                "is" if mode == "is" else mode,
                costs_mode,
            )
        )
    from tlab.backtest.r2_report import round2_sections

    extra.append(
        round2_sections(
            mode=mode,
            res=res,
            bars=bars,
            data=data,
            sc=sc,
            s=s,
            tr=tr,
            costs=costs,
            schedule=schedule,
            cfg=cfg,
            log_path=reports_dir / "oos_log.csv",
            strategy=strategy,
            h=h,
            cash_rate=cash_rate,
        )
    )
    data_info = "\n".join(
        f"- {k}: {df.index[0].date()} → {df.index[-1].date()} ({len(df)} velas)"
        for k, df in data.items()
        if k in syms and len(df)
    )
    data_info += (
        "\n"
        + "\n".join(f"- {k} entra al universo el {v.date()}" for k, v in sorted(entry_from.items()))
        + f"\n- Fuente: {data_src}\n- Periodo simulado: {a.date()} → {b.date()} (modo {mode})"
    )
    costs_info = (
        "\n".join(
            f"- {k}: slippage {v.slippage_bps} pb/lado, comisión {v.fee_rate * 100:.3f} %/lado "
            f"+ {v.commission_per_share} $/acc."
            for k, v in costs.items()
        )
        + (
            "\n- Calendario de costes (E11): "
            + "; ".join(
                f"desde {d.date()}: {m['equity'].slippage_bps} pb" for d, m in schedule.steps
            )
            if schedule
            else ""
        )
        + f"\n- Escenario: {costs_mode}\n- Riesgo por operación: {cfg.risk_per_trade * 100:.2f} %"
    )
    sin_ks = "/sin kill switch" if cfg.kill_switch_drawdown is None else ""
    if blind:
        # E3/D5: réplica a ciegas. Solo cifras del criterio 15; el detalle, aparte.
        exp = st.get("expectancy_r", float("nan"))
        out.mkdir(parents=True, exist_ok=True)
        (out / "criterio15.md").write_text(
            "# Réplica — criterio 15 (solo estas cifras; E3)\n"
            f"- Expectancy: {exp:.3f} R\n- Sharpe: {st['sharpe']:.2f}\n"
            f"- Operaciones: {st['trades']}\n"
            "- Percentiles frente a los monos: (se añaden al ejecutar los monos)\n",
            encoding="utf-8",
        )
        write_report(
            out / "detalle",
            f"{strategy} — réplica (DETALLE, no abrir)",
            st,
            bm,
            data_info,
            costs_info,
            params,
            0,
            res.equity,
            res.trades,
            "\n\n".join(extra),
        )
        (out / "detalle" / "README.md").write_text(BLIND_NOTE + "\n", encoding="utf-8")
        key = f"expectancy {exp:.3f} R, Sharpe {st['sharpe']:.2f}, n={st['trades']}"
        append_registry(
            registry,
            strategy,
            {**params, "risk_per_trade": cfg.risk_per_trade},
            f"replica/{costs_mode}{sin_ks}/commit {commit}",
            key,
            rep_rel,
        )
        return out / "criterio15.md"
    mode_txt = f"{tr.name}/{costs_mode}" + (
        f"/retraso {entry_delay} vela [no es variante]" if entry_delay else ""
    )
    n = append_registry(
        registry,
        strategy,
        {**params, "risk_per_trade": cfg.risk_per_trade},
        mode_txt + sin_ks + (f"/commit {commit}" if is_mode else ""),
        _key(st),
        rep_rel,
    )
    return write_report(
        out,
        f"{strategy} — modo {mode} ({sc.get('status', '?')})",
        st,
        bm,
        data_info,
        costs_info,
        params,
        n,
        res.equity,
        res.trades,
        "\n\n".join(extra),
    )
