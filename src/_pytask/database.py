"""Implement the database managed with pony."""
from __future__ import annotations

import enum
from pathlib import Path
from typing import Any

import click
from _pytask.click import EnumChoice
from _pytask.config import hookimpl
from _pytask.database_utils import create_database
from click import Context


class _DatabaseProviders(enum.Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    ORACLE = "oracle"
    COCKROACH = "cockroach"


def _database_filename_callback(
    ctx: Context, name: str, value: str | None  # noqa: ARG001
) -> str | None:
    if value is None:
        return ctx.params["root"].joinpath(".pytask.sqlite3")
    return value


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend command line interface."""
    additional_parameters = [
        click.Option(
            ["--database-provider"],
            type=EnumChoice(_DatabaseProviders),
            help=(
                "Database provider. All providers except sqlite are considered "
                "experimental."
            ),
            default=_DatabaseProviders.SQLITE,
        ),
        click.Option(
            ["--database-filename"],
            type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
            help=("Path to database relative to root."),
            default=Path(".pytask.sqlite3"),
            callback=_database_filename_callback,
        ),
        click.Option(
            ["--database-create-db"],
            type=bool,
            help="Create database if it does not exist.",
            default=True,
        ),
        click.Option(
            ["--database-create-tables"],
            type=bool,
            help="Create tables if they do not exist.",
            default=True,
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    if not config["database_filename"].is_absolute():
        config["database_filename"] = config["root"].joinpath(
            config["database_filename"]
        )

    config["database"] = {
        "provider": config["database_provider"].value,
        "filename": config["database_filename"].as_posix(),
        "create_db": config["database_create_db"],
        "create_tables": config["database_create_tables"],
    }


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Post-parse the configuration."""
    create_database(**config["database"])
