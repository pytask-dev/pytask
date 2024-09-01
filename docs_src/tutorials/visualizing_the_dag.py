from pathlib import Path

import networkx as nx
from my_project.config import BLD
from my_project.config import SRC

from pytask import build_dag


def draw_dag(path: Path = BLD / "dag.svg") -> None:
    dag = build_dag({"paths": SRC})

    # Set shapes to hexagons.
    nx.set_node_attributes(dag, "hexagon", "shape")

    # Export with pygraphviz and dot.
    graph = nx.nx_agraph.to_agraph(dag)
    graph.draw(path, prog="dot")


if __name__ == "__main__":
    draw_dag()
