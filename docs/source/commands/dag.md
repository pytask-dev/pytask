# dag

Create a visualization of the directed acyclic graph.

## Usage

```bash
pytask dag [OPTIONS] [PATHS]
```

## Examples

```bash
# Create a DAG as PDF.
pytask dag

# Create a PNG instead.
pytask dag -o dag.png

# Change the graph layout and direction.
pytask dag --layout dot --rank-direction LR
```

## Arguments

--8<-- "docs/source/_static/md/commands/dag-arguments.md"

## Options

--8<-- "docs/source/_static/md/commands/dag-options.md"

## Related

- [Visualizing the DAG](../tutorials/visualizing_the_dag.md)
