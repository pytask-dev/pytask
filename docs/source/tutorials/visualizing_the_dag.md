# Visualizing the DAG

To visualize the {term}`DAG` of the project, first, install
[pydot](https://github.com/pydot/pydot) and [graphviz](https://graphviz.org/). For
example, you can both install with conda

```console
$ conda install -c conda-forge pydot
```

After that, pytask offers two interfaces to visualize the {term}`DAG` of your project.

## Command line interface

You can quickly create a visualization from the command line by entering

```console
$ pytask dag
```

at the top of your project which will generate a `dag.pdf`.

There are ways to customize the visualization.

1. You can change the layout of the graph by using the {option}`pytask dag --layout`
   option. By default, it is set to `dot` and produces a hierarchical layout. graphviz
   supports other layouts as well which are listed
   [here](https://graphviz.org/#roadmap).
1. Using the {option}`pytask dag --output-path` option, you can provide a file name for
   the graph. The file extension changes the output format if it is supported by
   [pydot](https://github.com/pydot/pydot).

## Programmatic Interface

Since the possibilities for customization are limited via the command line interface,
there also exists a programmatic and interactive interface.

Similar to {func}`pytask.main`, there exists {func}`pytask.build_dag` which returns the
DAG as a {class}`networkx.DiGraph`.

```python
@pytask.mark.produces(BLD / "dag.svg")
def task_draw_dag(produces):
    dag = pytask.build_dag({"paths": SRC})
```

Customization works best on the {class}`networkx.DiGraph`. For example, here we set the
shape of all nodes to hexagons by adding the property to the node attributes.

```python
nx.set_node_attributes(dag, "hexagon", "shape")
```

For drawing, you better switch to pydot or pygraphviz since the matplotlib backend
handles shapes with texts poorly. Here we use pydot and store the graph as an `.svg`.

```python
graph = nx.nx_pydot.to_pydot(dag)
graph.write_svg(produces)
```
