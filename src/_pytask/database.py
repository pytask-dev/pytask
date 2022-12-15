"""Implement the database managed with pony."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

import click
import networkx as nx
from _pytask.config import hookimpl
from _pytask.dag import node_and_neighbors
from click import Context
from pony import orm


class _DatabaseProviders(str, Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    ORACLE = "oracle"
    COCKROACH = "cockroach"


db = orm.Database()


class State(db.Entity):  # type: ignore
    """Represent the state of a node in relation to a task."""

    task = orm.Required(str)
    node = orm.Required(str)
    state = orm.Required(str)

    orm.PrimaryKey(task, node)


def create_database(
    provider: str, filename: str, create_db: bool, create_tables: bool
) -> None:
    """Create the database.

    Raises
    ------
    orm.BindingError
        Raise if database is already bound.

    """
    try:
        db.bind(provider=provider, filename=filename, create_db=create_db)
        db.generate_mapping(create_tables=create_tables)
    except orm.BindingError:
        pass


@orm.db_session
def create_or_update_state(first_key: str, second_key: str, state: str) -> None:
    """Create or update a state."""
    try:
        state_in_db = State[first_key, second_key]  # type: ignore
    except orm.ObjectNotFound:
        State(task=first_key, node=second_key, state=state)
    else:
        state_in_db.state = state


def _database_filename_callback(
    ctx: Context, name: str, value: str | None  # noqa: U100
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
            type=click.Choice(_DatabaseProviders),  # type: ignore[arg-type]
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
def pytask_parse_config(
    config: dict[str, Any], config_from_cli: dict[str, Any]
) -> None:
    """Parse the configuration."""
    if not config_from_cli["database_filename"].is_absolute():
        config_from_cli["database_filename"] = config_from_cli["root"].joinpath(
            config["database_filename"]
        )

    for name in (
        "database_provider",
        "database_filename",
        "database_create_db",
        "database_create_tables",
    ):
        config[name] = config_from_cli[name]

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


def update_states_in_database(dag: nx.DiGraph, task_name: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(dag, task_name):
        node = dag.nodes[name].get("task") or dag.nodes[name]["node"]
        create_or_update_state(task_name, node.name, node.state())
