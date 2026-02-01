"""Contains hooks related to the database."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.engine import make_url

from _pytask.database_utils import configure_database_if_present
from _pytask.pluginmanager import hookimpl


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    database_url = config["database_url"]
    # Set default.
    if not database_url:
        config["database_url"] = make_url(
            f"sqlite:///{config['root'].joinpath('.pytask').as_posix()}/pytask.sqlite3"
        )
    elif isinstance(database_url, str):
        config["database_url"] = make_url(database_url)

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
    lockfile_path = config["root"] / "pytask.lock"
    command = config.get("command")
    if lockfile_path.exists() and command in (None, "build"):
        return
    configure_database_if_present(config["database_url"])
