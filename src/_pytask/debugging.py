"""Contains everything related to debugging."""
from __future__ import annotations

import functools
import pdb  # noqa: T100
import sys
from typing import Any
from typing import ClassVar
from typing import Generator
from typing import TYPE_CHECKING

import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.node_protocols import PTask
from _pytask.outcomes import Exit
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from _pytask.traceback import render_exc_info


if TYPE_CHECKING:
    import pluggy
    from _pytask.session import Session
    from types import TracebackType
    from types import FrameType
    from _pytask.capture import CaptureManager
    from _pytask.live import LiveManager


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend command line interface."""
    additional_parameters = [
        click.Option(
            ["--pdb"],
            help="Start the interactive debugger on errors.",
            is_flag=True,
            default=False,
        ),
        click.Option(
            ["--trace"],
            help="Enter debugger in the beginning of each task.",
            is_flag=True,
            default=False,
        ),
        click.Option(
            ["--pdbcls"],
            help=(
                "Start a custom debugger on errors. For example: "
                "--pdbcls=IPython.terminal.debugger:TerminalPdb"
            ),
            type=str,
            default=None,
            metavar="module_name:class_name",
            callback=_pdbcls_callback,
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


def _pdbcls_callback(
    ctx: click.Context, name: str, value: str | None  # noqa: ARG001
) -> tuple[str, str] | None:
    """Validate the debugger class string passed to pdbcls."""
    message = "'pdbcls' must be like IPython.terminal.debugger:TerminalPdb"

    if value is None:
        return None
    if isinstance(value, str):
        split = value.split(":")
        if len(split) != 2:  # noqa: PLR2004
            raise click.BadParameter(message)
        return tuple(split)  # type: ignore[return-value]
    raise click.BadParameter(message)


@hookimpl(trylast=True)
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Post parse the configuration.

    Register the plugins in this step to let other plugins influence the pdb or trace
    option and may be disable it. Especially thinking about pytask-parallel.

    """
    if config["pdb"]:
        config["pm"].register(PdbDebugger)

    if config["trace"]:
        config["pm"].register(PdbTrace)

    PytaskPDB._saved.append(
        (pdb.set_trace, PytaskPDB._pluginmanager, PytaskPDB._config)
    )
    pdb.set_trace = PytaskPDB.set_trace
    PytaskPDB._pluginmanager = config["pm"]
    PytaskPDB._config = config


@hookimpl
def pytask_unconfigure() -> None:
    """Return the resources.

    If the :func:`pdb.set_trace` function would not be returned, using breakpoints in
    test functions with pytask would fail.

    """
    pdb.set_trace, _, _ = PytaskPDB._saved.pop()


