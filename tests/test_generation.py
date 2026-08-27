"""Behavioral tests for scenario generation scaling."""

from __future__ import annotations

from pathlib import Path

from strommodell.generation import scale_generation
from strommodell.reference import load_reference_year

ROOT = Path(__file__).parents[1]
POWER_FIXTURE = ROOT / "tests" / "fixtures" / "reference-scaling.json"
CAPACITY_FIXTURE = ROOT / "tests" / "fixtures" / "capacity-2023-2024.json"


def test_scale_generation_uses_technology_specific_capacity_factor() -> None:
    reference = load_reference_year(
        POWER_FIXTURE,
        year=2024,
        capacity_path=CAPACITY_FIXTURE,
    )

    generation = scale_generation(
        reference,
        pv_gw=40,
        wind_onshore_gw=20,
        wind_offshore_gw=30,
    )

    assert generation.pv_gw == (12.0, 12.0)
    assert generation.wind_onshore_gw == (6.0, 6.0)
    assert generation.wind_offshore_gw == (9.0, 9.0)
