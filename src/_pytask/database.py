"""Implement the database managed with pony."""
from pathlib import Path
from typing import Any
from typing import Dict

import click
import networkx as nx
from _pytask.config import hookimpl
from _pytask.dag import node_and_neighbors
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from pony import orm


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


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend command line interface."""
    additional_parameters = [
        click.Option(
            ["--database-provider"],
            type=click.Choice(["sqlite", "postgres", "mysql", "oracle", "cockroach"]),
            help=(
                "Database provider. All providers except sqlite are considered "
                "experimental.  [default: sqlite]"
            ),
            default=None,
        ),
        click.Option(
            ["--database-filename"],
            type=click.Path(),
            help="Path to database relative to root.  [default: .pytask.sqlite3]",
            default=None,
        ),
        click.Option(
            ["--database-create-db"],
            type=bool,
            help="Create database if it does not exist.  [default: True]",
            default=None,
        ),
        click.Option(
            ["--database-create-tables"],
            type=bool,
            help="Create tables if they do not exist.  [default: True]",
            default=None,
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(
    config: Dict[str, Any],
    config_from_cli: Dict[str, Any],
    config_from_file: Dict[str, Any],
) -> None:
    """Parse the configuration."""
    config["database_provider"] = get_first_non_none_value(
        config_from_cli, config_from_file, key="database_provider", default="sqlite"
    )
    filename = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="database_filename",
        default=".pytask.sqlite3",
    )
    filename = Path(filename)
    if not filename.is_absolute():
        filename = Path(config["root"], filename).resolve()
    config["database_filename"] = filename

    config["database_create_db"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="database_create_db",
        default=True,
        callback=convert_truthy_or_falsy_to_bool,
    )
    config["database_create_tables"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="database_create_tables",
        default=True,
        callback=convert_truthy_or_falsy_to_bool,
    )
    config["database"] = {
        "provider": config["database_provider"],
        "filename": config["database_filename"].as_posix(),
        "create_db": config["database_create_db"],
        "create_tables": config["database_create_tables"],
    }


@hookimpl
def pytask_post_parse(config: Dict[str, Any]) -> None:
    """Post-parse the configuration."""
    create_database(**config["database"])


def update_states_in_database(dag: nx.DiGraph, task_name: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(dag, task_name):
        node = dag.nodes[name].get("task") or dag.nodes[name]["node"]
        create_or_update_state(task_name, node.name, node.state())
