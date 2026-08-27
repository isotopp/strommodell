"""Human- and machine-readable reports for completed runs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPORT_COLUMNS = (
    "scenario",
    "pv_gw",
    "wind_onshore_gw",
    "wind_offshore_gw",
    "battery_power_gw",
    "battery_energy_gwh",
    "gas_power_gw",
    "gas_work_twh",
    "curtailment_twh",
    "battery_throughput_gwh",
    "battery_final_soc_gwh",
    "demand_peak_gw",
    "unserved_load_twh",
)


def write_report(results_dir: str | Path) -> Path:
    """Write Markdown and CSV reports from a completed run directory."""
    directory = Path(results_dir)
    manifest = _load_json(directory / "manifest.json")
    result_names = manifest.get("results")
    if not isinstance(result_names, list) or not result_names:
        raise ValueError("Manifest contains no scenario results")
    documents = [_load_json(directory / name) for name in result_names]
    rows = [_row(document) for document in documents]
    markdown_path = directory / "report.md"
    csv_path = directory / "report.csv"
    if markdown_path.exists() or csv_path.exists():
        raise ValueError("Refusing to overwrite an existing report")
    markdown_path.write_text(
        _markdown(manifest.get("data", {}), documents, rows),
        encoding="utf-8",
    )
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return markdown_path


def _load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read result document: {path}") from exc
    if not isinstance(document, dict):
        raise TypeError(f"Result document must be an object: {path}")
    return document


def _row(document: dict[str, Any]) -> dict[str, Any]:
    scenario = document.get("scenario")
    metrics = document.get("metrics")
    if not isinstance(scenario, dict) or not isinstance(metrics, dict):
        raise TypeError("Result document is missing scenario or metrics")
    row = {
        "scenario": scenario.get("name"),
        "pv_gw": scenario.get("pv_gw"),
        "wind_onshore_gw": scenario.get("wind_onshore_gw"),
        "wind_offshore_gw": scenario.get("wind_offshore_gw"),
        "battery_power_gw": scenario.get("battery_power_gw"),
        "battery_energy_gwh": metrics.get("battery_energy_gwh"),
        "gas_power_gw": metrics.get("gas_power_gw"),
        "gas_work_twh": metrics.get("gas_work_twh"),
        "curtailment_twh": metrics.get("curtailment_twh"),
        "battery_throughput_gwh": metrics.get("battery_throughput_gwh"),
        "battery_final_soc_gwh": metrics.get("battery_final_soc_gwh"),
        "demand_peak_gw": metrics.get("demand_peak_gw"),
        "unserved_load_twh": metrics.get("unserved_load_twh"),
    }
    if any(row[column] is None for column in REPORT_COLUMNS):
        raise ValueError("Result document is missing report metrics")
    return row


def _markdown(
    data: object,
    documents: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> str:
    header = "| " + " | ".join(REPORT_COLUMNS) + " |"
    separator = "| " + " | ".join("---" for _ in REPORT_COLUMNS) + " |"
    body = [
        "| " + " | ".join(str(row[column]) for column in REPORT_COLUMNS) + " |"
        for row in rows
    ]
    assumptions = _assumptions(data, documents)
    return "\n".join(
        [
            "# Strommodell report",
            "",
            *assumptions,
            "",
            header,
            separator,
            *body,
            "",
        ]
    )


def _assumptions(data: object, documents: list[dict[str, Any]]) -> list[str]:
    values = data if isinstance(data, dict) else {}
    first_scenario = documents[0].get("scenario", {})
    charge = first_scenario.get("charge_efficiency", 0.9)
    discharge = first_scenario.get("discharge_efficiency", 0.9)
    return [
        f"- Data year: {values.get('year', 'unknown')}",
        f"- Source: {values.get('source', 'unknown')}",
        f"- Resolution: {values.get('resolution', 'unknown')}",
        f"- Capacity rule: {values.get('capacity_rule', 'unknown')}",
        f"- Battery efficiencies: charge {charge}, discharge {discharge}",
    ]
