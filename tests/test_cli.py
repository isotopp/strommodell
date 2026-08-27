"""End-to-end checks for the public command-line interface."""

from __future__ import annotations

import subprocess


def test_help_lists_run_subcommand() -> None:
    result = subprocess.run(
        ["strommodell", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "run" in result.stdout
