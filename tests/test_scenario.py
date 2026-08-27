"""Behavioral tests for complete scenario dispatch."""

from __future__ import annotations

from pathlib import Path

from strommodell.reference import load_reference_year
from strommodell.scenario import Scenario, run_scenario

ROOT = Path(__file__).parents[1]
POWER_FIXTURE = ROOT / "tests" / "fixtures" / "reference-scenario.json"
CAPACITY_FIXTURE = ROOT / "tests" / "fixtures" / "capacity-2023-2024.json"


def test_run_scenario_covers_remaining_load_with_gas() -> None:
    reference = load_reference_year(
        POWER_FIXTURE,
        year=2024,
        capacity_path=CAPACITY_FIXTURE,
    )

    result = run_scenario(
        reference,
        Scenario(
            name="gas-test",
            pv_gw=0,
            wind_onshore_gw=0,
            wind_offshore_gw=0,
            battery_power_gw=100,
            annual_demand_twh=0.1,
            initial_soc_gwh=0,
        ),
    )

    assert result.gas_power_gw == 50
    assert result.gas_work_twh == 0.1
    assert result.unserved_load_twh == 0
