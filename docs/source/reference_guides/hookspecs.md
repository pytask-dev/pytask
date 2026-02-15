# Hook Specifications

Hook specifications are the `entry-points` provided by pytask to change the behavior of
the program.

The names of hooks always start with `pytask_` by convention. If you encounter hooks
which are suffixed with `_protocol`, it means that subsequent hooks are allowed to raise
exceptions which are handled and stored in a report.

!!! note "Migration status"

```
This page now uses `mkdocstrings` instead of Sphinx autodoc. Cross-reference
backlinks are more limited for now.
```

## General

::: \_pytask.hookspecs.pytask_add_hooks

## Command Line Interface

::: \_pytask.hookspecs.pytask_extend_command_line_interface

## Configuration

::: \_pytask.hookspecs.pytask_configure ::: \_pytask.hookspecs.pytask_parse_config :::
\_pytask.hookspecs.pytask_post_parse ::: \_pytask.hookspecs.pytask_unconfigure

## Collection

::: \_pytask.hookspecs.pytask_collect ::: \_pytask.hookspecs.pytask_ignore_collect :::
\_pytask.hookspecs.pytask_collect_modify_tasks :::
\_pytask.hookspecs.pytask_collect_file_protocol :::
\_pytask.hookspecs.pytask_collect_file :::
\_pytask.hookspecs.pytask_collect_task_protocol :::
\_pytask.hookspecs.pytask_collect_task_setup ::: \_pytask.hookspecs.pytask_collect_task
::: \_pytask.hookspecs.pytask_collect_task_teardown :::
\_pytask.hookspecs.pytask_collect_node ::: \_pytask.hookspecs.pytask_collect_log

## Execution

::: \_pytask.hookspecs.pytask_execute ::: \_pytask.hookspecs.pytask_execute_log_start
::: \_pytask.hookspecs.pytask_execute_build :::
\_pytask.hookspecs.pytask_execute_task_protocol :::
\_pytask.hookspecs.pytask_execute_task_log_start :::
\_pytask.hookspecs.pytask_execute_task_setup ::: \_pytask.hookspecs.pytask_execute_task
::: \_pytask.hookspecs.pytask_execute_task_teardown :::
\_pytask.hookspecs.pytask_execute_task_process_report :::
\_pytask.hookspecs.pytask_execute_task_log_end :::
\_pytask.hookspecs.pytask_execute_log_end
