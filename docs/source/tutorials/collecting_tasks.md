# Collecting tasks

If you want to inspect your project and see a summary of all the tasks, you can use the
[`pytask collect`](../commands/collect.md) command.

Let us take the following task.

```py
--8<-- "docs_src/tutorials/collecting_tasks.py"
```

Now, running [`pytask collect`](../commands/collect.md) will produce the following
output.

--8<-- "docs/source/_static/md/collect.md"

If you want to have more information regarding the dependencies and products of the
task, append the [`pytask collect --nodes`](../commands/collect.md#options) flag.

--8<-- "docs/source/_static/md/collect-nodes.md"

To restrict the set of tasks you are looking at, use markers, expressions and ignore
patterns as usual.

## Further reading

- Read the [command reference for `pytask collect`](../commands/collect.md).
- Read the tutorial on [selecting tasks](selecting_tasks.md).
- Paths can be ignored with [`ignore`](../reference_guides/configuration.md#ignore).
