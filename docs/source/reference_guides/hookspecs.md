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
.. autofunction:: pytask_parse_config
.. autofunction:: pytask_post_parse
.. autofunction:: pytask_unconfigure
```

## Collection

The following hooks traverse directories and collect tasks from files.

```{eval-rst}
.. autofunction:: pytask_collect
.. autofunction:: pytask_ignore_collect
.. autofunction:: pytask_collect_modify_tasks
.. autofunction:: pytask_collect_file_protocol
.. autofunction:: pytask_collect_file
.. autofunction:: pytask_collect_task_protocol
.. autofunction:: pytask_collect_task_setup
.. autofunction:: pytask_collect_task
.. autofunction:: pytask_collect_task_teardown
.. autofunction:: pytask_collect_node
.. autofunction:: pytask_collect_log
```

## Execution

The following hooks execute the tasks and log information on the result in the terminal.

```{eval-rst}
.. autofunction:: pytask_execute
.. autofunction:: pytask_execute_log_start
.. autofunction:: pytask_execute_create_scheduler
.. autofunction:: pytask_execute_build
.. autofunction:: pytask_execute_task_protocol
.. autofunction:: pytask_execute_task_log_start
.. autofunction:: pytask_execute_task_setup
.. autofunction:: pytask_execute_task
.. autofunction:: pytask_execute_task_teardown
.. autofunction:: pytask_execute_task_process_report
.. autofunction:: pytask_execute_task_log_end
.. autofunction:: pytask_execute_log_end
```
