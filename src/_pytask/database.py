"""Contains hooks related to the database."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from _pytask.config import hookimpl
from _pytask.database_utils import create_database
from sqlalchemy.engine import make_url


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    # Set default.
    if not config["database_url"]:
        config["database_url"] = make_url(
            f"sqlite:///{config['root'].as_posix()}/.pytask.sqlite3"
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
