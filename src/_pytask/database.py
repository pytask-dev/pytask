"""Contains hooks related to the database."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import typed_settings as ts
from click import BadParameter
from click import Context
from sqlalchemy.engine import URL
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from _pytask.database_utils import create_database
from _pytask.pluginmanager import hookimpl

if TYPE_CHECKING:
    from _pytask.settings import SettingsBuilder


def _database_url_callback(
    ctx: Context,  # noqa: ARG001
    name: str,  # noqa: ARG001
    value: str | None,
) -> URL | None:
    """Check the url for the database."""
    # Since sqlalchemy v2.0.19, we need to shortcircuit here.
    if value is None:
        return None

    try:
        return make_url(value)
    except ArgumentError:
        msg = (
            "The 'database_url' must conform to sqlalchemy's url standard: "
            "https://docs.sqlalchemy.org/en/latest/core/engines.html#backend-specific-urls."
        )
        raise BadParameter(msg) from None


@ts.settings
class Database:
    """Settings for the database."""

    database_url: str = ts.option(
        default=None,
        help="Url to the database.",
        click={
            "show_default": "sqlite:///.../.pytask/pytask.sqlite3",
            "callback": _database_url_callback,
        },
    )


@hookimpl
def pytask_extend_command_line_interface(
    settings_builders: dict[str, SettingsBuilder],
) -> None:
    """Extend the command line interface."""
    for settings_builder in settings_builders.values():
        settings_builder.option_groups["database"] = Database()


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    # Set default.
    if not config["database_url"]:
        config["database_url"] = make_url(
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
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Post-parse the configuration."""
    create_database(config["database_url"])
