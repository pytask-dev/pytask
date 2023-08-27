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

```

## Command Line Interface

```{eval-rst}
.. autofunction:: pytask_extend_command_line_interface

```

## Configuration

The following hooks are used to configure pytask with the information from the command
line and the configuration file as well as making sure that all options play nicely
together.

```{eval-rst}
.. autofunction:: pytask_configure
```

```{eval-rst}
.. autofunction:: pytask_parse_config
```

```{eval-rst}
.. autofunction:: pytask_post_parse

```

```{eval-rst}
.. autofunction:: pytask_unconfigure

```

## Collection

The following hooks traverse directories and collect tasks from files.

```{eval-rst}
.. autofunction:: pytask_collect
```

```{eval-rst}
.. autofunction:: pytask_ignore_collect
```

```{eval-rst}
.. autofunction:: pytask_collect_modify_tasks
```

```{eval-rst}
.. autofunction:: pytask_collect_file_protocol
```

```{eval-rst}
.. autofunction:: pytask_collect_file
```

```{eval-rst}
.. autofunction:: pytask_collect_task_protocol
```

```{eval-rst}
.. autofunction:: pytask_collect_task_setup
```

```{eval-rst}
.. autofunction:: pytask_collect_task
```

```{eval-rst}
.. autofunction:: pytask_collect_task_teardown
```

```{eval-rst}
.. autofunction:: pytask_collect_node
```

```{eval-rst}
.. autofunction:: pytask_collect_log

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
.. autofunction:: pytask_dag
```

```{eval-rst}
.. autofunction:: pytask_dag_create_dag
```

```{eval-rst}
.. autofunction:: pytask_dag_validate_dag
```

```{eval-rst}
.. autofunction:: pytask_dag_select_execution_dag
```

```{eval-rst}
.. autofunction:: pytask_dag_log

```

## Execution

The following hooks execute the tasks and log information on the result in the terminal.

```{eval-rst}
.. autofunction:: pytask_execute
```

```{eval-rst}
.. autofunction:: pytask_execute_log_start
```

```{eval-rst}
.. autofunction:: pytask_execute_create_scheduler
```

```{eval-rst}
.. autofunction:: pytask_execute_build
```

```{eval-rst}
.. autofunction:: pytask_execute_task_protocol
```

```{eval-rst}
.. autofunction:: pytask_execute_task_log_start
```

```{eval-rst}
.. autofunction:: pytask_execute_task_setup
```

```{eval-rst}
.. autofunction:: pytask_execute_task
```

```{eval-rst}
.. autofunction:: pytask_execute_task_teardown
```

```{eval-rst}
.. autofunction:: pytask_execute_task_process_report
```

```{eval-rst}
.. autofunction:: pytask_execute_task_log_end
```

```{eval-rst}
.. autofunction:: pytask_execute_log_end
```
