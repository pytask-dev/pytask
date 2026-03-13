# Invoking pytask

Invoke pytask from the command line with

```console
$ pytask
```

Use the following flags to learn more about pytask and its configuration.

```console
$ pytask --version
$ pytask -h | --help
```

## Commands

pytask has multiple commands listed on the main help page.

--8<-- "docs/source/_static/md/help-page.md"

The `build` command is the default command, meaning the following two calls are
identical.

```console
$ pytask
$ pytask build
```

Display command-specific information by adding the help flag after the command.

```console
$ pytask <command-name> -h/--help
```

## The build command

The build command accepts many options and paths as positional arguments. If no paths
are passed via the command line interface, pytask will look for
[`paths`](../reference_guides/configuration.md#paths) in the configuration file. At
last, pytask will collect tasks from the current working directory and subsequent
folders.

You can also pass any number of paths of directories or modules to the program.

```console
$ pytask path/to/task_module.py path/to/folder
```

Don't use paths to run task subsets. Use [expressions](selecting_tasks.md) instead. When
pytask collects tasks from subpaths of your project, it cannot infer the whole structure
of dependencies and products and might run your tasks with missing or outdated
dependencies.

## Options

Here are a few selected options for the build command.

### Showing errors immediately

To show errors immediately when they occur, use

```console
$ pytask --show-errors-immediately
```

It can be helpful when you have a long-running workflow but want feedback as soon as it
is available.

### Stopping after the first (N) failures

To stop the build of the project after the first `n` failures, use

```console
$ pytask -x | --stop-after-first-failure  # Stop after the first failure
$ pytask --max-failures 2                 # Stop after the second failure
```

### Performing a dry-run

Do a dry run to see which tasks will be executed without executing them.

--8<-- "docs/source/_static/md/dry-run.md"

### Explaining why tasks are executed

Use the `--explain` flag to understand why tasks need to be executed. This shows what
changed (source files, dependencies, products, previous tasks) and helps you understand
pytask's execution decisions.

--8<-- "docs/source/_static/md/explain.md"

The explanation output respects the `--verbose` flag:

- Default verbosity: Shows tasks that would be executed and skipped tasks
- `-v` or `--verbose 1`: Same as default, with summary for persisted and unchanged tasks
- `--verbose 2`: Shows detailed information including persisted and unchanged tasks with
    change reasons

## Functional interface

pytask also has a functional interface that is explained in this
[article](../how_to_guides/functional_interface.ipynb).
