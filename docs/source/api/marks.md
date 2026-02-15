# Marks

Built-in marks are exposed dynamically via `pytask.mark`, so their API is documented
manually here.

## Built-In Marks

### `pytask.mark.persist`

```python
@pytask.mark.persist
```

Prevent execution of a task when all neighboring nodes exist, even if something changed.
See [making tasks persist](../tutorials/making_tasks_persist.md).

### `pytask.mark.skip`

```python
@pytask.mark.skip
```

Skip a task and all downstream tasks.
See [skipping tasks](../tutorials/skipping_tasks.md).

### `pytask.mark.skipif`

```python
@pytask.mark.skipif(condition: bool, *, reason: str)
```

Skip a task and all downstream tasks when `condition` is `True`.
See [skipping tasks](../tutorials/skipping_tasks.md).

### `pytask.mark.try_first`

```python
@pytask.mark.try_first
```

Prefer running a task as early as possible in the DAG.
See [how to influence build order](../how_to_guides/how_to_influence_build_order.md).

### `pytask.mark.try_last`

```python
@pytask.mark.try_last
```

Prefer running a task as late as possible in the DAG.
See [how to influence build order](../how_to_guides/how_to_influence_build_order.md).

## Mark Classes

::: pytask.Mark
    options:
      filters:
        - "!^_[^_].*"
        - "!^__.*__$"
      show_root_heading: true
      show_signature: true
::: pytask.mark
::: pytask.MarkDecorator
    options:
      filters:
        - "!^_[^_].*"
        - "!^__.*__$"
::: pytask.MarkGenerator
    options:
      filters:
        - "!^_[^_].*"
        - "!^__.*__$"

## Mark Utilities

::: pytask.get_all_marks
::: pytask.get_marks
::: pytask.has_mark
::: pytask.remove_marks
::: pytask.set_marks
