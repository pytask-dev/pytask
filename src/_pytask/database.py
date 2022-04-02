"""Implement the database managed with pony."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

import click
import networkx as nx
from _pytask.attrs import convert_to_none_or_type
from _pytask.config import hookimpl
from _pytask.config_utils import parse_click_choice
from _pytask.dag import node_and_neighbors
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from _pytask.typed_settings import option
from pony import orm


class _DatabaseProviders(Enum):
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


class DatabaseProviders(Enum):
    sqlite = "sqlite"
    postgres = "postgres"
    mysql = "mysql"
    oracle = "oracle"
    cockroach = "cockroach"


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend command line interface."""
    cli["build"]["options"]["database_provider"] = option(
        default=DatabaseProviders.sqlite,
        type=DatabaseProviders,
        help=(
            "Database provider. All providers except sqlite are considered "
            "experimental. [dim]\\[default: sqlite][/]"
        ),
    )
    cli["build"]["options"]["database_filename"] = option(
        default=".pytask.sqlite3",
        help="Path to database relative to root. [dim]\\[default: .pytask.sqlite3][/]",
        type=str,
    )
    cli["build"]["options"]["database_create_db"] = option(
        default=True,
        is_flag=True,
        help="Create database if it does not exist. [dim]\\[default: True][/]",
        param_decls="--database-create-db",
        type=bool,
    )
    cli["build"]["options"]["database_create_tables"] = option(
        default=True,
        is_flag=True,
        param_decls="--database-create-tables",
        type=bool,
        help="Create tables if they do not exist. [dim]\\[default: True][/]",
    )


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Post-parse the configuration."""
    create_database(
        provider=config.option.database_provider.value,
        filename=_create_path_to_database(
            config.option.database_filename, config.option.root
        ),
        create_db=config.option.database_create_db,
        create_tables=config.option.database_create_tables,
    )


def update_states_in_database(dag: nx.DiGraph, task_name: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(dag, task_name):
        node = dag.nodes[name].get("task") or dag.nodes[name]["node"]
        create_or_update_state(task_name, node.name, node.state())


def _create_path_to_database(database_filename, root):
    path = Path(database_filename)
    if not path.is_absolute():
        path = root.joinpath(path)
    return path.resolve().as_posix()
