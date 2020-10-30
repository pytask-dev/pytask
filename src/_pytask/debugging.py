"""This module contains everything related to debugging."""
import functools
import pdb
import sys
import traceback

import click
from _pytask.config import hookimpl
from _pytask.nodes import PythonFunctionTask
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info


@hookimpl
def pytask_extend_command_line_interface(cli):
    """Extend command line interface."""
    additional_parameters = [
        click.Option(
            ["--pdb"],
            help="Start the interactive debugger on errors.  [default: False]",
            is_flag=True,
            default=None,
        ),
        click.Option(
            ["--trace"],
            help="Enter debugger in the beginning of each task.  [default: False]",
            is_flag=True,
            default=None,
        ),
        click.Option(
            ["--pdbcls"],
            help=(
                "Start a custom debugger on errors. For example: "
                "--pdbcls=IPython.terminal.debugger:TerminalPdb"
            ),
            metavar="module_name:class_name",
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    """Parse the configuration."""
    config["pdb"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="pdb",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    config["trace"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="trace",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    config["pdbcls"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="pdbcls",
        default=None,
        callback=_pdbcls_callback,
    )


def _pdbcls_callback(x):
    """Validate the debugger class string passed to pdbcls."""
    message = "'pdbcls' must be like IPython.terminal.debugger:TerminalPdb"

    if x in [None, "None", "none"]:
        x = None
    elif isinstance(x, str):
        if len(x.split(":")) != 2:
            raise ValueError(message)
        else:
            x = tuple(x.split(":"))
    else:
        raise ValueError(message)

    return x


@hookimpl(trylast=True)
def pytask_post_parse(config):
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


class PytaskPDB:
    """Pseudo PDB that defers to the real pdb."""

    _pluginmanager = None
    _config = None
    _saved = []
    _recursive_debug = 0
    _wrapped_pdb_cls = None

    @classmethod
    def _is_capturing(cls, capman):
        if capman:
            return capman.is_capturing()
        return False

    @classmethod
    def _import_pdb_cls(cls, capman):
        if not cls._config:
            import pdb

            # Happens when using pytest.set_trace outside of a test.
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
            except Exception as exc:
                value = ":".join((modname, classname))
                raise ValueError(
                    f"--pdbcls: could not import {value!r}: {exc}."
                ) from exc
        else:
            import pdb

            pdb_cls = pdb.Pdb

        wrapped_cls = cls._get_pdb_wrapper_class(pdb_cls, capman)
        cls._wrapped_pdb_cls = (usepdb_cls, wrapped_cls)
        return wrapped_cls

    @classmethod
    def _get_pdb_wrapper_class(cls, pdb_cls, capman):
        # Type ignored because mypy doesn't support "dynamic"
        # inheritance like this.
        class PytaskPdbWrapper(pdb_cls):  # type: ignore[valid-type,misc]
            _pytask_capman = capman
            _continued = False

            def do_debug(self, arg):
                cls._recursive_debug += 1
                ret = super().do_debug(arg)
                cls._recursive_debug -= 1
                return ret

            def do_continue(self, arg):
                ret = super().do_continue(arg)
                if cls._recursive_debug == 0:
                    assert cls._config is not None
                    tm_width = cls._config["terminal_width"]
                    click.echo()

                    capman = self._pytask_capman
                    capturing = PytaskPDB._is_capturing(capman)
                    if capturing:
                        if capturing == "global":
                            click.echo(
                                f"{{:>^{tm_width}}}".format(
                                    " PDB continue (IO-capturing resumed) "
                                )
                            )
                        else:
                            click.echo(
                                f"{{:>^{tm_width}}}".format(
                                    " PDB continue (IO-capturing resumed for "
                                    f"{capturing}) "
                                )
                            )
                        assert capman is not None
                        capman.resume()
                    else:
                        click.echo(f"{{:>^{tm_width}}}".format(" PDB continue "))
                assert cls._pluginmanager is not None
                self._continued = True
                return ret

            do_c = do_cont = do_continue

            def do_quit(self, arg):
                """Raise Exit outcome when quit command is used in pdb.

                This is a bit of a hack - it would be better if BdbQuit could be
                handled, but this would require to wrap the whole pytest run, and adjust
                the report etc.

                """
                ret = super().do_quit(arg)

                if cls._recursive_debug == 0:
                    raise Exception("Quitting debugger")

                return ret

            do_q = do_quit
            do_exit = do_quit

            def setup(self, f, tb):
                """Suspend on setup().

                Needed after do_continue resumed, and entering another
                breakpoint again.

                """
                ret = super().setup(f, tb)
                if not ret and self._continued:
                    # pdb.setup() returns True if the command wants to exit
                    # from the interaction: do not suspend capturing then.
                    if self._pytask_capman:
                        self._pytask_capman.suspend(in_=True)
                return ret

            def get_stack(self, f, t):
                stack, i = super().get_stack(f, t)
                if f is None:
                    # Find last non-hidden frame.
                    i = max(0, len(stack) - 1)
                    while i and stack[i][0].f_locals.get("__tracebackhide__", False):
                        i -= 1
                return stack, i

        return PytaskPdbWrapper

    @classmethod
    def _init_pdb(cls, method, *args, **kwargs):
        """Initialize PDB debugging, dropping any IO capturing."""
        if cls._pluginmanager is None:
            capman = None
        else:
            capman = cls._pluginmanager.get_plugin("capturemanager")
        if capman:
            capman.suspend(in_=True)

        if cls._config:
            click.echo()

            if cls._recursive_debug == 0:
                tm_width = cls._config["terminal_width"]
                # Handle header similar to pdb.set_trace in py37+.
                header = kwargs.pop("header", None)
                if header is not None:
                    click.echo(f"{{:>^{tm_width}}}".format(f" {header} "))
                else:
                    capturing = cls._is_capturing(capman)
                    if capturing == "global":
                        click.echo(
                            f"{{:>^{tm_width}}}".format(
                                f" PDB {method} (IO-capturing turned off) "
                            )
                        )
                    elif capturing:
                        click.echo(
                            f"{{:>^{tm_width}}}".format(
                                f" PDB {method} (IO-capturing turned off for "
                                f"{capturing}) "
                            )
                        )
                    else:
                        click.echo(f"{{:>^{tm_width}}}".format(f" PDB {method} "))

        _pdb = cls._import_pdb_cls(capman)(**kwargs)

        return _pdb

    @classmethod
    def set_trace(cls, *args, **kwargs) -> None:
        """Invoke debugging via ``Pdb.set_trace``, dropping any IO capturing."""
        frame = sys._getframe().f_back
        _pdb = cls._init_pdb("set_trace", *args, **kwargs)
        _pdb.set_trace(frame)


class PdbDebugger:
    """Namespace for debugging."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(session, task):
        """Execute a task by wrapping the function with post-mortem debugger."""
        if isinstance(task, PythonFunctionTask):
            wrap_function_for_post_mortem_debugging(session, task)
        yield


def wrap_function_for_post_mortem_debugging(session, task):
    """Wrap the function for post-mortem debugging."""

    task_function = task.function

    @functools.wraps(task_function)
    def wrapper(*args, **kwargs):
        capman = session.config["pm"].get_plugin("capturemanager")
        tm_width = session.config["terminal_width"]
        try:
            task_function(*args, **kwargs)

        except Exception as e:
            capman.suspend(in_=True)
            out, err = capman.read()

            if out:
                click.echo(f"{{:-^{tm_width}}}".format(" Captured stdout "))
                click.echo(out)

            if err:
                click.echo(f"{{:-^{tm_width}}}".format(" Captured stderr "))
                click.echo(err)

            exc_info = remove_internal_traceback_frames_from_exc_info(sys.exc_info())

            click.echo(f"{{:>^{tm_width}}}".format(" Traceback "))
            traceback.print_exception(*exc_info)

            post_mortem(exc_info[2])

            capman.resume()

            raise e

    task.function = wrapper


class PdbTrace:
    """Namespace for tracing."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(session, task):
        """Wrapping the task function with a tracer."""
        if isinstance(task, PythonFunctionTask):
            wrap_function_for_tracing(session, task)
        yield


def wrap_function_for_tracing(session, task):
    """Wrap the task function for tracing."""

    _pdb = PytaskPDB._init_pdb("runcall")
    task_function = task.function

    # We can't just return `partial(pdb.runcall, task_function)` because (on python <
    # 3.7.4) runcall's first param is `func`, which means we'd get an exception if one
    # of the kwargs to task_function was called `func`.
    @functools.wraps(task_function)
    def wrapper(*args, **kwargs):
        capman = session.config["pm"].get_plugin("capturemanager")
        tm_width = session.config["terminal_width"]

        capman.suspend(in_=True)
        out, err = capman.read()

        if out:
            click.echo(f"{{:-^{tm_width}}}".format(" Captured stdout "))
            click.echo(out)

        if err:
            click.echo(f"{{:-^{tm_width}}}".format(" Captured stderr "))
            click.echo(err)

        _pdb.runcall(task_function, *args, **kwargs)

        capman.resume()

    task.function = wrapper


def post_mortem(t) -> None:
    p = PytaskPDB._init_pdb("post_mortem")
    p.reset()
    p.interaction(None, t)
    if p.quitting:
        raise Exception("Quitting debugger")
