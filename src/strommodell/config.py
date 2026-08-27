"""YAML scenario configuration and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .scenario import Scenario


@dataclass(frozen=True)
class ScenarioConfig:
    """Validated paths and scenarios from one YAML configuration."""

    path: Path
    year: int
    power_path: Path
    capacity_path: Path
    scenarios: tuple[Scenario, ...]
    source: str = "energy-charts"


def load_scenario_config(path: str | Path) -> ScenarioConfig:
    """Load and validate a YAML scenario configuration."""
    config_path = Path(path)
    try:
        document = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(
            f"Could not read scenario configuration: {config_path}"
        ) from exc
    if not isinstance(document, dict):
        raise TypeError("Scenario configuration must be a YAML mapping")
    year = _required_int(document, "year")
    if year < 1:
        raise ValueError("Scenario year must be positive")
    power_path = _required_path(document, "power_path", config_path.parent)
    capacity_path = _required_path(document, "capacity_path", config_path.parent)
    source = document.get("source", "energy-charts")
    if not isinstance(source, str) or not source:
        raise ValueError("Scenario source must be a non-empty string")
    scenarios_value = document.get("scenarios")
    if not isinstance(scenarios_value, list) or not scenarios_value:
        raise ValueError("Scenario configuration needs a non-empty scenarios list")

    scenarios: list[Scenario] = []
    names: set[str] = set()
    for index, value in enumerate(scenarios_value):
        if not isinstance(value, dict):
            raise TypeError(f"Scenario at index {index} must be a YAML mapping")
        try:
            scenario = Scenario(
                name=_required_string(value, "name"),
                pv_gw=_required_number(value, "pv_gw"),
                wind_onshore_gw=_required_number(value, "wind_onshore_gw"),
                wind_offshore_gw=_required_number(value, "wind_offshore_gw"),
                battery_power_gw=_required_number(value, "battery_power_gw"),
                annual_demand_twh=_optional_number(value, "annual_demand_twh", 1100.0),
                battery_duration_hours=_optional_number(
                    value, "battery_duration_hours", 4.0
                ),
                initial_soc_gwh=_optional_number_or_none(value, "initial_soc_gwh"),
                charge_efficiency=_optional_number(value, "charge_efficiency", 0.9),
                discharge_efficiency=_optional_number(
                    value, "discharge_efficiency", 0.9
                ),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid scenario at index {index}: {exc}") from exc
        if scenario.name in names:
            raise ValueError(f"Duplicate scenario name: {scenario.name}")
        names.add(scenario.name)
        scenarios.append(scenario)
    return ScenarioConfig(
        path=config_path,
        year=year,
        power_path=power_path,
        capacity_path=capacity_path,
        scenarios=tuple(scenarios),
        source=source,
    )


def _required_string(document: dict[str, Any], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_int(document: dict[str, Any], key: str) -> int:
    value = document.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value


def _required_number(document: dict[str, Any], key: str) -> float:
    value = document.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be numeric")
    return float(value)


def _optional_number(document: dict[str, Any], key: str, default: float) -> float:
    if key not in document:
        return default
    return _required_number(document, key)


def _optional_number_or_none(document: dict[str, Any], key: str) -> float | None:
    if key not in document or document[key] is None:
        return None
    return _required_number(document, key)


def _required_path(document: dict[str, Any], key: str, base: Path) -> Path:
    value = _required_string(document, key)
    return (base / value).resolve()
