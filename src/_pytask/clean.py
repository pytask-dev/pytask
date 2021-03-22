"""Add a command to clean the project from files unknown to pytask."""
import itertools
import shutil
import sys
from pathlib import Path

import attr
import click
from _pytask.config import hookimpl
from _pytask.config import IGNORED_TEMPORARY_FILES_AND_FOLDERS
from _pytask.console import console
from _pytask.enums import ColorCode
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import get_first_non_none_value
from rich.traceback import Traceback


_HELP_TEXT_MODE = (
    "Choose 'dry-run' to print the paths of files/directories which would be removed, "
    "'interactive' for a confirmation prompt for every path, and 'force' to remove all "
    "unknown paths at once.  [default: dry-run]"
)


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group):
    """Extend the command line interface."""
    cli.add_command(clean)


@hookimpl
def pytask_parse_config(config, config_from_cli):
    """Parse the configuration."""
    config["mode"] = get_first_non_none_value(
        config_from_cli, key="mode", default="dry-run"
    )
    config["quiet"] = get_first_non_none_value(
        config_from_cli, key="quiet", default=False
    )
    config["directories"] = get_first_non_none_value(
        config_from_cli, key="directories", default=False
    )


@hookimpl
def pytask_post_parse(config):
    """Correct ignore patterns such that caches, etc. will not be ignored."""
    if config["command"] == "clean":
        config["ignore"] = [
            i for i in config["ignore"] if i not in IGNORED_TEMPORARY_FILES_AND_FOLDERS
        ]


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["dry-run", "interactive", "force"]),
    help=_HELP_TEXT_MODE,
)
@click.option("-d", "--directories", is_flag=True, help="Remove whole directories.")
@click.option(
    "-q", "--quiet", is_flag=True, help="Do not print the names of the removed paths."
)
def clean(**config_from_cli):
    """Clean provided paths by removing files unknown to pytask."""
    config_from_cli["command"] = "clean"

    try:
        # Duplication of the same mechanism in :func:`pytask.main.main`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)
        session = Session.from_config(config)

    except Exception:
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED
        console.print(Traceback.from_exception(*sys.exc_info()))

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)

            known_paths = _collect_all_paths_known_to_pytask(session)
            include_directories = session.config["directories"]
            unknown_paths = _find_all_unknown_paths(
                session, known_paths, include_directories
            )
            common_ancestor = find_common_ancestor(
                *unknown_paths, *session.config["paths"]
            )

            if unknown_paths:
                targets = "Files"
                if session.config["directories"]:
                    targets += " and directories"
                console.print(f"\n{targets} which can be removed:\n")
                for path in unknown_paths:
                    short_path = relative_to(path, common_ancestor)
                    if session.config["mode"] == "dry-run":
                        console.print(f"Would remove {short_path}")
                    else:
                        should_be_deleted = session.config[
                            "mode"
                        ] == "force" or click.confirm(
                            f"Would you like to remove {short_path}?"
                        )
                        if should_be_deleted:
                            if not session.config["quiet"]:
                                console.print(f"Remove {short_path}")
                            if path.is_dir():
                                shutil.rmtree(path)
                            else:
                                path.unlink()
            else:
                console.print()
                console.print(
                    "There are no files and directories which can be deleted."
                )

            console.print()
            console.rule(style=None)

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED
            console.rule(style=ColorCode.FAILED)

        except Exception:
            console.print(Traceback.from_exception(*sys.exc_info()))
            console.rule(style=ColorCode.FAILED)
            session.exit_code = ExitCode.FAILED

    sys.exit(session.exit_code)


def _collect_all_paths_known_to_pytask(session):
    """Collect all paths from the session which are known to pytask.

    Paths belong to tasks and nodes and configuration values.

    """
    known_files = set()
    for task in session.tasks:
        for path in _yield_paths_from_task(task):
            known_files.add(path)

    known_directories = set()
    for path in known_files:
        known_directories.update(path.parents)

    known_paths = known_files | known_directories

    if session.config["config"]:
        known_paths.add(session.config["config"])
    known_paths.add(session.config["root"])
    known_paths.add(session.config["database_filename"])

    return known_paths


def _yield_paths_from_task(task):
    """Yield all paths attached to a task."""
    yield task.path
    for attribute in ["depends_on", "produces"]:
        for node in getattr(task, attribute).values():
            if isinstance(node.value, Path):
                yield node.value


def _find_all_unknown_paths(session, known_paths, include_directories):
    """Find all unknown paths.

    First, create a tree of :class:`_RecursivePathNode`. Then, create a list of unknown
    paths and potentially take short-cuts if complete directories can be deleted.

    """
    recursive_nodes = [
        _RecursivePathNode.from_path(path, known_paths, session)
        for path in session.config["paths"]
    ]
    unknown_paths = list(
        itertools.chain.from_iterable(
            [
                _find_all_unkown_paths_per_recursive_node(node, include_directories)
                for node in recursive_nodes
            ]
        )
    )
    return unknown_paths


def _find_all_unkown_paths_per_recursive_node(node, include_directories):
    """Return unknown paths per recursive file node.

    If ``--directories`` is given, take a short-cut and return only the path of the
    directory and not the path of every single file in it.

    """
    if node.is_unknown and (node.is_file or (node.is_dir and include_directories)):
        yield node.path
    else:
        for n in node.sub_nodes:
            yield from _find_all_unkown_paths_per_recursive_node(n, include_directories)


@attr.s(repr=False)
class _RecursivePathNode:
    """A class for a path to a file or directory which recursively instantiates itself.

    The problem is that we want to take a short-cut for unknown directories with only
    unknown contents and offer to remove the whole directory instead of all included
    files. Then, the directory node must be aware of its child nodes and be able to
    query whether all child nodes are unknown.

    Thus, this class creates subsequent nodes for all subsequent paths if it is a
    directory and stores the nodes of children.

    """

    path = attr.ib(type=Path)
    sub_nodes = attr.ib(type=list)
    is_dir = attr.ib(type=bool)
    is_file = attr.ib(type=bool)
    is_unknown = attr.ib(type=bool)

    @classmethod
    def from_path(cls, path: Path, known_paths: list, session):
        """Create a node from a path.

        While instantiating the class, subordinate nodes are spawned for all paths
        inside a directory.

        """
        sub_nodes = (
            [
                _RecursivePathNode.from_path(p, known_paths, session)
                for p in path.iterdir()
            ]
            if path.is_dir()
            # Do not collect sub files and folders for ignored folders.
            and not session.hook.pytask_ignore_collect(path=path, config=session.config)
            else []
        )

        is_unknown_file = path.is_file() and not (
            path in known_paths
            # Ignored files are also known.
            or session.hook.pytask_ignore_collect(path=path, config=session.config)
        )
        is_unknown_directory = (
            path.is_dir()
            # True for folders and ignored folders without any sub nodes.
            and all(node.is_unknown for node in sub_nodes)
            # True for not ignored paths.
            and not session.hook.pytask_ignore_collect(path=path, config=session.config)
        )
        is_unknown = is_unknown_file or is_unknown_directory

        return cls(path, sub_nodes, path.is_dir(), path.is_file(), is_unknown)

    def __repr__(self):
        return f"<Node at {self.path} is {'unknown' if self.is_unknown else 'known'}>"
