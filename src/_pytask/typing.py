import sys


# try/except ImportError does NOT work. c.f. https://github.com/python/mypy/issues/8520.
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    try:
        from typing_extensions import Literal
    except ImportError:
        Literal

__all__ = ["Literal"]
