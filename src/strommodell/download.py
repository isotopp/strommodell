"""Energy-Charts download service used by the public CLI."""

from __future__ import annotations

import tempfile
import urllib.request
from collections.abc import Callable
from pathlib import Path

from .reference import ImportedReference, import_reference_json

PUBLIC_POWER_URL = (
    "https://api.energy-charts.info/public_power?country=de&"
    "start={year}-01-01&end={year}-12-31"
)
PUBLIC_POWER_TIMEZONE = (
    "UTC (source timestamps); source period is {year} in Europe/Berlin"
)
PUBLIC_POWER_UNITS = "MW (power values; validated by integrating Load to 465.503 TWh)"


def download_reference_json(
    year: int,
    source: str,
    destination_dir: str | Path,
    *,
    fetcher: Callable[[str], bytes] | None = None,
) -> ImportedReference:
    """Download one Energy-Charts year and store it through the import boundary."""
    if source != "energy-charts":
        raise ValueError(f"Unsupported reference-data source: {source}")
    if year < 1:
        raise ValueError(f"Invalid data year: {year}")

    url = PUBLIC_POWER_URL.format(year=year)
    response_bytes = (fetcher or _fetch_bytes)(url)
    filename = f"energy-charts-public-power-de-{year}.json"
    with tempfile.TemporaryDirectory(prefix="strommodell-download-") as temporary_dir:
        source_path = Path(temporary_dir) / filename
        source_path.write_bytes(response_bytes)
        return import_reference_json(
            source_path,
            destination_dir,
            source_url=url,
            year=year,
            timezone=PUBLIC_POWER_TIMEZONE.format(year=year),
            resolution="15 minutes",
            units=PUBLIC_POWER_UNITS,
        )


def _fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "strommodell/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()
