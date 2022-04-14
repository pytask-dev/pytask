# Invoking pytask

pytask is a command line program which can be invoked with

```console
$ pytask
```

Use the following flags to learn more about pytask and its configuration.

```console
$ pytask --version
$ pytask -h | --help
```

## Commands

pytask has multiple commands which are listed in the main help page.

```{image} /_static/images/help_page.svg
```

The `build` command is the default command which means the following two calls are
identical.

```console
$ pytask

$ pytask build
```

To see command-specific, use the help flag after the command.

```console
$ pytask <command-name> --help
```

## The build command

The build command accepts among many options paths as positional arguments. If no paths
are passed to the command line interface, pytask will look for the `paths` key in the
configuration file. At last, pytask will collect tasks from the current working
directory and subsequent folders.

You can also pass any number of paths of directories or modules to cli.

```console
$ pytask path/to/task_module.py path/to/folder
```

Do not use paths to run a subset of tasks in your project. Use
{doc}`expressions <selecting_tasks>` instead. When pytask collects tasks from subpaths
of your project, it cannot infer the whole structure of dependencies and products and
might run your tasks with missing or outdated dependencies.

## Options

Here are some useful options for the build command.

### Showing errors immediately

To show errors immediately when they occur, use

```console
$ pytask --show-errors-immediately
```

It can be useful when you have a long-running workflow, but want feedback as soon as it
is available.

### Stopping after the first (N) failures

To stop the build of the project after the first (N) failures use

```console
$ pytask -x | --stop-after-first-failure  # Stop after the first failure
$ pytask --max-failures 2                 # Stop after the second failure
```
