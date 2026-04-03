# Task Execution Model

The task execution model can be confusing because several questions seem to arrive at
once: is the task still current, should it run, and what happens to the recorded state?

It becomes easier to follow once we stop looking at all of these questions at the same
time and instead watch an ordinary task move through pytask.

## The Normal Case

In the normal case, a task passes through four phases: setup, execution, teardown, and
processing the report.

### Setup

Setup is where pytask decides whether a task needs attention.

It checks a few basic questions first.

- Are all dependencies available and have they changed?
- Do the products already exist and have they changed?
- Has the task itself changed?

Generally, change means whether the current state of a node matches the recorded state
in the lockfile. For most filepath-based nodes, the state is the hash of the file
content.

If everything still matches the previously recorded state, the task is considered
unchanged and pytask will not run it.

If something does not match, the task is stale and pytask prepares to run it.

### Execution

Here pytask calls the task function itself.

### Teardown

Once the task function has returned, pytask checks whether the promised products are
really there.

This matters because a task can finish without raising an exception and still leave the
project in an incomplete state. Teardown is where pytask notices that kind of mismatch.

### Processing The Report

After teardown, pytask knows the outcome of the task. In case the task succeeded, this
is also the moment where pytask updates the recorded state for the task.

## Exceptions to the Rule

Not every task follows this path all the way through.

Markers and runtime options can short-circuit parts of the model. A task can be skipped,
persisted, or forced to run even when it would otherwise be left alone.

### Skipping Tasks

Sometimes a task and its subgraph should not run at all. This might be because the tasks
are too costly, buggy, or irrelevant for the current run.

For temporary exclusions, you would use the [`-m`](<>) or [`-k`](<>) options, maybe in
combination with a `not ...` expression.

For a permanent exclusion, you would use the
[`@pytask.mark.skip`](../api/marks.md#pytask.mark.skip) or
[`@pytask.mark.skipif`](../api/marks.md#pytask.mark.skipif) markers.

Skipping hooks into setup because pytask should stop before execution starts. All
dependent tasks are marked to be skipped as well.

### Persisting Tasks

Persisting is useful when a task would normally be considered stale, but rerunning it is
not desirable. A common example is a change to the task file that does not change the
actual result, such as formatting.

Persisting also has to hook into setup because pytask needs to decide early that the
task should not execute even though something changed. Later, when the report is
processed, pytask accepts the current state as the new recorded state.

Users can opt into this behavior with the
[`persist`](../tutorials/making_tasks_persist.md) marker. The disadvantage of the
decorator is that it is permanent and removing it triggers a rerun of the task.

What is missing is a temporary option of the persisting mechanism that would also allow
to integrate new or renamed tasks into an existing project without triggering a rerun.

### Forcing Tasks to Run

Sometimes the opposite is needed: a task should run even though pytask would otherwise
consider it unchanged.

This has to affect setup as well because setup is where pytask normally decides that an
unchanged task can be left alone. Forcing a task to run overrides that decision and lets
the task continue to execution.

Users can request this behavior with the `--force` option.

### Fine-grained Staleness Decision

The current model mostly answers staleness as a yes-or-no question based on recorded
state and the current state of the task, its dependencies, and its products.

Issue [#403](https://github.com/pytask-dev/pytask/issues/403) explores whether this
decision could become more fine-grained. For example, users might want to treat changes
to the task source differently from changes to dependencies or products, or they might
want to override the default decision for one run without changing the task itself.
