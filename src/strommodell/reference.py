"""Public import boundary for Energy-Charts reference data."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
