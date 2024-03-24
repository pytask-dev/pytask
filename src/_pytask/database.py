"""Contains hooks related to the database."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy.engine import make_url

from _pytask.database_utils import create_database
from _pytask.pluginmanager import hookimpl
from _pytask.settings import Database

if TYPE_CHECKING:
    from _pytask.settings import Settings
    from _pytask.settings_utils import SettingsBuilder


@hookimpl
def pytask_extend_command_line_interface(
    settings_builders: dict[str, SettingsBuilder],
) -> None:
    """Extend the command line interface."""
    for settings_builder in settings_builders.values():
        settings_builder.option_groups["database"] = Database()


@hookimpl
def pytask_parse_config(config: Settings) -> None:
    """Parse the configuration."""
    # Set default.
    if not config.database.database_url:
        config.database.database_url = make_url(
            f"sqlite:///{config['root'].joinpath('.pytask').as_posix()}/pytask.sqlite3"
        )

    if (
        config["database_url"].drivername == "sqlite"
        and config["database_url"].database
    ) and not Path(config["database_url"].database).is_absolute():
        if config["config"]:
            full_path = (
                config["config"]
                .parent.joinpath(config["database_url"].database)
                .resolve()
            )
        else:
            full_path = (
                config["root"].joinpath(config["database_url"].database).resolve()
            )
        config["database_url"] = config["database_url"]._replace(
            database=full_path.as_posix()
        )


@hookimpl
def pytask_post_parse(config: Settings) -> None:
    """Post-parse the configuration."""
    create_database(config["database_url"])
