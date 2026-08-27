"""Behavioral tests for normalized reference years."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strommodell.reference import load_reference_year

ROOT = Path(__file__).parents[1]
POWER_FIXTURE = ROOT / "tests" / "fixtures" / "reference-hourly.json"
CAPACITY_SNAPSHOT = ROOT / "data" / "raw" / "energy-charts-installed-power-de.json"


def test_load_reference_year_integrates_hourly_gigawatts() -> None:
    reference = load_reference_year(
        POWER_FIXTURE,
        year=2024,
        capacity_path=CAPACITY_SNAPSHOT,
    )

    assert reference.load_gw == (1.0, 1.0)
    assert reference.step_hours == 1.0
    assert reference.integrate_power_gwh(reference.load_gw) == 2.0
    assert reference.reference_capacity_gw == pytest.approx(
        {"pv": 92.0435, "wind_onshore": 62.301, "wind_offshore": 8.844}
    )


def test_reference_year_exposes_hourly_mean_power_view(tmp_path: Path) -> None:
    payload = {
        "unix_seconds": [1704067200, 1704068100, 1704069000, 1704069900],
        "production_types": [
            {"name": "Load", "data": [1000, 2000, 3000, 4000]},
            {"name": "Solar", "data": [0, 0, 0, 0]},
            {"name": "Wind onshore", "data": [0, 0, 0, 0]},
            {"name": "Wind offshore", "data": [0, 0, 0, 0]},
        ],
    }
    power_path = tmp_path / "reference-quarter-hour.json"
    power_path.write_text(json.dumps(payload))

    hourly = load_reference_year(
        power_path,
        year=2024,
        capacity_path=CAPACITY_SNAPSHOT,
    ).to_hourly()

    assert hourly.step_hours == 1.0
    assert hourly.timestamps_utc == (datetime(2024, 1, 1, tzinfo=UTC),)
    assert hourly.load_gw == (2.5,)
