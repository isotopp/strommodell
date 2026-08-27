"""Behavioral tests for comparable scenario reports."""

from __future__ import annotations

from pathlib import Path

from strommodell import main

ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "tests" / "fixtures" / "scenario.yaml"


def test_report_cli_writes_markdown_and_csv_metrics(tmp_path: Path) -> None:
    main(["run", str(CONFIG), "--output", str(tmp_path)])
    main(["report", str(tmp_path)])

    markdown = (tmp_path / "report.md").read_text()
    assert "gas_power_gw" in markdown
    assert "gas_work_twh" in markdown
    assert (tmp_path / "report.csv").is_file()
