"""Command-line entry point for the German electricity-system model."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def main(args: Sequence[str] | None = None) -> None:
    """Run the public command-line interface."""
    parser = argparse.ArgumentParser(prog="strommodell")
    subcommands = parser.add_subparsers(dest="command", title="subcommands")
    subcommands.add_parser("download", help="download and document reference data")
    subcommands.add_parser("run", help="run one or more model scenarios")
    subcommands.add_parser("report", help="create a scenario report")
    parser.parse_args(args)
