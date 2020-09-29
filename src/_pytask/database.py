"""Implement the database managed with pony."""
from pathlib import Path

import click
from _pytask.config import hookimpl
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from pony import orm


db = orm.Database()


class State(db.Entity):
    """Represent the state of a node in relation to a task."""

    task = orm.Required(str)
    node = orm.Required(str)
    state = orm.Required(str)

    orm.PrimaryKey(task, node)


def create_database(provider, filename, create_db, create_tables):
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
def create_or_update_state(first_key, second_key, state):
    """Create or update a state."""
    try:
        state_in_db = State[first_key, second_key]
    except orm.ObjectNotFound:
        State(task=first_key, node=second_key, state=state)
    else:
        state_in_db.state = state


@hookimpl
def pytask_extend_command_line_interface(cli):
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
def pytask_parse_config(config, config_from_cli, config_from_file):
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
def pytask_post_parse(config):
    create_database(**config["database"])
