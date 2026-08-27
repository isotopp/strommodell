"""Command-line entry point for the German electricity-system model."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from .download import download_reference_json
from .runner import run_scenarios

if TYPE_CHECKING:
    from collections.abc import Callable


def main(
    args: Sequence[str] | None = None,
    *,
    fetcher: Callable[[str], bytes] | None = None,
) -> None:
    """Run the public command-line interface."""
    parser = argparse.ArgumentParser(prog="strommodell")
    subcommands = parser.add_subparsers(dest="command", title="subcommands")
    download = subcommands.add_parser(
        "download", help="download and document reference data"
    )
    download.add_argument("--year", required=True, type=int)
    download.add_argument("--source", required=True, choices=("energy-charts",))
    download.add_argument("--output", default=Path("data/raw"), type=Path)
    run = subcommands.add_parser("run", help="run one or more model scenarios")
    run.add_argument("config", type=Path)
    run.add_argument("--output", required=True, type=Path)
    subcommands.add_parser("report", help="create a scenario report")
    options = parser.parse_args(args)
    if options.command == "download":
        try:
            result = download_reference_json(
                options.year,
                options.source,
                options.output,
                fetcher=fetcher,
            )
        except (OSError, TypeError, ValueError) as exc:
            parser.error(str(exc))
        print(f"Wrote {result.raw_path} and {result.metadata_path}")
    elif options.command == "run":
        try:
            manifest_path = run_scenarios(options.config, options.output)
        except (OSError, TypeError, ValueError) as exc:
            parser.error(str(exc))
        print(f"Wrote {manifest_path}")
