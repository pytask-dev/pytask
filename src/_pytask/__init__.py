import os

from ._version import get_versions

__version__ = get_versions()["version"]
if "CI" in os.environ:
    __version__ = __version__.split("+")[0]

__git_version__ = get_versions()["full-revisionid"]
del get_versions
