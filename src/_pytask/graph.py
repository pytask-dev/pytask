"""This file contains the command and code for drawing the DAG."""
import sys
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

import click
import networkx as nx
from _pytask.compat import check_for_optional_program
from _pytask.compat import import_optional_dependency
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.outcomes import ExitCode
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import get_first_non_none_value
from _pytask.shared import reduce_names_of_multiple_nodes
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from rich.text import Text
from rich.traceback import Traceback


if TYPE_CHECKING:
    from typing import NoReturn

    if sys.version_info >= (3, 8):
        from typing import Literal
    else:
        from typing_extensions import Literal

    _RankDirection = Literal["TB", "LR", "BT", "RL"]


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(dag)


@hookimpl
def pytask_parse_config(
    config: Dict[str, Any],
    config_from_cli: Dict[str, Any],
    config_from_file: Dict[str, Any],
) -> None:
    """Parse configuration."""
    config["output_path"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="output_path",
        default=Path.cwd() / "dag.pdf",
        callback=lambda x: None if x is None else Path(x),
    )
    config["layout"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="layout",
        default="dot",
    )
    config["rank_direction"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="rank_direction",
        default="TB",
        callback=_rank_direction_callback,
    )


def _rank_direction_callback(
    x: Optional["_RankDirection"],
) -> Optional["_RankDirection"]:
    """Validate the passed options for rank direction."""
    if x in [None, "None", "none"]:
        x = None
    elif x in ["TB", "LR", "BT", "RL"]:
        pass
    else:
        raise ValueError(
            "'rank_direction' can only be one of ['TB', 'LR', 'BT', 'RL']."
        )
    return x


_HELP_TEXT_LAYOUT: str = (
    "The layout determines the structure of the graph. Here you find an overview of "
    "all available layouts: https://graphviz.org/docs/layouts."
)


_HELP_TEXT_OUTPUT: str = (
    "The output path of the visualization. The format is inferred from the file "
    "extension."
)


_HELP_TEXT_RANK_DIRECTION: str = (
    "The direction of the directed graph. It can be ordered from top to bottom, TB, "
    "left to right, LR, bottom to top, BT, or right to left, RL.  [default: TB]"
)


@click.command()
@click.option("-l", "--layout", type=str, default=None, help=_HELP_TEXT_LAYOUT)
@click.option("-o", "--output-path", type=str, default=None, help=_HELP_TEXT_OUTPUT)
@click.option(
    "--rank-direction",
    type=click.Choice(["TB", "LR", "BT", "RL"]),
    help=_HELP_TEXT_RANK_DIRECTION,
)
def dag(**config_from_cli: Any) -> "NoReturn":
    """Create a visualization of the project's DAG."""
    try:
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        console.print_exception()
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            import_optional_dependency("pydot")
            check_for_optional_program(
                session.config["layout"],
                extra="The layout program is part of the graphviz package which you "
                "can install with conda.",
            )
            session.hook.pytask_collect(session=session)
            session.hook.pytask_resolve_dependencies(session=session)
            dag = _refine_dag(session)
            _write_graph(dag, session.config["output_path"], session.config["layout"])

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:
            session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            exc_info = remove_internal_traceback_frames_from_exc_info(sys.exc_info())
            console.print()
            console.print(Traceback.from_exception(*exc_info))
            console.rule(style="failed")

    sys.exit(session.exit_code)


def build_dag(config_from_cli: Dict[str, Any]) -> nx.DiGraph:
    """Build the DAG.

    This function is the programmatic interface to ``pytask dag`` and returns a
    preprocessed :class:`pydot.Dot` which makes plotting easier than with matplotlib.

    To change the style of the graph, it might be easier to convert the graph back to
    networkx, set attributes, and convert back to pydot or pygraphviz.

    Parameters
    ----------
    config_from_cli : Dict[str, Any]
        The configuration usually received from the CLI. For example, use ``{"paths":
        "example-directory/"}`` to collect tasks from a directory.

    Returns
    -------
    pydot.Dot
        A preprocessed graph which can be customized and exported.

    """
    try:
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        console.print_exception()
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            import_optional_dependency("pydot")
            check_for_optional_program(
                session.config["layout"],
                extra="The layout program is part of the graphviz package which you "
                "can install with conda.",
            )
            session.hook.pytask_collect(session=session)
            session.hook.pytask_resolve_dependencies(session=session)
            dag = _refine_dag(session)

        except Exception:
            raise

        else:
            return dag


def _refine_dag(session: Session) -> nx.DiGraph:
    """Refine the dag for plotting."""
    dag = _shorten_node_labels(session.dag, session.config["paths"])
    dag = _clean_dag(dag)
    dag = _style_dag(dag)
    dag = _escape_node_names_with_colons(dag)
    dag.graph["graph"] = {"rankdir": session.config["rank_direction"]}

    return dag


def _create_session(config_from_cli: Dict[str, Any]) -> nx.DiGraph:
    """Create a session object."""
    try:
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        console.print_exception()
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            import_optional_dependency("pydot")
            check_for_optional_program(session.config["layout"])
            session.hook.pytask_collect(session=session)
            session.hook.pytask_resolve_dependencies(session=session)

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:
            session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style="failed")

    return session


def _shorten_node_labels(dag: nx.DiGraph, paths: List[Path]) -> nx.DiGraph:
    """Shorten the node labels in the graph for a better experience."""
    node_names = dag.nodes
    short_names = reduce_names_of_multiple_nodes(node_names, dag, paths)
    short_names = [i.plain if isinstance(i, Text) else i for i in short_names]
    old_to_new = dict(zip(node_names, short_names))
    dag = nx.relabel_nodes(dag, old_to_new)
    return dag


def _clean_dag(dag: nx.DiGraph) -> nx.DiGraph:
    """Clean the DAG."""
    for node in dag.nodes:
        dag.nodes[node].clear()
    return dag


def _style_dag(dag: nx.DiGraph) -> nx.DiGraph:
    """Style the DAG."""
    shapes = {name: "hexagon" if "::task_" in name else "box" for name in dag.nodes}
    nx.set_node_attributes(dag, shapes, "shape")
    return dag


def _escape_node_names_with_colons(dag: nx.DiGraph) -> nx.DiGraph:
    """Escape node names with colons.

    pydot cannot handle colons in node names since it messes up some syntax. Escaping
    works by wrapping the string in double quotes. See this issue for more information:
    https://github.com/pydot/pydot/issues/224.

    """
    return nx.relabel_nodes(dag, {name: f'"{name}"' for name in dag.nodes})


def _write_graph(dag: nx.DiGraph, path: Path, layout: str) -> None:
    """Write the graph to disk."""
    path.parent.mkdir(exist_ok=True, parents=True)
    graph = nx.nx_pydot.to_pydot(dag)
    graph.write(path, prog=layout, format=path.suffix[1:])
