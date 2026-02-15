# Collecting tasks

If you want to inspect your project and see a summary of all the tasks, you can use the
`pytask collect` command.

Let us take the following task.

```py
--8<-- "docs_src/tutorials/collecting_tasks.py"
```

Now, running `pytask collect` will produce the following output.

--8<-- "docs/source/_static/md/collect.md"

If you want to have more information regarding the dependencies and products of the
task, append the `pytask collect --nodes` flag.

--8<-- "docs/source/_static/md/collect-nodes.md"

To restrict the set of tasks you are looking at, use markers, expressions and ignore
patterns as usual.

## Further reading

- The documentation on the command line interface of `pytask collect` can be found
    [here](../reference_guides/command_line_interface.md).
- Read [here](selecting_tasks.md) about selecting tasks.
- Paths can be ignored with `ignore`.
