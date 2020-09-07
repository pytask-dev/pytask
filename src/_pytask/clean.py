"""Add a command to clean the project from files unknown to pytask."""
import itertools
import shutil
import sys
import traceback
from pathlib import Path

import attr
import click
from _pytask.config import hookimpl
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import falsy_to_none_callback
from _pytask.shared import get_first_not_none_value


HELP_TEXT_MODE = (
    "Choose 'dry-run' to print the paths of files/directories which would be removed, "
    "'interactive' for a confirmation prompt for every path, and 'force' to remove all "
    "unknown paths at once.  [default: dry-run]"
)


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group):
    """Extend the command line interface."""
    cli.add_command(clean)


@hookimpl
def pytask_parse_config(config, config_from_cli):
    """Parse the configuration."""
    config["mode"] = get_first_not_none_value(
        config_from_cli, key="mode", default="dry-run"
    )
    config["quiet"] = get_first_not_none_value(
        config_from_cli, key="quiet", default=False
    )
    config["directories"] = get_first_not_none_value(
        config_from_cli, key="directories", default=False
    )


@click.command()
@click.argument(
    "paths", nargs=-1, type=click.Path(exists=True), callback=falsy_to_none_callback
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["dry-run", "interactive", "force"]),
    help=HELP_TEXT_MODE,
)
@click.option("-d", "--directories", is_flag=True, help="Remove whole directories.")
@click.option(
    "-q", "--quiet", is_flag=True, help="Do not print the names of the removed paths."
)
@click.option(
    "-c", "--config", type=click.Path(exists=True), help="Path to configuration file."
)
def clean(**config_from_cli):
    """Clean provided paths by removing files unknown to pytask."""
    try:
        # Duplication of the same mechanism in :func:`pytask.main.main`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

        session = Session.from_config(config)
        session.exit_code = ExitCode.OK

    except Exception:
        traceback.print_exception(*sys.exc_info())
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)

            known_paths = collect_all_paths_known_to_pytask(session)
            include_directories = session.config["directories"]
            unknown_paths = find_all_unknown_paths(
                session, known_paths, include_directories
            )

            targets = "Files"
            if session.config["directories"]:
                targets += " and directories"
            click.echo(f"\n{targets} which can be removed:\n")
            for path in unknown_paths:
                if session.config["mode"] == "dry-run":
                    click.echo(f"Would remove {path}.")
                else:
                    should_be_deleted = session.config[
                        "mode"
                    ] == "force" or click.confirm(f"Would you like to remove {path}?")
                    if should_be_deleted:
                        if not session.config["quiet"]:
                            click.echo(f"Remove {path}.")
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()

            click.echo("")

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except Exception:
            traceback.print_exception(*sys.exc_info())
            session.exit_code = ExitCode.FAILED

    return session


def collect_all_paths_known_to_pytask(session):
    """Collect all paths from the session which are known to pytask.

    Paths belong to tasks and nodes and configuration values.

    """
    known_files = set()
    for task in session.tasks:
        for path in yield_paths_from_task(task):
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


def yield_paths_from_task(task):
    """Yield all paths attached to a task."""
    yield task.path
    for attribute in ["depends_on", "produces"]:
        for node in getattr(task, attribute):
            if isinstance(node.value, Path):
                yield node.value


def find_all_unknown_paths(session, known_paths, include_directories):
    """Find all unknown paths.

    First, create a tree of :class:`RecursivePathNode`. Then, create a list of unknown
    paths and potentially take short-cuts if complete directories can be deleted.

    """
    recursive_nodes = [
        RecursivePathNode.from_path(path, known_paths)
        for path in session.config["paths"]
    ]
    unknown_paths = list(
        itertools.chain.from_iterable(
            [
                find_all_unkown_paths_per_recursive_node(node, include_directories)
                for node in recursive_nodes
            ]
        )
    )
    return unknown_paths


def find_all_unkown_paths_per_recursive_node(node, include_directories):
    """Return unknown paths per recursive file node.

    If ``"--directories"`` is given, take a short-cut and return only the path of the
    directory and not the path of every single file in it.

    """
    if node.is_unknown and (node.is_file or (node.is_dir and include_directories)):
        yield node.path
    else:
        for n in node.sub_nodes:
            yield from find_all_unkown_paths_per_recursive_node(n, include_directories)


@attr.s(repr=False)
class RecursivePathNode:
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
    def from_path(cls, path: Path, known_paths: list):
        """Create a node from a path.

        While instantiating the class, subordinate nodes are spawned for all paths
        inside a directory.

        """
        sub_nodes = (
            [RecursivePathNode.from_path(p, known_paths) for p in path.glob("*")]
            if path.is_dir()
            else []
        )
        is_unknown = (path.is_file() and path not in known_paths) or (
            path.is_dir() and all(node.is_unknown for node in sub_nodes)
        )
        return cls(path, sub_nodes, path.is_dir(), path.is_file(), is_unknown)

    def __repr__(self):
        return f"<Node at {self.path} is {'unknown' if self.is_unknown else 'known'}>"
