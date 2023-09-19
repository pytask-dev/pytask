# API

## Command line interface

To extend pytask's command line interface and set the right types for your options,
pytask offers the following functionalities.

### Classes

```{eval-rst}
.. autoclass:: pytask.ColoredCommand
.. autoclass:: pytask.ColoredGroup
.. autoclass:: pytask.EnumChoice
```

## Compatibility

```{eval-rst}
.. autofunction:: pytask.check_for_optional_program
.. autofunction:: pytask.import_optional_dependency
```

## Console

To write to the terminal, use pytask's console.

```{eval-rst}
.. class:: pytask.console
```

## Marks

pytask uses marks to attach additional information to task functions which is processed
by the host or by plugins. The following marks are available by default.

### Marks

```{eval-rst}
.. function:: pytask.mark.depends_on(objects: Any | Iterable[Any] | dict[Any, Any])

    Specify dependencies for a task.

    :type objects: Any | Iterable[Any] | dict[Any, Any]
    :param objects:
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`_pytask.hookspecs.pytask_collect_node` entry-point.
```

```{eval-rst}
.. function:: pytask.mark.persist()

    A marker for a task which should be peristed.
```

```{eval-rst}
.. function:: pytask.mark.produces(objects: Any | Iterable[Any] | dict[Any, Any])

    Specify products of a task.

    :type objects: Any | Iterable[Any] | dict[Any, Any]
    :param objects:
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`_pytask.hookspecs.pytask_collect_node` entry-point.
```

```{eval-rst}
.. function:: pytask.mark.skipif(condition: bool, *, reason: str)

    Skip a task based on a condition and provide a necessary reason.

    :param bool condition: A condition for when the task is skipped.
    :param str reason: A reason why the task is skipped.
```

```{eval-rst}
.. function:: pytask.mark.skip_ancestor_failed(reason: str = "No reason provided")

    An internal marker for a task which is skipped because an ancestor failed.

    :param str reason: A reason why the task is skipped.
```

```{eval-rst}
.. function:: pytask.mark.skip_unchanged()

    An internal marker for a task which is skipped because nothing has changed.

    :param str reason: A reason why the task is skipped.
```

```{eval-rst}
.. function:: pytask.mark.skip()

    Skip a task.
```

```{eval-rst}
.. function:: pytask.mark.task(name, *, id, kwargs)

    The task decorator allows to mark any task function regardless of its name as a task
    or assigns a new task name.

    It also allows to repeat tasks in for-loops by adding a specific ``id`` or keyword
    arguments via ``kwargs``.

    .. deprecated:: 0.4.0

       Will be removed in v0.5.0. Use :func:`~pytask.task` instead.

    :type name: str | None
    :param name: The name of the task.
    :type id: str | None
    :param id:  An id for the task if it is part of a parametrization.
    :type kwargs: dict[Any, Any] | None
    :param kwargs:
        A dictionary containing keyword arguments which are passed to the task when it
        is executed.

```

```{eval-rst}
.. function:: pytask.mark.try_first

    Indicate that the task should be executed as soon as possible.

    This indicator is a soft measure to influence the execution order of pytask.

    .. important::

        This indicator is not intended for general use to influence the build order and
        to overcome misspecification of task dependencies and products.

        It should only be applied to situations where it is hard to define all
        dependencies and products and automatic inference may be incomplete like with
        pytask-latex and latex-dependency-scanner.

```

```{eval-rst}
.. function:: pytask.mark.try_last

    Indicate that the task should be executed as late as possible.

    This indicator is a soft measure to influence the execution order of pytask.

    .. important::

        This indicator is not intended for general use to influence the build order and
        to overcome misspecification of task dependencies and products.

        It should only be applied to situations where it is hard to define all
        dependencies and products and automatic inference may be incomplete like with
        pytask-latex and latex-dependency-scanner.
```

### Custom marks

Marks are created dynamically using the factory object {class}`pytask.mark` and applied
as a decorator.

For example:

```python
@pytask.mark.timeout(10, "slow", method="thread")
def task_function():
    ...
```

Will create and attach a {class}`Mark <pytask.Mark>` object to the collected
{class}`Task <pytask.Task>` to the `markers` attribute. The `mark` object will have the
following attributes:

```python
mark.args == (10, "slow")
mark.kwargs == {"method": "thread"}
```

