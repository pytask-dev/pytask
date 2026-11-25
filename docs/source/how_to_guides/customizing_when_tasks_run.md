# Customizing when tasks run

By default, pytask decides whether a task should run by comparing the current state of
the task, its dependencies, and its products with the recorded state from a previous
run.

Sometimes this default is not precise enough. You may want to treat one kind of change
as relevant and another one as irrelevant.

For these cases, a task could define `run_on`.

!!! note

    This page sketches a possible interface. It is written as a design target, not as
    documentation for a released feature.

## When is this useful?

Typical situations are:

- An expensive task should rerun when dependencies change, but not when only comments,
    formatting, imports, or helper functions in the task module changed.
- A task should ignore product changes for the purpose of deciding whether to rerun.
    This can be useful when a product is post-processed manually or contains metadata
    that does not affect downstream tasks.
- A task should always run because it talks to an external service, records a timestamp,
    samples new data, or performs another intentional side effect.
- A task should refresh periodically, for example once per day for a remote dataset or
    once per week for a cached model.
- A task should refresh according to calendar time, for example on Monday morning or at
    the start of every month.
- A task should rerun when an external condition changes, such as an environment
    variable, package version, database revision, remote ETag, or model registry
    version.
- A task should rerun only for semantic changes, for example when a CSV schema changes
    but not when rows are reordered or comments in a configuration file change.

Some of these cases are better solved by changing how state is computed instead of by
changing the run condition. For example, semantic changes of inputs should usually be
modeled with a custom node or a custom hash function because the node knows what part of
the input is meaningful. The `run_on` interface should decide how to interpret detected
changes, not replace node state computation.

## Design goals

An optimal interface should satisfy a few constraints:

- Keep the current behavior as the default.
- Make common policies readable at the task definition.
- Treat missing products and `--force` as hard execution triggers.
- Validate declarative conditions early so misspellings do not silently change
    reproducibility.
