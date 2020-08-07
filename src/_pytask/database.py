from pathlib import Path

import click
from _pytask.config import hookimpl
from _pytask.shared import get_first_not_none_value
from pony import orm


db = orm.Database()


class State(db.Entity):
    task = orm.Required(str)
    node = orm.Required(str)
    state = orm.Required(str)

    orm.PrimaryKey(task, node)


def create_database(provider, filename, create_db, create_tables):
    try:
        db.bind(provider=provider, filename=filename, create_db=create_db)
        db.generate_mapping(create_tables=create_tables)
    except orm.BindingError:
        pass


@orm.db_session
def create_or_update_state(first_key, second_key, state):
    try:
        state_in_db = State[first_key, second_key]
    except orm.ObjectNotFound:
        State(task=first_key, node=second_key, state=state)
    else:
        state_in_db.state = state


@hookimpl
def pytask_add_parameters_to_cli(command):
    additional_parameters = [
        click.Option(
            ["--database-provider"],
            type=click.Choice(["sqlite", "postgres", "mysql", "oracle", "cockroach"]),
            help="Database provider.  [default: sqlite]",
        ),
        click.Option(
            ["--database-filename"], type=click.Path(), help="Path to database.",
        ),
        click.Option(
            ["--database-create-db"],
            type=bool,
            help="Create database if it does not exist.",
        ),
        click.Option(
            ["--database-create-tables"],
            type=bool,
            help="Create tables if they do not exist.",
        ),
    ]
    command.params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    provider = get_first_not_none_value(
        config_from_cli, config_from_file, key="database_provider", default="sqlite"
    )
    filename = get_first_not_none_value(
        config_from_cli,
        config_from_file,
        key="database_filename",
        default=".pytask.sqlite3",
    )
    filename = Path(filename)
    if not filename.is_absolute():
        filename = Path(config["root"], filename).resolve().as_posix()

    create_db = get_first_not_none_value(
        config_from_cli, config_from_file, key="database_create_db", default=True
    )
    create_tables = get_first_not_none_value(
        config_from_cli, config_from_file, key="database_create_tables", default=True
    )
    config["database"] = {
        "provider": provider,
        "filename": filename,
        "create_db": create_db,
        "create_tables": create_tables,
    }
