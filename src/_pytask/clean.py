"""Add a command to clean the project from files unknown to pytask."""
from __future__ import annotations

import itertools
import shutil
import sys
from pathlib import Path
from types import TracebackType
from typing import Any
from typing import Generator
from typing import Iterable
from typing import List
from typing import TYPE_CHECKING

import attr
import click
from _pytask.click import ColoredCommand
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.exceptions import CollectionError
from _pytask.git import get_all_files
from _pytask.git import get_root
from _pytask.git import is_git_installed
from _pytask.nodes import Task
from _pytask.outcomes import ExitCode
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import falsy_to_none_callback
from _pytask.shared import get_first_non_none_value
from _pytask.shared import parse_value_or_multiline_option
from _pytask.shared import to_list
from _pytask.traceback import render_exc_info
from pybaum.tree_util import tree_just_yield


if TYPE_CHECKING:
    from typing import NoReturn


_DEFAULT_EXCLUDE: list[str] = [".git/*", ".hg/*", ".svn/*"]


_HELP_TEXT_MODE = (
    "Choose 'dry-run' to print the paths of files/directories which would be removed, "
    "'interactive' for a confirmation prompt for every path, and 'force' to remove all "
    "unknown paths at once. [dim]\\[default: dry-run][/]"
)


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(clean)


@hookimpl
def pytask_parse_config(
    config: dict[str, Any],
    config_from_cli: dict[str, Any],
    config_from_file: dict[str, Any],
) -> None:
    """Parse the configuration."""
    config["directories"] = config_from_cli.get("directories", False)
    cli_excludes = parse_value_or_multiline_option(config_from_cli.get("exclude"))
    file_excludes = parse_value_or_multiline_option(config_from_file.get("exclude"))
    config["exclude"] = (
        to_list(cli_excludes or []) + to_list(file_excludes or []) + _DEFAULT_EXCLUDE
    )
    config["mode"] = config_from_cli.get("mode", "dry-run")
    config["quiet"] = get_first_non_none_value(
        config_from_cli, key="quiet", default=False
    )


@click.command(cls=ColoredCommand)
@click.option(
    "-d",
    "--directories",
    is_flag=True,
    help="Remove whole directories. [dim]\\[default: False][/]",
)
@click.option(
    "-e",
    "--exclude",
    metavar="PATTERN",
    multiple=True,
    type=str,
    help="A filename pattern to exclude files from the cleaning process.",
    callback=falsy_to_none_callback,
)
@click.option(
    "--mode",
    default="dry-run",
    type=click.Choice(["dry-run", "interactive", "force"]),
    help=_HELP_TEXT_MODE,
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Do not print the names of the removed paths. [dim]\\[default: quiet][/]",
)
def clean(**config_from_cli: Any) -> NoReturn:
    """Clean the provided paths by removing files unknown to pytask."""
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
        exc_info: tuple[
            type[BaseException], BaseException, TracebackType | None
        ] = sys.exc_info()
        console.print(render_exc_info(*exc_info))

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)

            known_paths = _collect_all_paths_known_to_pytask(session)
            exclude = session.config["exclude"]
            include_directories = session.config["directories"]
            unknown_paths = _find_all_unknown_paths(
                session, known_paths, exclude, include_directories
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
            console.rule(style="failed")

        except Exception:
            exc_info = sys.exc_info()
            console.print(render_exc_info(*exc_info, show_locals=config["show_locals"]))
            console.rule(style="failed")
            session.exit_code = ExitCode.FAILED

    sys.exit(session.exit_code)


def _collect_all_paths_known_to_pytask(session: Session) -> set[Path]:
    """Collect all paths from the session which are known to pytask.

    Paths belong to tasks and nodes and configuration values.

    """
    known_files = set()
    for task in session.tasks:
        for path in _yield_paths_from_task(task):
            known_files.add(path)

    known_directories: set[Path] = set()
    for path in known_files:
        known_directories.update(path.parents)

    known_paths = known_files | known_directories

    if session.config["config"]:
        known_paths.add(session.config["config"])
    known_paths.add(session.config["root"])
    known_paths.add(session.config["database_filename"])

    # Add files tracked by git.
    if is_git_installed():
        git_root = get_root(session.config["root"])
        if git_root is not None:
            paths_known_by_git = get_all_files(session.config["root"])
            absolute_paths_known_by_git = [
                git_root.joinpath(p) for p in paths_known_by_git
            ]
            known_paths.update(absolute_paths_known_by_git)
            known_paths.add(git_root / ".git")

    return known_paths


def _yield_paths_from_task(task: Task) -> Generator[Path, None, None]:
    """Yield all paths attached to a task."""
    yield task.path
    for attribute in ["depends_on", "produces"]:
        for node in tree_just_yield(getattr(task, attribute)):
            if hasattr(node, "path") and isinstance(node.path, Path):
                yield node.path


def _find_all_unknown_paths(
    session: Session,
    known_paths: set[Path],
    exclude: tuple[str, ...],
    include_directories: bool,
) -> list[Path]:
    """Find all unknown paths.

    First, create a tree of :class:`_RecursivePathNode`. Then, create a list of unknown
    paths and potentially take short-cuts if complete directories can be deleted.

    """
    recursive_nodes = [
        _RecursivePathNode.from_path(path, known_paths, exclude)
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
    sub_nodes = attr.ib(type=List["_RecursivePathNode"])
    is_dir = attr.ib(type=bool)
    is_file = attr.ib(type=bool)
    is_unknown = attr.ib(type=bool)

    @classmethod
    def from_path(
        cls, path: Path, known_paths: Iterable[Path], exclude: tuple[str, ...]
    ) -> _RecursivePathNode:
        """Create a node from a path.

        While instantiating the class, subordinate nodes are spawned for all paths
        inside a directory.

        """
        # Spawn subnodes for a directory, but only if the directory is not excluded.
        sub_nodes = (
            [
                _RecursivePathNode.from_path(p, known_paths, exclude)
                for p in path.iterdir()
            ]
            if path.is_dir()
            # Do not collect sub files and folders for excluded folders.
            and not any(path.match(pattern) for pattern in exclude)
            else []
        )

        is_unknown_file = path.is_file() and not (
            path in known_paths
            # Excluded files are also known.
            or any(path.match(pattern) for pattern in exclude)
        )
        is_unknown_directory = (
            path.is_dir()
            # True for folders and ignored folders without any sub nodes.
            and all(node.is_unknown for node in sub_nodes)
            # True for not ignored paths.
            and not any(path.match(pattern) for pattern in exclude)
        )
        is_unknown = is_unknown_file or is_unknown_directory

        return cls(path, sub_nodes, path.is_dir(), path.is_file(), is_unknown)

    def __repr__(self) -> str:
        return f"<Node at {self.path} is {'unknown' if self.is_unknown else 'known'}>"


def _find_all_unkown_paths_per_recursive_node(
    node: _RecursivePathNode, include_directories: bool
) -> Generator[Path, None, None]:
    """Return unknown paths per recursive file node.

    If ``--directories`` is given, take a short-cut and return only the path of the
    directory and not the path of every single file in it.

    """
    if node.is_unknown and (node.is_file or (node.is_dir and include_directories)):
        yield node.path
    else:
        for n in node.sub_nodes:
            yield from _find_all_unkown_paths_per_recursive_node(n, include_directories)
