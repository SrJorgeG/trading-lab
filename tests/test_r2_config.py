"""R2-1 y R2-2: kill switch al 15 %, techo de las reglas duras y límite de calibración."""

from __future__ import annotations

import pandas as pd
import pytest

from tlab.backtest.portfolio_sim import SimConfig
from tlab.backtest.robustness import calibrate_risk, kill_switch_episodes
from tlab.config import HardRuleError, load_settings, load_strategy_config, validate_settings
from tlab.risk import check_kill_switch


def test_k1_k2_borde_exacto():
    assert check_kill_switch(10000.0, 8500.00, 0.15) is False  # "más de un 15 %"
    assert check_kill_switch(10000.0, 8499.99, 0.15) is True


def test_k3_valor_por_defecto():
    assert check_kill_switch(10000.0, 8499.99) is True
    assert check_kill_switch(10000.0, 8500.0) is False


def test_k4_episodios_por_defecto():
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    eq = pd.Series([100.0, 86.0, 84.9], index=idx)
    assert kill_switch_episodes(eq) == [idx[2]]  # 84,9 < 85; 86 no


def test_k5_settings_al_15():
    assert load_settings()["risk"]["kill_switch_drawdown"] == 0.15


def test_k6_techo_kill_switch():
    with pytest.raises(HardRuleError):
        validate_settings({"risk": {"kill_switch_drawdown": 0.16}})


@pytest.mark.parametrize(
    "key,val",
    [("risk_per_trade", 0.011), ("max_positions", 4), ("max_gross_exposure", 1.01)],
)
def test_k7_techo_otras_reglas(key, val):
    with pytest.raises(HardRuleError):
        validate_settings({"risk": {key: val}})


def test_k8_mas_estricto_pasa():
    s = {"risk": {"kill_switch_drawdown": 0.10}}
    assert validate_settings(s) is s


def test_valor_no_positivo_falla():
    with pytest.raises(HardRuleError):
        validate_settings({"risk": {"risk_per_trade": 0.0}})


def test_load_settings_valida(tmp_path):
    p = tmp_path / "s.toml"
    p.write_text("[risk]\nkill_switch_drawdown = 0.2\n")
    with pytest.raises(HardRuleError):
        load_settings(p)


def test_k9_simconfig_por_defecto():
    assert SimConfig().kill_switch_drawdown == 0.15


# ---------------------------------------------------------------- R2-2
def test_l1_l2_l3():
    lvl = {0.01: -0.13, 0.0075: -0.119, 0.005: -0.08}
    assert calibrate_risk(lvl, limit=0.12) == 0.0075
    assert calibrate_risk({0.01: -0.12, 0.0075: -0.1}, limit=0.12) == 0.01  # el borde entra
    assert calibrate_risk({0.01: -0.20, 0.0075: -0.16, 0.005: -0.121}, limit=0.12) is None


def test_l4_limit_obligatorio():
    with pytest.raises(TypeError):
        calibrate_risk({0.01: -0.05})  # type: ignore[call-arg]


def test_l5_casos_de_la_ronda_1_con_limite_explicito():
    assert calibrate_risk({0.01: -0.15, 0.0075: -0.099, 0.005: -0.07}, limit=0.10) == 0.0075
    assert calibrate_risk({0.01: -0.08, 0.0075: -0.06, 0.005: -0.04}, limit=0.10) == 0.01
    assert calibrate_risk({0.01: -0.30, 0.0075: -0.2, 0.005: -0.11}, limit=0.10) is None


@pytest.mark.parametrize("sid", ["donchian_crypto", "donchian_etf", "tsmom_etf", "rsi2_etf"])
def test_l6_ronda1_conserva_010(sid):
    assert load_strategy_config(sid)["calibration_dd_limit"] == 0.10