class PytaskPDB:
    """Pseudo PDB that defers to the real pdb."""

    _pluginmanager: pluggy.PluginManager | None = None
    _config: dict[str, Any] | None = None
    _saved: ClassVar[list[tuple[Any, ...]]] = []
    _recursive_debug: int = 0
    _wrapped_pdb_cls: tuple[type[pdb.Pdb], type[pdb.Pdb]] | None = None

    @classmethod
    def _is_capturing(cls, capman: CaptureManager) -> bool:
        """Check if the capture manager is capturing."""
        if capman:
            return capman.is_capturing()
        return False

    @classmethod
    def _import_pdb_cls(
        cls, capman: CaptureManager, live_manager: LiveManager
    ) -> type[pdb.Pdb]:
        """Create a debugger from an imported class."""
        if not cls._config:
            import pdb  # noqa: T100

            # Happens when using pytask.set_trace outside of a task.
            return pdb.Pdb

        usepdb_cls = cls._config["pdbcls"]

        if cls._wrapped_pdb_cls and cls._wrapped_pdb_cls[0] == usepdb_cls:
            return cls._wrapped_pdb_cls[1]

        if usepdb_cls:
            modname, classname = usepdb_cls

            try:
                __import__(modname)
                mod = sys.modules[modname]

                # Handle --pdbcls=pdb:pdb.Pdb (useful e.g. with pdbpp).
                parts = classname.split(".")
                pdb_cls = getattr(mod, parts[0])
                for part in parts[1:]:
                    pdb_cls = getattr(pdb_cls, part)
            except Exception as exc:  # noqa: BLE001
                value = f"{modname}:{classname}"
                msg = f"--pdbcls: could not import {value!r}: {exc}."
                raise ValueError(msg) from exc
        else:
            import pdb  # noqa: T100

            pdb_cls = pdb.Pdb

        wrapped_cls = cls._get_pdb_wrapper_class(pdb_cls, capman, live_manager)
        cls._wrapped_pdb_cls = (usepdb_cls, wrapped_cls)
        return wrapped_cls

    @classmethod
    def _get_pdb_wrapper_class(  # noqa: C901
        cls, pdb_cls: type[pdb.Pdb], capman: CaptureManager, live_manager: LiveManager
    ) -> type[pdb.Pdb]:
        """Create a pdf wrapper class."""

        # Type ignored because mypy doesn't support "dynamic"
        # inheritance like this.
        class PytaskPdbWrapper(pdb_cls):  # type: ignore[valid-type,misc]
            _pytask_capman = capman
            _pytask_live_manager = live_manager
            _continued = False

            def do_debug(self, arg: Any) -> None:
                cls._recursive_debug += 1
                ret = super().do_debug(arg)
                cls._recursive_debug -= 1
                return ret

            def do_continue(self, arg: Any) -> int:
                ret = super().do_continue(arg)
                if cls._recursive_debug == 0:
                    assert cls._config is not None
                    console.print()

                    capman = self._pytask_capman
                    capturing = PytaskPDB._is_capturing(capman)
                    if capturing:
                        console.rule(
                            "PDB continue (IO-capturing resumed)",
                            characters=">",
                            style=None,
                        )
                        assert capman is not None
                        capman.resume()
                    else:
                        console.rule("PDB continue", characters=">", style=None)

                    if not self._pytask_live_manager.is_started:
                        self._pytask_live_manager.resume()

                assert cls._pluginmanager is not None
                self._continued = True
                return ret

            do_c = do_cont = do_continue

            def do_quit(self, arg: Any) -> int:
                """Raise Exit outcome when quit command is used in pdb.

                This is a bit of a hack - it would be better if BdbQuit could be
                handled, but this would require to wrap the whole pytest run, and adjust
                the report etc.

                """
                ret = super().do_quit(arg)

                if cls._recursive_debug == 0:
                    msg = "Quitting debugger"
                    raise Exit(msg)

                return ret

            do_q = do_quit
            do_exit = do_quit

            def setup(self, f: FrameType, tb: TracebackType) -> str:
                """Suspend on setup().

                Needed after do_continue resumed, and entering another breakpoint again.

                """
                ret = super().setup(f, tb)
                if not ret and self._continued:
                    # pdb.setup() returns True if the command wants to exit
                    # from the interaction: do not suspend capturing then.
                    if self._pytask_capman:
                        self._pytask_capman.suspend(in_=True)
                    if self._pytask_live_manager:
                        self._pytask_live_manager.pause()
                return ret

            def get_stack(self, f: FrameType, t: TracebackType) -> tuple[str, int]:
                stack, i = super().get_stack(f, t)
                if f is None:
                    # Find last non-hidden frame.
                    i = max(0, len(stack) - 1)
                    while i and stack[i][0].f_locals.get("__tracebackhide__", False):
                        i -= 1
                return stack, i

        return PytaskPdbWrapper

    @classmethod
    def _init_pdb(
        cls, method: str, *args: Any, **kwargs: Any  # noqa: ARG003
    ) -> pdb.Pdb:
        """Initialize PDB debugging, dropping any IO capturing."""
        if cls._pluginmanager is None:
            capman = None
            live_manager = None
        else:
            capman = cls._pluginmanager.get_plugin("capturemanager")
            live_manager = cls._pluginmanager.get_plugin("live_manager")
        if capman:
            capman.suspend(in_=True)
        if live_manager:
            live_manager.pause()

        if cls._config:
            console.print()

            if cls._recursive_debug == 0:
                # Handle header similar to pdb.set_trace in py37+.
                header = kwargs.pop("header", None)
                if header is not None:
                    console.rule(header, characters=">", style=None)
                else:
                    capturing = cls._is_capturing(capman)
                    if capturing:
                        console.rule(
                            f"PDB {method} (IO-capturing turned off)",
                            characters=">",
                            style=None,
                        )
                    else:
                        console.rule(f"PDB {method}", characters=">", style=None)

        return cls._import_pdb_cls(capman, live_manager)(**kwargs)

    @classmethod
    def set_trace(cls, *args: Any, **kwargs: Any) -> None:
        """Invoke debugging via ``Pdb.set_trace``, dropping any IO capturing."""
        frame = sys._getframe().f_back
        _pdb = cls._init_pdb("set_trace", *args, **kwargs)
        _pdb.set_trace(frame)


