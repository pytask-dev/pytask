from pathlib import Path

import pytask
from pony import orm
from pytask.shared import get_first_not_none_value

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


@pytask.hookimpl
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
