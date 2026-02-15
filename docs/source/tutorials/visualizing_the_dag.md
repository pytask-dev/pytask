# Visualizing the DAG

To visualize the `DAG` of the project, first, install
[pygraphviz](https://github.com/pygraphviz/pygraphviz) and
[graphviz](https://graphviz.org/). For example, you can both install with pixi

```console
$ pixi add pygraphviz graphviz
```

After that, pytask offers two interfaces to visualize your project's `DAG`.

## Command-line interface

You can quickly create a visualization with this command.

```console
$ pytask dag
```

It generates a `dag.pdf` in the current working directory.

If you do not want to generate a PDF, use `pytask dag --output-path` or, shorter,
`pytask dag -o` to choose a different format inferred from the file-ending. Select any
format supported by [graphviz](https://graphviz.org/docs/outputs/).

```console
$ pytask dag -o dag.png
```

You can change the graph's layout by using the `pytask dag --layout` option. Its default
is set to `dot` and produces a hierarchical structure. graphviz supports other layouts,
which are listed [here](https://graphviz.org/docs/layouts/).

## Programmatic Interface

The programmatic and interactive interface allows for customizing the figure.

Similar to `pytask.build`, there exists `pytask.build_dag` which returns the DAG as a
`networkx.DiGraph`.

Create an executable script that you can execute with `python script.py`.

```python
--8 < --"docs_src/tutorials/visualizing_the_dag.py"
```

Customization works best on the `networkx.DiGraph`. For example, here, we set the shape
of all nodes to hexagons by adding the property to the node attributes.

For drawing, you better switch to pygraphviz since the matplotlib backend handles shapes
with texts poorly. Here we store the graph as a `.svg`.