Example for using multiple custom markers:

```python
@pytask.mark.timeout(10, "slow", method="thread")
@pytask.mark.slow
def task_function():
    ...
```

### Classes

```{eval-rst}
.. autoclass:: pytask.Mark
.. autoclass:: pytask.mark
.. autoclass:: pytask.MarkDecorator
.. autoclass:: pytask.MarkGenerator
```

### Functions

These functions help you to handle marks.

```{eval-rst}
.. autofunction:: pytask.get_all_marks
.. autofunction:: pytask.get_marks
.. autofunction:: pytask.has_mark
.. autofunction:: pytask.remove_marks
.. autofunction:: pytask.set_marks
```

## Exceptions

Exceptions all inherit from

```{eval-rst}
.. autoclass:: pytask.PytaskError
```

The following exceptions can be used to interrupt pytask's flow, emit reduced tracebacks
and return the correct exit codes.

```{eval-rst}
.. autoclass:: pytask.CollectionError
.. autoclass:: pytask.ConfigurationError
.. autoclass:: pytask.ExecutionError
.. autoclass:: pytask.ResolvingDependenciesError
```

The remaining exceptions convey specific errors.

```{eval-rst}
.. autoclass:: pytask.NodeNotCollectedError
.. autoclass:: pytask.NodeNotFoundError
```

## General classes

```{eval-rst}
.. autoclass:: pytask.Session
```

## Nodes

Nodes are the interface for different kinds of dependencies or products. They inherit
from {class}`pytask.MetaNode`.

```{eval-rst}
.. autoclass:: pytask.MetaNode
```

Then, different kinds of nodes can be implemented.

```{eval-rst}
.. autoclass:: pytask.PathNode
    :members:
```

```{eval-rst}
.. autoclass:: pytask.PythonNode
    :members:
```

To parse dependencies and products from nodes, use the following functions.

```{eval-rst}
.. autofunction:: pytask.depends_on
.. autofunction:: pytask.parse_nodes
.. autofunction:: pytask.produces
```

## Tasks

To mark any callable as a task use

```{eval-rst}
.. autofunction:: pytask.task
```

Task are currently represented by the following class:

```{eval-rst}
.. autoclass:: pytask.Task
```

Currently, there are no different types of tasks since changing the `.function`
attribute with a custom callable proved to be sufficient.

To carry over information from user-defined tasks like task functions to
{class}`pytask.Task` objects, use a metadata object that is stored in an `.pytask_meta`
attribute of the task function.

```{eval-rst}
.. autoclass:: pytask.CollectionMetadata
```

## Outcomes

The exit code of pytask is determined by

```{eval-rst}
.. autoclass:: pytask.ExitCode
    :members:
    :member-order: bysource
```

Collected items can have the following outcomes

```{eval-rst}
.. autoclass:: pytask.CollectionOutcome
```

Tasks can have the following outcomes

```{eval-rst}
.. autoclass:: pytask.TaskOutcome
```

The following exceptions are used to abort the execution of a task with an appropriate
outcome.

```{eval-rst}
.. autoclass:: pytask.Exit
.. autoclass:: pytask.Persisted
.. autoclass:: pytask.Skipped
.. autoclass:: pytask.SkippedAncestorFailed
.. autoclass:: pytask.SkippedUnchanged
```

### Functions

```{eval-rst}
.. autofunction:: pytask.count_outcomes
```

## Programmatic Interfaces

```{eval-rst}
.. autofunction:: pytask.build_dag
.. autofunction:: pytask.build
```

## Reports

There are some classes to handle different kinds of reports.

```{eval-rst}
.. autoclass:: pytask.CollectionReport
.. autoclass:: pytask.ExecutionReport
.. autoclass:: pytask.DagReport
```

## Tracebacks

```{eval-rst}
.. autofunction:: pytask.format_exception_without_traceback
.. autofunction:: pytask.remove_internal_traceback_frames_from_exc_info
.. autofunction:: pytask.remove_traceback_from_exc_info
.. autofunction:: pytask.render_exc_info
```

## Warnings

### Classes

```{eval-rst}
.. autoclass:: pytask.WarningReport
```

### Functions

```{eval-rst}
.. autofunction:: pytask.parse_warning_filter
.. autofunction:: pytask.warning_record_to_str
```
