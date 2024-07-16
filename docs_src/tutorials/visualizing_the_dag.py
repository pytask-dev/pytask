from pathlib import Path

import networkx as nx
from my_project.config import BLD
from my_project.config import SRC
from pytask import Product
from pytask import build_dag
from typing_extensions import Annotated


def draw_dag(path: Annotated[Path, Product] = BLD / "dag.svg") -> None:
    dag = build_dag({"paths": SRC})

    # Set shapes to hexagons.
    nx.set_node_attributes(dag, "hexagon", "shape")

    # Export with pygraphviz and dot.
    graph = nx.nx_agraph.to_agraph(dag)
    graph.draw(path, prog="dot")


if __name__ == "__main__":
    draw_dag()
