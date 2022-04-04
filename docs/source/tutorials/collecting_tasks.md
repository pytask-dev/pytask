# Collecting tasks

If you want to inspect your project and see a summary of all the tasks in the projects,
you can use the {program}`pytask collect` command.

For example, let us take the following task

```python
# Content of task_module.py

import pytask


@pytask.mark.depends_on("in.txt")
@pytask.mark.produces("out.txt")
def task_write_file(depends_on, produces):
    produces.write_text(depends_on.read_text())
```

Now, running {program}`pytask collect` will produce the following output.

```{image} /_static/images/collect.svg
```

If you want to have more information regarding dependencies and products of the task,
append the `--nodes` flag.

```{image} /_static/images/collect-nodes.svg
```

To restrict the set of tasks you are looking at, use markers, expression and ignore
patterns as usual.

## Further reading

- The documentation on the command line interface of {program}`pytask collect` can be
  found {doc}`here <../reference_guides/command_line_interface>`.
- Read {doc}`here <selecting_tasks>` about selecting tasks.
- Paths can be ignored with {confval}`ignore`.
