# Visualizing the DAG

To visualize the {term}`DAG` of the project, first, install
[pydot](https://github.com/pydot/pydot) and [graphviz](https://graphviz.org/). For
example, you can both install with conda

```console
$ conda install -c conda-forge pydot
```

After that, pytask offers two interfaces to visualize your project's {term}`DAG`.

## Command-line interface

You can quickly create a visualization with this command.

```console
$ pytask dag
```

It generates a `dag.pdf` in the current working directory.

There are ways to customize the visualization.

1. You can change the graph's layout by using the {option}`pytask dag --layout` option.
   Its default is set to `dot` and produces a hierarchical structure. graphviz supports
   other layouts, which are listed [here](https://graphviz.org/docs/layouts/).
1. Using the {option}`pytask dag --output-path` option, you can provide a file name for
   the graph. The file extension changes the output format as supported by
   [pydot](https://github.com/pydot/pydot).

## Programmatic Interface

The programmatic and interactive interface allows customizing the figure.

Similar to {func}`pytask.main`, there exists {func}`pytask.build_dag` which returns the
DAG as a {class}`networkx.DiGraph`.

```python
@pytask.mark.produces(BLD / "dag.svg")
def task_draw_dag(produces):
    dag = pytask.build_dag({"paths": SRC})
```

Customization works best on the {class}`networkx.DiGraph`. For example, here, we set the
shape of all nodes to hexagons by adding the property to the node attributes.

```python
nx.set_node_attributes(dag, "hexagon", "shape")
```

For drawing, you better switch to pydot or pygraphviz since the matplotlib backend
handles shapes with texts poorly. Here we use pydot and store the graph as a `.svg`.

```python
graph = nx.nx_pydot.to_pydot(dag)
graph.write_svg(produces)
```
