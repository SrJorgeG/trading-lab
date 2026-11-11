"""El visor arranca sin errores (si Streamlit está instalado) y el comando antiguo sigue vivo."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("script", ["visor.py", "visor_montecarlo.py"])
def test_visor_renders_tabs(script):
    testing = pytest.importorskip("streamlit.testing.v1")
    at = testing.AppTest.from_file(str(ROOT / "scripts" / script), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    labels = [t.label for t in at.tabs]
    for want in ("🎲 Monte Carlo", "🗺️ Mapa de parámetros", "🐒 Contra el azar"):
        assert want in labels


def test_scripts_help_runs():
    import subprocess
    import sys

    for s in ("param_sweep.py", "random_benchmark.py"):
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / s), "--help"], capture_output=True, text=True
        )
        assert out.returncode == 0 and "in-sample" in out.stdout


def test_cli_refuses_oos_without_confirm(monkeypatch, settings):
    import importlib.util

    from conftest import make_bars

    import tlab.backtest.targets as tg

    data = {"SPY": make_bars(1200, seed=1)}
    real_build = tg.build_target
    for s in ("param_sweep", "random_benchmark"):
        spec = importlib.util.spec_from_file_location(s, ROOT / "scripts" / f"{s}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        monkeypatch.setattr(
            mod,
            "build_target",
            lambda *a, **k: real_build(*a, **{**k, "data": data, "settings": settings}),
        )
        args = ["--strategy", "tsmom_12m", "--universe", "SPY", "--period", "oos", "--no-registry"]
        if s == "param_sweep":
            args += ["--grid", "months=3:6"]
        assert mod.main(args) == 3
