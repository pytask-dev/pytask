"""This module contains the main namespace for pytask."""
from __future__ import annotations

from _pytaks.mark_utils import get_specific_markers_from_task
from _pytaks.mark_utils import has_marker
from _pytaks.mark_utils import remove_markers_from_func
from _pytask import __version__
from _pytask.build import main
from _pytask.cli import cli
from _pytask.config import hookimpl
from _pytask.graph import build_dag
from _pytask.mark import Mark
from _pytask.mark import MARK_GEN as mark  # noqa: N811
from _pytask.mark import MarkDecorator
from _pytask.mark import MarkGenerator
from _pytask.nodes import FilePathNode
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.nodes import PythonFunctionTask
from _pytask.session import Session


__all__ = [
    "__version__",
    "build_dag",
    "cli",
    "get_specific_markers_from_task",
    "has_marker",
    "hookimpl",
    "main",
    "mark",
    "remove_markers_from_func",
    "FilePathNode",
    "Mark",
    "MarkDecorator",
    "MarkGenerator",
    "MetaNode",
    "MetaTask",
    "PythonFunctionTask",
    "Session",
]
