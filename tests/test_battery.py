"""Behavioral tests for four-hour battery dispatch."""

from __future__ import annotations

import pytest

from strommodell.battery import dispatch_battery


def test_battery_fills_to_energy_limit_and_curtails_remaining_surplus() -> None:
    result = dispatch_battery(
        (-125.0, -125.0, -125.0, -125.0),
        power_gw=100,
        duration_hours=4,
        initial_soc_gwh=0,
        charge_efficiency=1,
        step_hours=1,
    )

    assert result.energy_capacity_gwh == 400
    assert result.state_of_charge_gwh[-1] == pytest.approx(400)
    assert result.charge_gw[-1] == pytest.approx(100)
    assert result.curtailment_gw[-1] == pytest.approx(25)
    assert max(result.charge_gw) <= 100


def test_battery_defaults_to_half_full_and_accounts_for_discharge_loss() -> None:
    result = dispatch_battery((100.0,), power_gw=100, duration_hours=4, step_hours=1)

    assert result.initial_soc_gwh == pytest.approx(200)
    assert result.discharge_gw == (100,)
    assert result.remaining_residual_gw == (0,)
    assert result.final_soc_gwh == pytest.approx(200 - 100 / 0.9)
