import pluggy
from pytask.mark import MARK_GEN as mark  # noqa: F401, N811

__version__ = "0.0.4"


hookimpl = pluggy.HookimplMarker("pytask")
