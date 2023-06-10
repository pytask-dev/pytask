"""Contains hooks related to the database."""
from __future__ import annotations

from typing import Any

from _pytask.config import hookimpl
from _pytask.database_utils import create_database
from sqlalchemy.engine import make_url


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    if not config["database_url"]:
        config["database_url"] = make_url(
            f"sqlite:///{config['root'].as_posix()}/.pytask.sqlite3"
        )


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Post-parse the configuration."""
    create_database(config["database_url"])
