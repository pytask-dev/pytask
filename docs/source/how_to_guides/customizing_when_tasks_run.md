# Customizing when tasks run

By default, pytask decides whether a task should run by comparing the current state of
the task, its dependencies, and its products with the recorded state from a previous
run.

Sometimes this default is not precise enough. You may want to treat one kind of change
as relevant and another one as irrelevant.

For these cases, a task can define `run_on`.

## When is this useful?

Typical situations are:

- A task should rerun when dependencies change, but not when only the task file changed.
- A task should ignore changes to selected products for the purpose of deciding whether
    to rerun.
- A task should use a project-specific rule to decide whether the current state still
    requires execution.

## Use declarative run conditions

For many cases, it is enough to describe which changes should trigger execution.

The default is `None`, which means that pytask uses its default behavior. At the moment,
this means considering all three change kinds: `task_change`, `dependency_change`, and
`product_change`.

```python
from pathlib import Path

import pytask


@pytask.task(
    kwargs={"depends_on": Path("input.txt"), "produces": Path("output.txt")},
    run_on=("dependency_change",),
)
def task_copy(depends_on: Path, produces: Path) -> None:
    produces.write_text(depends_on.read_text())
```

In this example, pytask reruns the task when dependencies change, but not when only the
task itself or its products changed.

Supported values are:

- `None`, which means pytask's default behavior
- `all`, which is shorthand for `task_change`, `dependency_change`, and `product_change`
- `True`, which means always execute the task
- `task_change`
- `dependency_change`
- `product_change`

The change kinds can be passed as a single value or as an iterable.

Time-based values can also express expiration-like rules.

- `"7d"`
- `timedelta(days=7)`

Other time-based interfaces could be added later. Cron expressions and RRULEs are both
candidate interfaces, but this part of the design is still open.

This also makes combinations possible such as:

- `run_on=("all", "7d")`

For example, `True` can be used as a shorthand for always running a task.

```python
from pathlib import Path

import pytask


@pytask.task(
    kwargs={"depends_on": Path("input.txt"), "produces": Path("output.txt")},
    run_on=True,
)
def task_copy(depends_on: Path, produces: Path) -> None:
    produces.write_text(depends_on.read_text())
```

## Use a callable for advanced rules

If declarative values are not enough, `run_on` can also be a callable.

```python
from pathlib import Path

import pytask


def run_on(task): ...


@pytask.task(
    kwargs={"depends_on": Path("input.txt"), "produces": Path("output.txt")},
    run_on=run_on,
)
def task_copy(depends_on: Path, produces: Path) -> None:
    produces.write_text(depends_on.read_text())
```

The callable receives the current task as its first positional argument.

A public helper can be used to read recorded state from the lockfile:

- `pytask.get_recorded_state(task)` for the task itself
- `pytask.get_recorded_state(task, node)` for a dependency or product node

For example:

```python
from optree import tree_leaves

import pytask


def run_on(task) -> bool:
    for node in tree_leaves(task.depends_on):
        if node.state() != pytask.get_recorded_state(task, node):
            return True
    return task.state() != pytask.get_recorded_state(task)
```

An expiration rule after seven days could also inspect file modification times for
path-based tasks and nodes. For example:

```python
from datetime import datetime, timedelta, timezone

from optree import tree_leaves

import pytask


def run_on(task) -> bool:
    deadline = datetime.now(timezone.utc) - timedelta(days=7)

    if isinstance(task, pytask.PTaskWithPath):
        modified = datetime.fromtimestamp(task.path.stat().st_mtime, tz=timezone.utc)
        if modified < deadline:
            return True

    for node in tree_leaves(task.depends_on):
        if isinstance(node, pytask.PPathNode):
            modified = datetime.fromtimestamp(
                node.path.stat().st_mtime, tz=timezone.utc
            )
            if modified < deadline:
                return True

    for node in tree_leaves(task.produces):
        if isinstance(node, pytask.PPathNode):
            modified = datetime.fromtimestamp(
                node.path.stat().st_mtime, tz=timezone.utc
            )
            if modified < deadline:
                return True

    return False
```

The relevant use cases for a callable are currently:

- expiration-like rules which are more complex than a simple duration
- project-specific combinations of change kinds
- selective ignore rules for parts of the task state

This part of the interface is still more open than the declarative values above.

## Related

- [Task Execution Model](../explanations/execution_policies.md)
- [Reconciling Lockfile State](reconciling_lockfile_state.md)
- [Hashing Inputs Of Tasks](hashing_inputs_of_tasks.md)