- Keep one-off state reconciliation separate. If existing outputs should be accepted as
    current, use
    [`pytask lock accept`](../reference_guides/commands.md#pytask-lock-accept) instead
    of encoding that decision in every future run.
- Provide the same information to `--explain`, dry runs, and normal execution so users
    can understand why a task ran or was skipped.

The interface should therefore have two layers:

1. A declarative layer for most tasks.
1. A callable layer for project-specific rules.

## Use declarative policies

For many cases, it is enough to describe which changes should trigger execution.

The default should be `None`, which means that pytask uses its existing behavior. In
practice, this means a task runs when the task source, one of its dependencies, or one
of its products has changed.

The proposed public API should use explicit names instead of strings:

```python
from pathlib import Path

import pytask


@pytask.task(
    kwargs={"depends_on": Path("input.txt"), "produces": Path("output.txt")},
    run_on=pytask.RunOn.changed(
        dependencies=True,
        task=False,
        products=False,
    ),
)
def task_copy(depends_on: Path, produces: Path) -> None:
    produces.write_text(depends_on.read_text())
```

In this example, pytask reruns the task when dependencies change, but not when only the
task itself or its products changed.

The most useful constructors would be:

- `None`, which means pytask's default behavior.
- `pytask.RunOn.changed(...)`, which selects the kinds of state changes that matter.
- `pytask.RunOn.always()`, which always executes the task.
- `pytask.RunOn.after("7d")`, which reruns the task after the last successful execution
    or accepted state update is older than seven days.
- `pytask.RunOn.calendar("0 6 * * MON", timezone="Europe/Berlin")`, which reruns the
    task when a calendar schedule is due.
- `pytask.RunOn.any(...)` and `pytask.RunOn.all(...)`, which compose simpler policies.

For example, a cache can be refreshed when inputs change or when the cache is older than
one week:

```python
from pathlib import Path

import pytask


@pytask.task(
    kwargs={"depends_on": Path("raw.parquet"), "produces": Path("features.parquet")},
    run_on=pytask.RunOn.any(
        pytask.RunOn.changed(dependencies=True),
        pytask.RunOn.after("7d"),
    ),
)
def task_build_features(depends_on: Path, produces: Path) -> None: ...
```

And a side-effectful task can opt out of state-based skipping:

```python
from pathlib import Path

import pytask


@pytask.task(
    kwargs={"produces": Path("snapshot.json")},
    run_on=pytask.RunOn.always(),
)
def task_download_snapshot(produces: Path) -> None: ...
```

## Use custom state for semantic changes

If a task should rerun only when an input changes semantically, the best interface is
usually not `run_on`. Instead, encode the semantic state in the node.

For example, a task that depends only on the schema of a CSV file should depend on a
node whose `state()` returns a schema hash. Then the normal default run condition
remains correct because pytask sees the meaningful state change directly.

This keeps responsibilities separate:

- Nodes decide what state means.
- `run_on` decides which detected state changes require execution.
- [`pytask lock accept`](../reference_guides/commands.md#pytask-lock-accept) updates
    recorded state when existing outputs should be trusted without rerunning tasks.

## Use a callable for advanced policies

If declarative values are not enough, `run_on` can also be a callable.

```python
from pathlib import Path

import pytask


def needs_refresh(context: pytask.RunContext) -> bool: ...


@pytask.task(
    kwargs={"depends_on": Path("input.txt"), "produces": Path("output.txt")},
    run_on=needs_refresh,
)
def task_copy(depends_on: Path, produces: Path) -> None:
    produces.write_text(depends_on.read_text())
```

The callable should receive a context object instead of only the task. Passing a context
keeps the interface extensible and avoids forcing every user to know the internal
lockfile representation.

The context should expose:

- the current task
- detected changes for the task source, dependencies, and products
- the current and recorded state for each node
- `now`, the timestamp used for the whole run-condition decision
- `last_success`, the time of the last successful execution or accepted state update
- helpers for looking up dependencies and products by name

The Python shape could look like this:

```python
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypeAlias

import pytask


ChangeReason: TypeAlias = Literal[
    "unchanged",
    "changed",
    "missing",
    "not_in_lockfile",
    "first_run",
    "forced",
]


@dataclass(frozen=True)
class StateChange:
    node: pytask.PNode | pytask.PTask
    current: str | None
    recorded: str | None
    reason: ChangeReason

    @property
    def has_changed(self) -> bool:
        return self.reason != "unchanged"


@dataclass(frozen=True)
class ChangeSet:
    task: StateChange
    dependencies: Mapping[str, StateChange]
    products: Mapping[str, StateChange]

    @property
    def any(self) -> bool:
        return (
            self.task.has_changed or self.dependencies_changed or self.products_changed
        )

    @property
    def dependencies_changed(self) -> bool:
        return any(change.has_changed for change in self.dependencies.values())

    @property
    def products_changed(self) -> bool:
        return any(change.has_changed for change in self.products.values())


@dataclass(frozen=True)
class RunDecision:
    should_run: bool
    reason: str | None = None
    metadata: Mapping[str, str] | None = None

    @classmethod
    def run(cls, reason: str, metadata: Mapping[str, str] | None = None) -> RunDecision:
        return cls(should_run=True, reason=reason, metadata=metadata)

    @classmethod
    def skip(
        cls, reason: str, metadata: Mapping[str, str] | None = None
    ) -> RunDecision:
        return cls(should_run=False, reason=reason, metadata=metadata)


@dataclass(frozen=True)
class RunContext:
    task: pytask.PTask
    changed: ChangeSet
    now: datetime
    last_success: datetime | None
    recorded_metadata: Mapping[str, str]

    def dependency(self, name: str) -> StateChange:
        return self.changed.dependencies[name]

    def product(self, name: str) -> StateChange:
        return self.changed.products[name]


RunResult: TypeAlias = bool | RunDecision
RunCallable: TypeAlias = Callable[[RunContext], RunResult]
```

For example, a task can rerun when dependencies changed or when a remote API reports a
new version. The returned metadata can be stored after successful execution so the next
decision has the same comparison value available.

```python
import requests

import pytask


def needs_refresh(context: pytask.RunContext) -> pytask.RunDecision:
    response = requests.head("https://example.com/data.csv", timeout=10)
    remote_etag = response.headers.get("ETag")
    metadata = {"remote_etag": remote_etag} if remote_etag is not None else None

    if context.changed.dependencies_changed:
        return pytask.RunDecision.run("dependencies changed", metadata=metadata)

    if remote_etag != context.recorded_metadata.get("remote_etag"):
        return pytask.RunDecision.run("remote ETag changed", metadata=metadata)

    return pytask.RunDecision.skip("remote ETag is unchanged", metadata=metadata)
```

The callable should return a structured result when it needs to explain itself:

```python
import pytask


def needs_refresh(context: pytask.RunContext) -> pytask.RunDecision:
    if context.changed.dependencies_changed:
        return pytask.RunDecision.run("dependencies changed")

    if context.last_success is None:
        return pytask.RunDecision.run("task has no recorded successful execution")

    return pytask.RunDecision.skip("cache is still fresh")
```

A plain `bool` return value is convenient, but a structured result is better for
`--explain`, dry runs, and debugging.

The first version should keep `run_on` callables synchronous. Hidden event loop handling
inside the scheduler would be hard to explain, and it would make behavior depend on
whether pytask is already running inside an event loop. The design can still leave room
for a later extension by centralizing evaluation behind `RunCallable`. If async checks
become important, `RunCallable` could grow to:

```python
from collections.abc import Awaitable, Callable
from typing import TypeAlias


RunCallable: TypeAlias = Callable[[RunContext], RunResult | Awaitable[RunResult]]
```

That change should come with explicit scheduler semantics for when awaitables are
awaited, whether multiple run-condition checks may run concurrently, and how their
output appears in `--explain`.

## What pytask would need to record

State comparison is already available through the lockfile. Some proposed policies need
additional metadata:

- Relative time policies such as `pytask.RunOn.after("7d")` need the time of the last
    successful task execution or accepted state update. Without this timestamp there is
    no stable anchor for "older than seven days".
- Calendar policies need to know whether a scheduled run has already been satisfied.
    They can use `last_success` for simple schedules, but robust cron-like policies need
    the last satisfied schedule slot so a delayed run does not repeatedly satisfy the
    same due time.
- Custom callables may need small pieces of policy-specific metadata, such as a remote
    ETag or a database revision.

This metadata should live next to the task state in the lockfile and should be updated
only after successful execution or after an explicit state-acceptance command. Failed
tasks should not advance freshness metadata.

The lockfile should remain an implementation detail for normal users. The public API
should expose the relevant state through `RunContext`.

## Related

- [Hashing Inputs Of Tasks](hashing_inputs_of_tasks.md)
