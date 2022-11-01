# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Analyse CLI module."""
from pathlib import Path
from typing import List, Optional, cast
from warnings import filterwarnings

import click
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.constants import DEFAULT_SKILL_CONFIG_FILE

from autonomy.analyse.abci.docstrings import process_module
from autonomy.analyse.abci.logs import parse_file
from autonomy.analyse.benchmark.aggregate import BlockTypes, aggregate
from autonomy.analyse.handlers import check_handlers
from autonomy.cli.utils.click_utils import PathArgument, abci_spec_format_flag
from autonomy.cli.utils.spec_helpers import check_all as check_all_fsm
from autonomy.cli.utils.spec_helpers import check_one as check_one_fsm
from autonomy.cli.utils.spec_helpers import update_one as update_one_fsm


BENCHMARKS_DIR = Path("./benchmarks.html")

filterwarnings("ignore")


@click.group(name="analyse")
def analyse_group() -> None:
    """Analyse an agent service."""


@analyse_group.command(name="fsm-specs")
@click.option("--package", type=PathArgument())
@click.option("--app-class", type=str)
@click.option("--update", is_flag=True, help="Update FSM definition if check fails.")
@abci_spec_format_flag()
@pass_ctx
def generate_abci_app_specs(
    ctx: Context,
    package: Optional[Path],
    app_class: Optional[str],
    spec_format: str,
    update: bool,
) -> None:
    """Generate ABCI app specs."""

    all_packages = package is None

    try:
        if all_packages:
            # If package path is not provided check all available packages
            click.echo("Checking all available packages")
            check_all_fsm(Path(ctx.registry_path))
            click.echo("Done")
            return

        if not all_packages and not update:
            click.echo(f"Checking {package}")
            check_one_fsm(
                package_path=cast(Path, package),
                app_class=app_class,
                spec_format=spec_format,
            )
            click.echo("Check successful")
            return

        if not all_packages and update:
            click.echo(f"Updating {package}")
            update_one_fsm(
                package_path=cast(Path, package),
                app_class=app_class,
                spec_format=spec_format,
            )
            click.echo(f"Updated FSM specification for {package}")
            return

        click.echo("Please provide valid arguments")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@analyse_group.group(name="abci")
def abci_group() -> None:
    """Analyse ABCI apps of an agent service."""


@abci_group.command(name="docstrings")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    default=Path("packages/"),
)
@click.option("--check", is_flag=True, default=False)
def docstrings(packages_dir: Path, check: bool) -> None:
    """Analyse ABCI docstring definitions."""

    packages_dir = Path(packages_dir)
    needs_update = set()
    abci_compositions = packages_dir.glob("*/skills/*/rounds.py")

    try:
        for path in sorted(abci_compositions):
            click.echo(f"Processing: {path}")
            if process_module(path, check=check):
                needs_update.add(str(path))

        if len(needs_update) > 0:
            file_string = "\n".join(sorted(needs_update))
            if check:
                raise click.ClickException(
                    f"Following files needs updating.\n\n{file_string}"
                )
            click.echo(f"\nUpdated following files.\n\n{file_string}")
        else:
            click.echo("No update needed.")
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@abci_group.command(name="logs")
@click.argument("file", type=click.Path(file_okay=True, dir_okay=False, exists=True))
def parse_logs(file: Path) -> None:
    """Parse logs of an agent service."""

    try:
        parse_file(str(file))
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@analyse_group.command(name="handlers")
@pass_ctx
@click.option(
    "--common-handlers",
    "-h",
    type=str,
    default=[
        "abci",
    ],
    help="Specify which handlers to check. Eg. -h handler_a -h handler_b -h handler_c",
    multiple=True,
)
@click.option(
    "--ignore",
    "-i",
    type=str,
    default=[
        "abstract_abci",
    ],
    help="Specify which skills to skip. Eg. -i skill_0 -i skill_1 -i skill_2",
    multiple=True,
)
def run_handler_check(
    ctx: Context, ignore: List[str], common_handlers: List[str]
) -> None:
    """Check handler definitions."""

    try:
        for yaml_file in sorted(
            Path(ctx.registry_path).glob(f"*/*/*/{DEFAULT_SKILL_CONFIG_FILE}")
        ):
            if yaml_file.parent.name in ignore:
                click.echo(f"Skipping {yaml_file.parent}")
                continue

            click.echo(f"Checking {yaml_file.parent}")
            check_handlers(
                yaml_file.resolve(),
                common_handlers=common_handlers,
            )
    except (FileNotFoundError, ValueError, ImportError) as e:
        raise click.ClickException(str(e)) from e


@analyse_group.command(name="benchmarks")
@click.argument(
    "path",
    type=click.types.Path(exists=True, dir_okay=True, resolve_path=True),
    required=True,
)
@click.option(
    "--block-type",
    "-b",
    type=click.Choice(choices=(*BlockTypes.types, BlockTypes.ALL), case_sensitive=True),
    default=BlockTypes.ALL,
    required=False,
)
@click.option(
    "--period",
    "-d",
    type=int,
    default=-1,
    required=False,
)
@click.option(
    "--output",
    "-o",
    type=click.types.Path(file_okay=True, dir_okay=False, resolve_path=True),
    default=BENCHMARKS_DIR,
)
def benchmark(path: Path, block_type: str, period: int, output: Path) -> None:
    """Benchmark aggregator."""

    try:
        aggregate(path=path, block_type=block_type, period=period, output=Path(output))
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
