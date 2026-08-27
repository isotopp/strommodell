"""Public import boundary for Energy-Charts reference data."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

REQUIRED_SERIES = ("Load", "Solar", "Wind onshore", "Wind offshore")
SOURCE_NAME = "Fraunhofer ISE Energy-Charts public_power API"
NORMALIZATION = (
    "Aggregate four consecutive 15-minute MW values by arithmetic mean to "
    "hourly MW. Integrate MW over hours to energy."
)


class ReferenceDataError(ValueError):
    """Raised when a reference-data input cannot be imported safely."""


@dataclass(frozen=True)
class ImportedReference:
    """Paths written by :func:`import_reference_json`."""

    raw_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class ReferenceYear:
    """Normalized UTC/GW observations for one historical data year."""

    year: int
    timestamps_utc: tuple[datetime, ...]
    load_gw: tuple[float, ...]
    pv_gw: tuple[float, ...]
    wind_onshore_gw: tuple[float, ...]
    wind_offshore_gw: tuple[float, ...]
    reference_capacity_gw: dict[str, float]
    step_hours: float

    def integrate_power_gwh(self, power_gw: Sequence[float]) -> float:
        """Integrate interval-average power using this year's step size."""
        if len(power_gw) != len(self.timestamps_utc):
            raise ReferenceDataError("Power series length does not match timestamps")
        return math.fsum(power_gw) * self.step_hours

    def to_hourly(self) -> ReferenceYear:
        """Return an hourly mean-power view without changing this reference year."""
        if math.isclose(self.step_hours, 1.0):
            return self
        samples_per_hour = round(1 / self.step_hours)
        if samples_per_hour < 1 or not math.isclose(
            samples_per_hour * self.step_hours, 1.0
        ):
            raise ReferenceDataError(
                "Reference step cannot be aggregated to whole hours"
            )
        if len(self.timestamps_utc) % samples_per_hour:
            raise ReferenceDataError("Reference data does not contain complete hours")

        def hourly_means(values: Sequence[float]) -> tuple[float, ...]:
            return tuple(
                math.fsum(values[start : start + samples_per_hour]) / samples_per_hour
                for start in range(0, len(values), samples_per_hour)
            )

        return ReferenceYear(
            year=self.year,
            timestamps_utc=self.timestamps_utc[::samples_per_hour],
            load_gw=hourly_means(self.load_gw),
            pv_gw=hourly_means(self.pv_gw),
            wind_onshore_gw=hourly_means(self.wind_onshore_gw),
            wind_offshore_gw=hourly_means(self.wind_offshore_gw),
            reference_capacity_gw=self.reference_capacity_gw,
            step_hours=1.0,
        )


