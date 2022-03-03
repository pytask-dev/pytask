# Hook Specifications

```{eval-rst}
.. currentmodule:: _pytask.hookspecs
```

Hook specifications are the {term}`entry-points <entry-point>` provided by pytask to
change the behavior of the program.

The following sections provide an overview of the different phases while executing the
tasks the purpose of the entry-points.

## Naming

The names of hooks always start with `pytask_` by convention. The following term usually
specifies the phase during the execution of tasks if there exist a group of hook
specifications.

If you encounter hooks which are suffixed with `_protocol`, it means that subsequent
hooks are allowed to raise exceptions which are handled and stored in a report.

## General

```{eval-rst}
.. autofunction:: pytask_add_hooks
   :noindex:

```

## Command Line Interface

```{eval-rst}
.. autofunction:: pytask_extend_command_line_interface
   :noindex:

```

## Configuration

The following hooks are used to configure pytask with the information from the command
line and the configuration file as well as making sure that all options play nicely
together.

```{eval-rst}
.. autofunction:: pytask_configure
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_parse_config
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_post_parse
   :noindex:

```

```{eval-rst}
.. autofunction:: pytask_unconfigure
   :noindex:

```

## Collection

The following hooks traverse directories and collect tasks from files.

```{eval-rst}
.. autofunction:: pytask_collect
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_ignore_collect
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_modify_tasks
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_file_protocol
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_file
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_task_protocol
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_task_setup
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_task
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_task_teardown
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_node
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_collect_log
   :noindex:

```

## Parametrization

The hooks to parametrize a task are called during the collection when a function is
collected. Then, the function is duplicated according to the parametrization and the
duplicates are collected with {func}`pytask_collect_task`.

```{eval-rst}
.. autofunction:: pytask_parametrize_task
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_parametrize_kwarg_to_marker
   :noindex:

```

## Resolving Dependencies

The following hooks are designed to build a DAG from tasks and dependencies and check
which files have changed and need to be re-run.

:::{warning}
This step is still experimental and likely to change in the future. If you are planning
to write a plugin which extends pytask in this dimension, please, start a discussion
before writing a plugin. It may make your life easier if changes in pytask anticipate
your plugin.
:::

```{eval-rst}
.. autofunction:: pytask_resolve_dependencies
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_resolve_dependencies_create_dag
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_resolve_dependencies_validate_dag
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_resolve_dependencies_select_execution_dag
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_resolve_dependencies_log
   :noindex:

```

## Execution

The following hooks execute the tasks and log information on the result in the terminal.

```{eval-rst}
.. autofunction:: pytask_execute
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_log_start
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_create_scheduler
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_build
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_task_protocol
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_task_log_start
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_task_setup
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_task
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_task_teardown
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_task_process_report
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_task_log_end
   :noindex:
```

```{eval-rst}
.. autofunction:: pytask_execute_log_end
   :noindex:
```
