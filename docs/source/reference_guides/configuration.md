# The configuration

This document lists all options to configure pytask with a `pyproject.toml` file.

## The basics

To learn about the basics visit the {doc}`tutorial <../tutorials/configuration>`.

Examples for the TOML specification be found [here](https://toml.io/en/) or in
[PEP 518](https://peps.python.org/pep-0518/).

The configuration values are set under the `[tool.pytask.ini_options]` section to mimic
the old ini configurations and to allow pytask leveraging the full potential of the TOML
format in the future.

```toml
[tool.pytask.ini_options]
editor_url_scheme = "vscode"
```

## The options

````{confval} check_casing_of_paths

Since pytask encourages platform-independent reproducibility, it will raise a
warning if you used a path with incorrect casing on a case-insensitive file system.
For example, the path `TeXt.TxT` will match the actual file `text.txt` on
case-insensitive file systems (usually Windows and macOS), but not on case-sensitive
systems (usually Linux).

If you have very strong reasons for relying on this inaccuracy, although, it is
strongly discouraged, you can deactivate the warning in the configuration file with

```toml
check_casing_of_paths = false
```

```{note}
An error is only raised on Windows when a case-insensitive path is used. Contributions
are welcome to also support macOS.
```

````

````{confval} database_url

SQLite is the legacy state format. pytask now uses `pytask.lock` as the primary state
backend and only consults the database when no lockfile exists. During that first run,
the lockfile is written and subsequent runs use the lockfile only.

The `database_url` option remains for backwards compatibility and controls the legacy
database location and dialect ([supported by sqlalchemy](https://docs.sqlalchemy.org/en/latest/core/engines.html#backend-specific-urls)).

```toml
database_url = "sqlite:///.pytask/pytask.sqlite3"
```

Relative paths for SQLite databases are interpreted as either relative to the
configuration file or the root directory.

````

````{confval} editor_url_scheme

Depending on your terminal, pytask is able to turn task ids into clickable links to the
modules in which tasks are defined. By default, following the link will open the module
with your default application. It is done with

```toml
editor_url_scheme = "file"
```

If you use `vscode` or `pycharm` instead, the file will be opened in the
specified editor and the cursor will also jump to the corresponding line.

```toml
editor_url_scheme = "vscode"

# or

editor_url_scheme = "pycharm"
```

For complete flexibility, you can also enter a custom url which can use the
variables `path` and `line_number` to open the file.

```toml
editor_url_scheme = "editor://{path}:{line_number}"
```

Maybe you want to contribute this URL scheme to make it available to more people.

To disable links, use

```toml
editor_url_scheme = "no_link"
```

````

````{confval} hook_module

Register additional modules containing hook implementations.

```toml
hook_modules = ["myproject.hooks", "hooks.py"]
```

You can use module names and paths as values. Relative paths are assumed to be relative
to the configuration file or the current working directory.

{ref}`This how-to guide <hook-module>` has more information.

````

````{confval} ignore

pytask can ignore files and directories and exclude some tasks or reduce the duration of
the collection.

To ignore some file/folder via the command line, use the `--ignore` flag multiple
times.

```console
$ pytask --ignore some_file.py --ignore some_directory/*
```

Or, use the configuration file:

```toml
# For single entries only.
ignore = "some_file.py"

# Or single and multiple entries.
ignore = ["some_directory/*", "some_file.py"]
```

````

````{confval} markers

pytask uses markers to attach additional information to task functions. To see which
markers are available, type

```console
$ pytask markers
```

on the command-line interface.

If you use a marker which has not been configured, you will get a warning. To
silence the warning and document the marker, provide the following information in
your pytask configuration file.

```toml
[tool.pytask.ini_options.markers]
wip = "Work-in-progress. These are tasks which I am currently working on."
```

````

````{confval} n_entries_in_table

You can set the number of entries displayed in the live table during the execution to any positive integer including zero.

```console
$ pytask build --n-entries-in-table 10
```

````

````{confval} sort_table

You can decide whether the entries displayed in the live table are sorted alphabetically
once all tasks have been executed, which can be helpful when working with many tasks.
Use either `true` or `false`. This option is only supported in the configuration file.

```toml
sort_table = false  # default: true
```

````

````{confval} paths

If you want to collect tasks from specific paths without passing the names via the
command line, you can add the paths to the configuration file. Paths passed via the
command line will overwrite the configuration value.

```toml
paths = ["folder_1", "folder_2/task_2.py"]
```
````

````{confval} pdbcls

If you want to use a custom debugger instead of the standard Python debugger, you can
specify it with the `pdbcls` option. The value must be in the format
`module_name:class_name`.

```console
$ pytask build --pdbcls=IPython.terminal.debugger:TerminalPdb
```

Or, use the configuration file:

```toml
pdbcls = "IPython.terminal.debugger:TerminalPdb"
```

This is particularly useful when working with enhanced debuggers like `pdbpp` or `pdbp`
that provide additional features such as syntax highlighting and tab completion:

```toml
pdbcls = "pdbp:Pdb"
```

The custom debugger will be used when you invoke the `--pdb` flag for post-mortem
debugging or when using `breakpoint()` in your task code.

````

````{confval} show_errors_immediately

If you want to print the exception and tracebacks of errors as soon as they occur,
set this value to true.

```console
pytask build --show-errors-immediately
```

```toml
show_errors_immediately = true
```

````

````{confval} show_locals

If you want to print local variables of each stack frame in the tracebacks, set this
value to true.

```console
pytask build --show-locals
```

```toml
show_locals = true
```

````

````{confval} strict_markers

If you want to raise an error for unregistered markers, pass

```console
pytask build --strict-markers
```

or set the option to a truthy value.

```toml
strict_markers = true
```

````

````{confval} task_files

Change the pattern which identify task files.

```toml
task_files = ["task_*.py"]  # default

task_files = ["task_*.py", "tasks_*.py"]
```

````
