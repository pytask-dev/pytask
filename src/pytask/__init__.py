from _pytask.build import main
from _pytask.cli import cli
from _pytask.config import hookimpl
from _pytask.mark import MARK_GEN as mark  # noqa: N811

from ._version import get_versions

__all__ = ["cli", "hookimpl", "main", "mark"]

__version__ = get_versions()["version"]
del get_versions
