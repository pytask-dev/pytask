"""This file contains the command and code for drawing the DAG."""
import shutil
from pathlib import Path
from typing import Any
from typing import Dict

import click
import networkx as nx
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.dag import descending_tasks
from _pytask.enums import ColorCode
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.nodes import reduce_names_of_multiple_nodes
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import get_first_non_none_value


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group):
    """Extend the command line interface."""
    cli.add_command(dag)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
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


_HELP_TEXT_LAYOUT = (
    "The layout determines the structure of the graph. Here you find an overview of "
    "all available layouts: https://graphviz.org/#roadmap."
)


_HELP_TEXT_OUTPUT = (
    "The output path of the visualization. The format is inferred from the file "
    "extension."
)


@click.command()
@click.option("-l", "--layout", type=str, default=None, help=_HELP_TEXT_LAYOUT)
@click.option("-o", "--output-path", type=str, default=None, help=_HELP_TEXT_OUTPUT)
def dag(**config_from_cli):
    """Create a visualization of the project's DAG."""
    session = _create_session(config_from_cli)
    dag = _refine_dag(session)
    _write_graph(dag, session.config["output_path"], session.config["layout"])


def build_dag(config_from_cli: Dict[str, Any]) -> "pydot.Dot":  # noqa: F821
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
    session = _create_session(config_from_cli)
    dag = _refine_dag(session)
    return dag


def _refine_dag(session):
    dag = _shorten_node_labels(session.dag, session.config["paths"])
    dag = _add_root_node(dag)
    dag = _clean_dag(dag)
    dag = _style_dag(dag)
    dag = _escape_node_names_with_colons(dag)

    return dag


def _create_session(config_from_cli: Dict[str, Any]) -> nx.DiGraph:
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
            session.hook.pytask_collect(session=session)
            session.hook.pytask_resolve_dependencies(session=session)

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:
            session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style=ColorCode.FAILED)

    return session


def _shorten_node_labels(dag, paths):
    node_names = dag.nodes
    short_names = reduce_names_of_multiple_nodes(node_names, dag, paths)
    old_to_new = dict(zip(node_names, short_names))
    dag = nx.relabel_nodes(dag, old_to_new)
    return dag


def _add_root_node(dag):
    tasks_without_predecessor = [
        name
        for name in dag.nodes
        if len(list(descending_tasks(name, dag))) == 0 and "task" in dag.nodes[name]
    ]
    if tasks_without_predecessor:
        dag.add_node("root")
        for name in tasks_without_predecessor:
            dag.add_edge("root", name)

    return dag


def _clean_dag(dag):
    """Clean the DAG."""
    for node in dag.nodes:
        dag.nodes[node].clear()
    return dag


def _style_dag(dag: nx.DiGraph) -> nx.DiGraph:
    shapes = {name: "hexagon" if "::task_" in name else "box" for name in dag.nodes}
    nx.set_node_attributes(dag, shapes, "shape")
    return dag


def _escape_node_names_with_colons(dag: nx.DiGraph):
    """Escape node names with colons.

    pydot cannot handle colons in node names since it messes up some syntax. Escaping
    works by wrapping the string in double quotes. See this issue for more information:
    https://github.com/pydot/pydot/issues/224.

    """
    return nx.relabel_nodes(dag, {name: f'"{name}"' for name in dag.nodes})


def _write_graph(dag: nx.DiGraph, path: Path, layout: str) -> None:
    try:
        import pydot  # noqa: F401
    except ImportError:
        raise ImportError(
            "To visualize the project's DAG you need to install pydot which is "
            "available with pip and conda. For example, use 'conda install -c "
            "conda-forge pydot'."
        ) from None
    if shutil.which(layout) is None:
        raise RuntimeError(
            f"The layout program '{layout}' could not be found on your PATH. Please, "
            "install graphviz. For example, use 'conda install -c conda-forge "
            "graphivz'."
        )

    path.parent.mkdir(exist_ok=True, parents=True)
    graph = nx.nx_pydot.to_pydot(dag)
    graph.write(path, prog=layout, format=path.suffix[1:])