def import_reference_json(
    source_path: str | Path,
    destination_dir: str | Path,
    *,
    source_url: str,
    year: int,
    timezone: str,
    resolution: str,
    units: str,
) -> ImportedReference:
    """Copy a valid Energy-Charts JSON snapshot and write its metadata."""
    source = Path(source_path)
    destination = Path(destination_dir)
    if not source.is_file():
        raise ReferenceDataError(f"Reference data file does not exist: {source}")
    if not source_url or not timezone or not resolution or not units:
        raise ReferenceDataError(
            "source_url, timezone, resolution and units are required"
        )

    raw_bytes = source.read_bytes()
    try:
        payload = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise ReferenceDataError(f"Reference data is not valid JSON: {source}") from exc
    samples = _validate_payload(payload, source)

    raw_path = destination / source.name
    metadata_path = raw_path.with_suffix(".metadata.json")
    if raw_path.exists() or metadata_path.exists():
        raise ReferenceDataError(
            f"Refusing to overwrite existing imported data in {destination}"
        )
    destination.mkdir(parents=True, exist_ok=True)

    raw_path.write_bytes(raw_bytes)
    metadata: dict[str, Any] = {
        "source": SOURCE_NAME,
        "url": source_url,
        "retrieved_at_utc": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "country": "DE",
        "year": year,
        "timezone": timezone,
        "resolution": resolution,
        "unit": units,
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "samples": samples,
        "required_series": list(REQUIRED_SERIES),
        "normalization": NORMALIZATION,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ImportedReference(raw_path=raw_path, metadata_path=metadata_path)


def load_reference_year(
    power_path: str | Path,
    year: int = 2024,
    *,
    capacity_path: str | Path | None = None,
) -> ReferenceYear:
    """Load Energy-Charts power and annual-average reference capacities."""
    source = Path(power_path)
    payload = _read_json(source)
    sample_count = _validate_payload(payload, source)
    payload_dict = cast(dict[str, Any], payload)
    timestamps = tuple(
        datetime.fromtimestamp(value, UTC) for value in payload_dict["unix_seconds"]
    )
    if len(timestamps) < 2:
        raise ReferenceDataError("At least two timestamps are required to infer a step")
    intervals = [(right - left).total_seconds() for left, right in pairwise(timestamps)]
    if any(interval <= 0 for interval in intervals) or any(
        interval != intervals[0] for interval in intervals[1:]
    ):
        raise ReferenceDataError(
            "Timestamps must be strictly increasing at a fixed interval"
        )
    step_hours = intervals[0] / 3600

    series = {
        item["name"]: item["data"]
        for item in payload_dict["production_types"]
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    expected_length = len(timestamps)
    if sample_count != expected_length:
        raise ReferenceDataError("Reference data sample count is inconsistent")

    def values(name: str) -> tuple[float, ...]:
        data = series[name]
        if len(data) != expected_length:
            raise ReferenceDataError(f"Series {name!r} does not match timestamps")
        return tuple(float(value) / 1000 for value in data)

    capacities = _load_average_capacities(
        Path(capacity_path)
        if capacity_path is not None
        else source.parent / "energy-charts-installed-power-de.json",
        year,
    )
    return ReferenceYear(
        year=year,
        timestamps_utc=timestamps,
        load_gw=values("Load"),
        pv_gw=values("Solar"),
        wind_onshore_gw=values("Wind onshore"),
        wind_offshore_gw=values("Wind offshore"),
        reference_capacity_gw=capacities,
        step_hours=step_hours,
    )


def _read_json(source: Path) -> object:
    if not source.is_file():
        raise ReferenceDataError(f"Reference data file does not exist: {source}")
    try:
        return json.loads(source.read_bytes())
    except json.JSONDecodeError as exc:
        raise ReferenceDataError(f"Reference data is not valid JSON: {source}") from exc


def _load_average_capacities(source: Path, year: int) -> dict[str, float]:
    payload = _read_json(source)
    if not isinstance(payload, dict):
        raise ReferenceDataError(
            f"Installed-power data must be a JSON object: {source}"
        )
    years = payload.get("time")
    production_types = payload.get("production_types")
    if not isinstance(years, list) or not isinstance(production_types, list):
        raise ReferenceDataError(
            f"Installed-power data is missing time series: {source}"
        )
    try:
        previous_index = years.index(str(year - 1))
        current_index = years.index(str(year))
    except ValueError as exc:
        raise ReferenceDataError(
            f"Installed-power data lacks year-end values for {year - 1}/{year}: {source}"
        ) from exc
    series = {
        item["name"]: item["data"]
        for item in production_types
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    capacity_series = {
        "pv": "Solar DC",
        "wind_onshore": "Wind onshore",
        "wind_offshore": "Wind offshore",
    }
    capacities: dict[str, float] = {}
    for key, name in capacity_series.items():
        data = series.get(name)
        if not isinstance(data, list) or len(data) <= current_index:
            raise ReferenceDataError(f"Installed-power series {name!r} is incomplete")
        previous = data[previous_index]
        current = data[current_index]
        if (
            isinstance(previous, bool)
            or not isinstance(previous, (int, float))
            or isinstance(current, bool)
            or not isinstance(current, (int, float))
            or previous <= 0
            or current <= 0
        ):
            raise ReferenceDataError(
                f"Installed-power series {name!r} has invalid capacity"
            )
        capacities[key] = (float(previous) + float(current)) / 2
    return capacities


def _validate_payload(payload: object, source: Path) -> int:
    if not isinstance(payload, dict):
        raise ReferenceDataError(f"Reference data must be a JSON object: {source}")
    timestamps = payload.get("unix_seconds")
    production_types = payload.get("production_types")
    if not isinstance(timestamps, list) or not timestamps:
        raise ReferenceDataError(f"Missing unix_seconds time axis: {source}")
    if not isinstance(production_types, list):
        raise ReferenceDataError(f"Missing production_types: {source}")

    for value in timestamps:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ReferenceDataError(
                f"unix_seconds contains a non-numeric timestamp: {source}"
            )
        if not math.isfinite(value):
            raise ReferenceDataError(
                f"unix_seconds contains a non-finite timestamp: {source}"
            )

    series_by_name = {
        item.get("name"): item
        for item in production_types
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    missing = [name for name in REQUIRED_SERIES if name not in series_by_name]
    if missing:
        names = ", ".join(missing)
        raise ReferenceDataError(f"Missing required series ({names}): {source}")
    sample_count = len(timestamps)
    for name in REQUIRED_SERIES:
        data = series_by_name[name].get("data")
        if not isinstance(data, list) or len(data) != sample_count:
            raise ReferenceDataError(
                f"Series {name!r} does not align with unix_seconds: {source}"
            )
        for value in data:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ReferenceDataError(
                    f"Series {name!r} contains non-numeric data: {source}"
                )
            if not math.isfinite(value):
                raise ReferenceDataError(
                    f"Series {name!r} contains non-finite data: {source}"
                )
    return sample_count
