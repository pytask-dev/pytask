# The configuration

This document lists all options to configure pytask via the configuration files.

## The basics

To learn about the basics visit the {doc}`tutorial <../tutorials/configuration>`.

## Truthy and falsy values

For some of the configuration values you need truthy or falsy values. pytask recognizes
the following values.

- truthy: `True`, `true`, `1`.
- falsy: `False`, `false`, `0`.

Additionally, the following values are interpreted as None which is neither truthy or
falsy.

- `None`
- `none`

## The options

```{eval-rst}
.. confval:: check_casing_of_paths

    Since pytask encourages platform-independent reproducibility, it will raise a
    warning if you used a path with incorrect casing on a case-insensitive file system.
    For example, the path ``TeXt.TxT`` will match the actual file ``text.txt`` on
    case-insensitive file systems (usually Windows and macOS), but not on case-sensitive
    systems (usually Linux).

    If you have very strong reasons for relying on this inaccuracy, although, it is
    strongly discouraged, you can deactivate the warning in the configuration file with

    .. code-block:: ini

        check_casing_of_paths = false

    .. note::

        An error is only raised on Windows when a case-insensitive path is used.
        Contributions are welcome to also support macOS.

```

```{eval-rst}
.. confval:: editor_url_scheme

    Depending on your terminal, pytask is able to turn task ids into clickable links to
    the modules in which tasks are defined. By default, following the link will open the
    module with your default application. It is done with

    .. code-block:: ini

        editor_url_scheme = file

    If you use ``vscode`` or ``pycharm`` instead, the file will be opened in the
    specified editor and the cursor will also jump to the corresponding line.

    .. code-block:: ini

        editor_url_scheme = vscode | pycharm

    For complete flexibility, you can also enter a custom url which can use the
    variables ``path`` and ``line_number`` to open the file.

    .. code-block:: ini

        editor_url_scheme = editor://{path}:{line_number}

    Maybe you want to contribute this URL scheme to make it available to more people.

    To disable links, use

    .. code-block:: ini

        editor_url_scheme = no_link

```

```{eval-rst}
.. confval:: ignore

    pytask can ignore files and directories and exclude some tasks or reduce the
    duration of the collection.

    To ignore some file/folder via the command line, use the ``--ignore`` flag multiple
    times.

    .. code-block:: console

        $ pytask --ignore some_file.py --ignore some_directory/*

    Or, use the configuration file:

    .. code-block:: ini

        # For single entries only.
        ignore = some_file.py

        # Or single and multiple entries.
        ignore =
            some_directory/*
            some_file.py

```

```{eval-rst}
.. confval:: markers

    pytask uses markers to attach additional information to task functions. To see which
    markers are available, type

    .. code-block:: console

        $ pytask markers

    on the command-line interface.

    If you use a marker which has not been configured, you will get a warning. To
    silence the warning and document the marker, provide the following information in
    your pytask configuration file.

    .. code-block:: ini

        markers =
            wip: Work-in-progress. These are tasks which I am currently working on.

```

```{eval-rst}
.. confval:: n_entries_in_table

    You can limit the number of entries displayed in the live table during the execution
    to make it more clear. Use either ``all`` or an integer greater or equal to one. On
    the command line use

    .. code-block:: console

        $ pytask build --n-entries-in-table 10

    and in the configuration use

    .. code-block:: ini

        n_entries_in_table = all  # default 15

```

```{eval-rst}
.. confval:: paths

    If you want to collect tasks from specific paths without passing the names via the
    command line, you can add the paths to the configuration file. Paths passed via the
    command line will overwrite the configuration value.

    .. code-block:: ini

        # For single entries only.
        paths = src

        # Or single and multiple entries.
        paths =
            folder_1
            folder_2/task_2.py

```

```{eval-rst}
.. confval:: pdb

    If you want to enter the interactive debugger whenever an error occurs, pass the
    flag to the command line interface

    .. code-block:: console

        pytask build --pdb

    or use a truthy configuration value.

    .. code-block:: ini

        pdb = True

```

```{eval-rst}
.. confval:: show_errors_immediately

    If you want to print the exception and tracebacks of errors as soon as they occur,
    set this value to true.

    .. code-block:: console

        pytask build --show-errors-immediately

    .. code-block:: ini

        show_errors_immediately = True

```

```{eval-rst}
.. confval:: show_locals

    If you want to print local variables of each stack frame in the tracebacks, set this
    value to true.

    .. code-block:: console

        pytask build --show-locals

    .. code-block:: ini

        show_locals = True

```

```{eval-rst}
.. confval:: strict_markers

    If you want to raise an error for unregistered markers, pass

    .. code-block:: console

        pytask build --strict-markers

    or set the option to a truthy value.

    .. code-block:: ini

        strict_markers = True

```

```{eval-rst}
.. confval:: task_files

    Change the pattern which identify task files.

    .. code-block:: ini

        task_files = task_*.py  # default

        task_files =
            task_*.py
            tasks_*.py

```

```{eval-rst}
.. confval:: trace

    If you want to enter the interactive debugger in the beginning of each task, use

    .. code-block:: console

        pytask build --trace

    or set this option to a truthy value.

    .. code-block:: ini

        trace = True
```
