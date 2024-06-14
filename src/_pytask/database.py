"""Contains hooks related to the database."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.engine import make_url

from _pytask.database_utils import create_database
from _pytask.pluginmanager import hookimpl

if TYPE_CHECKING:
    from _pytask.settings import Settings


@hookimpl
def pytask_post_parse(config: Settings) -> None:
    """Post-parse the configuration."""
    path = config.common.root.joinpath(".pytask").as_posix()
    url = make_url(f"sqlite:///{path}/pytask.sqlite3")
    create_database(url)
