# Collecting tasks

If you want to inspect your project and see a summary of all the tasks, you can use the
`pytask collect` command.

Let us take the following task.

```python
# Content of task_module.py

import pytask


@pytask.mark.depends_on("in.txt")
@pytask.mark.produces("out.txt")
def task_write_file(depends_on, produces):
    produces.write_text(depends_on.read_text())
```

Now, running `pytask collect` will produce the following output.

```{image} /_static/images/collect.svg
```

If you want to have more information regarding the dependencies and products of the
task, append the {option}`pytask collect --nodes` flag.

```{image} /_static/images/collect-nodes.svg
```

To restrict the set of tasks you are looking at, use markers, expressions and ignore
patterns as usual.

## Further reading

- The documentation on the command line interface of `pytask collect` can be found
  {doc}`here <../reference_guides/command_line_interface>`.
- Read {doc}`here <selecting_tasks>` about selecting tasks.
- Paths can be ignored with {confval}`ignore`.
