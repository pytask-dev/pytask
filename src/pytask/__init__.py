from _pytask.build import main
from _pytask.cli import cli
from _pytask.config import hookimpl
from _pytask.mark import MARK_GEN as mark  # noqa: N811

__all__ = ["cli", "hookimpl", "main", "mark"]
__version__ = "0.0.11"

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
