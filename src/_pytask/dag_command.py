"""Contains the command and code for drawing the DAG."""

from __future__ import annotations

import enum
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Iterable

import click
import networkx as nx
import typed_settings as ts
from rich.text import Text

from _pytask.compat import check_for_optional_program
from _pytask.compat import import_optional_dependency
from _pytask.console import console
from _pytask.dag import create_dag
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.outcomes import ExitCode
from _pytask.pluginmanager import get_plugin_manager
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import storage
from _pytask.session import Session
from _pytask.settings_utils import SettingsBuilder
from _pytask.settings_utils import create_settings_loaders
from _pytask.settings_utils import update_settings
from _pytask.shared import reduce_names_of_multiple_nodes
from _pytask.traceback import Traceback

if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from _pytask.settings import Settings


class _RankDirection(enum.Enum):
    TB = "TB"
    LR = "LR"
    BT = "BT"
    RL = "RL"


@ts.settings
class Dag:
    layout: str = ts.option(
        default="dot",
        help="The layout determines the structure of the graph. Here you find an "
        "overview of all available layouts: https://graphviz.org/docs/layouts.",
    )
    output_path: Path = ts.option(
        click={
            "type": click.Path(file_okay=True, dir_okay=False, path_type=Path),
            "param_decls": ["-o", "--output-path"],
        },
        default=Path("dag.pdf"),
        help="The output path of the visualization. The format is inferred from the "
        "file extension.",
    )
    rank_direction: _RankDirection = ts.option(
        default=_RankDirection.TB,
        help="The direction of the directed graph. It can be ordered from top to "
        "bottom, TB, left to right, LR, bottom to top, BT, or right to left, RL.",
        click={"param_decls": ["-r", "--rank-direction"]},
    )


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(settings_builder: SettingsBuilder) -> None:
    """Extend the command line interface."""
    settings_builder.commands["dag"] = dag


def dag(**raw_config: Any) -> int:
    """Create a visualization of the project's directed acyclic graph."""
    try:
        pm = storage.get()
        config = pm.hook.pytask_configure(pm=pm, raw_config=raw_config)
        session = Session(config=config, hook=config.common.pm.hook)

    except (ConfigurationError, Exception):  # pragma: no cover
        console.print_exception()
        session = Session(exit_code=ExitCode.CONFIGURATION_FAILED)

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            import_optional_dependency("pygraphviz")
            check_for_optional_program(
                session.config.dag.layout,
                extra="The layout program is part of the graphviz package which you "
                "can install with conda.",
            )
            session.hook.pytask_collect(session=session)
            session.dag = create_dag(session=session)
            dag = _refine_dag(session)
            _write_graph(dag, session.config.dag.output_path, session.config.dag.layout)

        except CollectionError:  # pragma: no cover
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:  # pragma: no cover
            session.exit_code = ExitCode.DAG_FAILED

        except Exception:  # noqa: BLE001
            session.exit_code = ExitCode.FAILED
            console.print()
            console.print(Traceback(sys.exc_info()))
            console.rule(style="failed")

    session.hook.pytask_unconfigure(session=session)
    sys.exit(session.exit_code)


def build_dag(
    paths: Path | tuple[Path, ...] = (),
    tasks: Callable[..., Any] | PTask | Iterable[Callable[..., Any] | PTask] = (),
    task_files: Iterable[str] = ("task_*.py",),
    settings: Settings | None = None,
    **kwargs: Any,
) -> nx.DiGraph:
    """Build the DAG.

    This function is the programmatic interface to ``pytask dag`` and returns a
    preprocessed :class:`pygraphviz.AGraph` which makes plotting easier than with
    matplotlib.

    To change the style of the graph, it might be easier to convert the graph back to
    networkx, set attributes, and convert back to pygraphviz.

    Returns
    -------
    pygraphviz.AGraph
        A preprocessed graph which can be customized and exported.

    """
    try:
        updates = {
            "paths": paths,
            "tasks": tasks,
            "task_files": task_files,
            **kwargs,
        }

        if settings is None:
            from _pytask.cli import settings_builders

            pm = get_plugin_manager()
            storage.store(pm)

            settings = ts.load_settings(
                settings_builders["dag"].build_settings(), create_settings_loaders()
            )
        else:
            pm = storage.get()

        settings = update_settings(settings, updates)
        config_ = pm.hook.pytask_configure(pm=pm, config=settings)
        session = Session.from_config(config_)

    except (ConfigurationError, Exception):  # pragma: no cover
        console.print_exception()
        session = Session(exit_code=ExitCode.CONFIGURATION_FAILED)

    else:
        session.hook.pytask_log_session_header(session=session)
        import_optional_dependency("pygraphviz")
        check_for_optional_program(
            session.config.dag.layout,
            extra="The layout program is part of the graphviz package that you "
            "can install with conda.",
        )
        session.hook.pytask_collect(session=session)
        session.dag = create_dag(session=session)
        session.hook.pytask_unconfigure(session=session)
        return _refine_dag(session)


def _refine_dag(session: Session) -> nx.DiGraph:
    """Refine the dag for plotting."""
    dag = _shorten_node_labels(session.dag, session.config.common.paths)
    dag = _clean_dag(dag)
    dag = _style_dag(dag)
    dag.graph["graph"] = {"rankdir": session.config.dag.rank_direction.name}

    return dag


def _shorten_node_labels(dag: nx.DiGraph, paths: tuple[Path, ...]) -> nx.DiGraph:
    """Shorten the node labels in the graph for a better experience."""
    node_names = dag.nodes
    short_names = reduce_names_of_multiple_nodes(node_names, dag, paths)
    short_names = [i.plain if isinstance(i, Text) else i for i in short_names]  # type: ignore[attr-defined]
    old_to_new = dict(zip(node_names, short_names))
    return nx.relabel_nodes(dag, old_to_new)


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


def _write_graph(dag: nx.DiGraph, path: Path, layout: str) -> None:
    """Write the graph to disk."""
    path.parent.mkdir(exist_ok=True, parents=True)
    graph = nx.nx_agraph.to_agraph(dag)
    graph.draw(path, prog=layout)
    console.print()
    console.print(f"Written to {path}.")
