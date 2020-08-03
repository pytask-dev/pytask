import pluggy
from pytask.mark.structures import MARK_GEN as mark  # noqa: F401, N811

hookimpl = pluggy.HookimplMarker("pytask")


__all__ = ["hookimpl", "mark"]
__version__ = "0.0.4"