class PdbDebugger:
    """Namespace for debugging."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(
        session: Session, task: PTask
    ) -> Generator[None, None, None]:
        """Execute a task by wrapping the function with post-mortem debugger."""
        if isinstance(task, PTask):
            wrap_function_for_post_mortem_debugging(session, task)
        yield


def wrap_function_for_post_mortem_debugging(session: Session, task: PTask) -> None:
    """Wrap the function for post-mortem debugging."""
    task_function = task.function

    @functools.wraps(task_function)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        capman = session.config["pm"].get_plugin("capturemanager")
        live_manager = session.config["pm"].get_plugin("live_manager")
        try:
            task_function(*args, **kwargs)

        except Exception:
            # Order is important! Pausing the live object before the capturemanager
            # would flush the table to stdout and it will be visible in the captured
            # output.
            capman.suspend(in_=True)
            out, err = capman.read()
            live_manager.pause()

            if out or err:
                console.print()

            if out:
                console.rule("Captured stdout", style=None)
                console.print(out)

            if err:
                console.rule("Captured stderr", style=None)
                console.print(err)

            exc_info = remove_internal_traceback_frames_from_exc_info(sys.exc_info())

            console.print()
            console.rule("Traceback", characters=">", style=None)
            console.print(render_exc_info(*exc_info, session.config["show_locals"]))

            post_mortem(exc_info[2])

            live_manager.resume()
            capman.resume()

            raise

    task.function = wrapper


class PdbTrace:
    """Namespace for tracing."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(
        session: Session, task: PTask
    ) -> Generator[None, None, None]:
        """Wrapping the task function with a tracer."""
        if isinstance(task, PTask):
            wrap_function_for_tracing(session, task)
        yield


def wrap_function_for_tracing(session: Session, task: PTask) -> None:
    """Wrap the task function for tracing."""
    _pdb = PytaskPDB._init_pdb("runcall")
    task_function = task.function

    # We can't just return `partial(pdb.runcall, task_function)` because (on python <
    # 3.7.4) runcall's first param is `func`, which means we'd get an exception if one
    # of the kwargs to task_function was called `func`.
    @functools.wraps(task_function)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        capman = session.config["pm"].get_plugin("capturemanager")
        live_manager = session.config["pm"].get_plugin("live_manager")

        # Order is important! Pausing the live object before the capturemanager would
        # flush the table to stdout and it will be visible in the captured output.
        capman.suspend(in_=True)
        out, err = capman.read()
        live_manager.stop()

        if out or err:
            console.print()

        if out:
            console.rule("Captured stdout", style=None)
            console.print(out)

        if err:
            console.rule("Captured stderr", style=None)
            console.print(err)

        _pdb.runcall(task_function, *args, **kwargs)

        live_manager.resume()
        capman.resume()

    task.function = wrapper


def post_mortem(t: TracebackType) -> None:
    """Start post-mortem debugging."""
    p = PytaskPDB._init_pdb("post_mortem")
    p.reset()
    p.interaction(None, t)
    if p.quitting:
        msg = "Quitting debugger"
        raise Exit(msg)
