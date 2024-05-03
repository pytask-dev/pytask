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
.. autoclass:: pytask.DataCatalog
   :members:
```

## Marks

pytask uses marks to attach additional information to task functions that the host or
plugins process. The following marks are available by default.

### Built-in marks

```{eval-rst}
.. function:: pytask.mark.persist()

    A marker for a task which should be persisted.

.. function:: pytask.mark.skipif(condition: bool, *, reason: str)

    Skip a task based on a condition and provide a necessary reason.

    :param bool condition: A condition for when the task is skipped.
    :param str reason: A reason why the task is skipped.

.. function:: pytask.mark.skip_ancestor_failed(reason: str = "No reason provided")

    An internal marker for a task which is skipped because an ancestor failed.

    :param str reason: A reason why the task is skipped.

.. function:: pytask.mark.skip_unchanged()

    An internal marker for a task which is skipped because nothing has changed.

    :param str reason: A reason why the task is skipped.

.. function:: pytask.mark.skip()

    Skip a task.

.. function:: pytask.mark.try_first

    Indicate that the task should be executed as soon as possible.

    This indicator is a soft measure to influence the execution order of pytask.

    .. important::

        This indicator is not intended for general use to influence the build order and
        to overcome misspecification of task dependencies and products.

        It should only be applied to situations where it is hard to define all
        dependencies and products and automatic inference may be incomplete like with
        pytask-latex and latex-dependency-scanner.

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
def task_function(): ...
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
def task_function(): ...
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

## Protocols

Protocols define how tasks and nodes for dependencies and products have to be set up.

```{eval-rst}
.. autoprotocol:: pytask.PNode
   :show-inheritance:
.. autoprotocol:: pytask.PPathNode
   :show-inheritance:
.. autoprotocol:: pytask.PTask
   :show-inheritance:
.. autoprotocol:: pytask.PTaskWithPath
   :show-inheritance:
.. autoprotocol:: pytask.PProvisionalNode
   :show-inheritance:
```

## Nodes

Nodes are the interface for different kinds of dependencies or products.

```{eval-rst}
.. autoclass:: pytask.PathNode
   :members:
.. autoclass:: pytask.PickleNode
   :members:
.. autoclass:: pytask.PythonNode
   :members:
.. autoclass:: pytask.DirectoryNode
   :members:
```

To parse dependencies and products from nodes, use the following functions.

```{eval-rst}
.. autofunction:: pytask.parse_dependencies_from_task_function
.. autofunction:: pytask.parse_products_from_task_function
```

## Tasks

To mark any callable as a task use

```{eval-rst}
.. autofunction:: pytask.task
```

Task are currently represented by the following classes:

```{eval-rst}
.. autoclass:: pytask.Task
   :members:
.. autoclass:: pytask.TaskWithoutPath
   :members:
```

Currently, there are no different types of tasks since changing the `.function`
attribute with a custom callable proved to be sufficient.

To carry over information from user-defined tasks like task functions to
{class}`pytask.Task` objects, use a metadata object that is stored in an `.pytask_meta`
attribute of the task function.

```{eval-rst}
.. autoclass:: pytask.CollectionMetadata
    :members:
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

## Path utilities

```{eval-rst}
.. autofunction:: pytask.path.import_path
.. autofunction:: pytask.path.hash_path
```

## Programmatic Interfaces

```{eval-rst}
.. autofunction:: pytask.build_dag
.. autofunction:: pytask.build
```

## Reports

Reports are classes that handle successes and errors during the collection, dag
resolution and execution.

```{eval-rst}
.. autoclass:: pytask.CollectionReport
.. autoclass:: pytask.ExecutionReport
.. autoclass:: pytask.DagReport
```

## Tree utilities

```{eval-rst}
.. autoclass:: pytask.tree_util.PyTree
.. autofunction:: pytask.tree_util.tree_flatten_with_path
.. autofunction:: pytask.tree_util.tree_leaves
.. autofunction:: pytask.tree_util.tree_map
.. autofunction:: pytask.tree_util.tree_map_with_path
.. autofunction:: pytask.tree_util.tree_structure
```

## Typing

```{eval-rst}
..  class:: pytask.Product

    An indicator to mark arguments of tasks as products.

    >>> from pathlib import Path
    >>> from pytask import Product
    >>> from typing_extensions import Annotated
    >>> def task_example(path: Annotated[Path, Product]) -> None:
    ...     path.write_text("Hello, World!")

.. autofunction:: pytask.is_task_function
```

## Tracebacks

```{eval-rst}
.. autoclass:: pytask.Traceback
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
