# The configuration

This document lists all options to configure pytask with a `pyproject.toml` file.

## The basics

To learn about the basics visit the {doc}`tutorial <../tutorials/configuration>`.

Examples for the TOML specification be found [here](https://toml.io/en/) or in
[PEP 518](https://peps.python.org/pep-0518/).

The configuration values are set under the `[tool.pytask.ini_options]` section to mimic
the old ini configurations and to allow pytask leveraging the full potential of the TOML
format in the future.

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

:::{note}
An error is only raised on Windows when a case-insensitive path is used. Contributions
are welcome to also support macOS.
:::

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

You can limit the number of entries displayed in the live table during the execution
to make it more clear. Use either `all` or an integer greater or equal to one. On
the command line use

```console
$ pytask build --n-entries-in-table 10
```

and in the configuration use

```toml
n_entries_in_table = "all"  # default 15
```

````

````{confval} paths

If you want to collect tasks from specific paths without passing the names via the
command line, you can add the paths to the configuration file. Paths passed via the
command line will overwrite the configuration value.

```toml

# For single entries only.
paths = "src"

# Or single and multiple entries.
paths = ["folder_1", "folder_2/task_2.py"]

```
````

````{confval} pdb

If you want to enter the interactive debugger whenever an error occurs, pass the
flag to the command line interface

```console
pytask build --pdb
```

or use a truthy configuration value.

```toml
pdb = true
```

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
task_files = "task_*.py"  # default

task_files = ["task_*.py", "tasks_*.py"]
```

````

````{confval} trace

If you want to enter the interactive debugger in the beginning of each task, use

```console
pytask build --trace
```

or set this option to a truthy value.

```toml
trace = true
```

````
