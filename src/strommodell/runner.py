"""Execute validated scenario configurations and persist results."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import ScenarioConfig, load_scenario_config
from .reference import load_reference_year
from .scenario import ScenarioResult, run_scenario

CAPACITY_RULE = "mean of 31 December capacity in previous and data year"


def run_scenarios(config_path: str | Path, output_dir: str | Path) -> Path:
    """Run every scenario in YAML and return the written manifest path."""
    config = load_scenario_config(config_path)
    reference = load_reference_year(
        config.power_path,
        year=config.year,
        capacity_path=config.capacity_path,
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result_files: list[str] = []
    used_filenames: set[str] = set()
    for scenario in config.scenarios:
        filename = _scenario_filename(scenario.name)
        if filename in used_filenames:
            raise ValueError(
                f"Scenario names resolve to the same output: {scenario.name}"
            )
        used_filenames.add(filename)
        result_path = output / filename
        if result_path.exists():
            raise ValueError(f"Refusing to overwrite existing result: {result_path}")
        result = run_scenario(reference, scenario)
        result_path.write_text(
            json.dumps(_result_document(result, config), indent=2) + "\n",
            encoding="utf-8",
        )
        result_files.append(filename)

    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        raise ValueError(f"Refusing to overwrite existing manifest: {manifest_path}")
    manifest = {
        "schema_version": 1,
        "data": _data_document(config),
        "results": result_files,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _scenario_filename(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-_")
    if not slug:
        raise ValueError(f"Scenario name cannot produce a filename: {name!r}")
    return f"{slug}.json"


def _data_document(config: ScenarioConfig) -> dict[str, Any]:
    return {
        "year": config.year,
        "source": config.source,
        "resolution": "15 minutes",
        "power_path": str(config.power_path),
        "capacity_path": str(config.capacity_path),
        "capacity_rule": CAPACITY_RULE,
    }


def _result_document(result: ScenarioResult, config: ScenarioConfig) -> dict[str, Any]:
    scenario = result.scenario
    return {
        "schema_version": 1,
        "scenario": {
            "name": scenario.name,
            "pv_gw": scenario.pv_gw,
            "wind_onshore_gw": scenario.wind_onshore_gw,
            "wind_offshore_gw": scenario.wind_offshore_gw,
            "battery_power_gw": scenario.battery_power_gw,
            "battery_duration_hours": scenario.battery_duration_hours,
        },
        "data": _data_document(config),
        "metrics": {
            "gas_power_gw": result.gas_power_gw,
            "gas_work_twh": result.gas_work_twh,
            "curtailment_twh": result.curtailment_twh,
            "battery_throughput_gwh": result.battery.throughput_gwh,
            "battery_energy_gwh": result.battery.energy_capacity_gwh,
            "battery_final_soc_gwh": result.battery.final_soc_gwh,
            "demand_peak_gw": result.demand.peak_gw,
            "unserved_load_twh": result.unserved_load_twh,
        },
        "timeseries": {
            "timestamps_utc": [
                timestamp.isoformat() for timestamp in result.generation.timestamps_utc
            ],
            "gas_residual_gw": list(result.gas_residual_gw),
        },
    }
