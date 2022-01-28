"""This module contains the main namespace for pytask."""
from __future__ import annotations

from _pytask import __version__
from _pytask.build import main
from _pytask.cli import cli
from _pytask.config import hookimpl
from _pytask.graph import build_dag
from _pytask.mark import MARK_GEN as mark  # noqa: N811
from _pytask.nodes import MetaTask
from _pytask.session import Session


__all__ = [
    "__version__",
    "build_dag",
    "cli",
    "hookimpl",
    "main",
    "mark",
    "MetaTask",
    "Session",
]
