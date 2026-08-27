"""Behavioral tests for YAML scenario execution."""

from __future__ import annotations

import json
from pathlib import Path

from strommodell import main

ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "tests" / "fixtures" / "scenario.yaml"


def test_run_cli_writes_scenario_result_and_provenance(tmp_path: Path) -> None:
    main(["run", str(CONFIG), "--output", str(tmp_path)])

    result = json.loads((tmp_path / "gas-test.json").read_text())
    assert result["scenario"]["name"] == "gas-test"
    assert result["data"]["year"] == 2024
    assert result["metrics"]["gas_power_gw"] == 50
    assert (tmp_path / "manifest.json").is_file()
