"""Behavioral tests for the public reference-data import API."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from strommodell.reference import import_reference_json

RAW_SNAPSHOT = (
    Path(__file__).parents[1]
    / "data"
    / "raw"
    / "energy-charts-public-power-de-2024.json"
)


def test_import_json_reproduces_raw_snapshot_and_metadata(tmp_path: Path) -> None:
    result = import_reference_json(
        RAW_SNAPSHOT,
        tmp_path,
        source_url=(
            "https://api.energy-charts.info/public_power?country=de&"
            "start=2024-01-01&end=2024-12-31"
        ),
        year=2024,
        timezone="UTC (source timestamps); source period is 2024 in Europe/Berlin",
        resolution="15 minutes",
        units="MW (power values; validated by integrating Load to 465.503 TWh)",
    )

    assert result.raw_path.read_bytes() == RAW_SNAPSHOT.read_bytes()
    metadata = json.loads(result.metadata_path.read_text())
    assert metadata["source"] == "Fraunhofer ISE Energy-Charts public_power API"
    assert metadata["url"] == (
        "https://api.energy-charts.info/public_power?country=de&"
        "start=2024-01-01&end=2024-12-31"
    )
    assert metadata["year"] == 2024
    assert metadata["timezone"] == (
        "UTC (source timestamps); source period is 2024 in Europe/Berlin"
    )
    assert metadata["resolution"] == "15 minutes"
    assert metadata["unit"] == (
        "MW (power values; validated by integrating Load to 465.503 TWh)"
    )
    assert metadata["sha256"] == hashlib.sha256(RAW_SNAPSHOT.read_bytes()).hexdigest()
    assert metadata["samples"] == 35136
    assert metadata["required_series"] == [
        "Load",
        "Solar",
        "Wind onshore",
        "Wind offshore",
    ]
    datetime.fromisoformat(metadata["retrieved_at_utc"])
