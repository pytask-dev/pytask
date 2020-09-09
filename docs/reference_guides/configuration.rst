The configuration
=================

This document lists all options to configure pytask via the configuration files.


The basics
----------

To learn about the basics visit the :doc:`tutorial
<../tutorials/how_to_configure_pytask>`.


Truthy and falsy values
-----------------------

For some of the configuration values you need truthy or falsy values. pytask recognizes
the following values.

- truthy: ``True``, ``true``, ``1``.
- falsy: ``False``, ``false``, ``0``.


The options
-----------

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


.. confval:: markers

    pytask uses markers to attach additional information to task functions. To see which
    markers are available, type

    .. code-block:: console

        $ pytask --markers

    on the command-line interface.

    If you use a marker which has not been configured, you will get a warning. To
    silence the warning and document the marker, provide the following information in
    your pytask configuration file.

    .. code-block:: ini

        markers =
            wip: Work-in-progress. These are tasks which I am currently working on.


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


.. confval:: pdb

    If you want to enter the interactive debugger when an error occurs, set this option
    to a truthy value.

    .. code-block:: ini

        pdb = True


.. confval:: strict_markers

    If you want to raise an error for unregistered markers, set this option to a truthy
    value.

    .. code-block:: ini

        strict_markers = True


.. confval:: trace

    If you want to enter the interactive debugger in the beginning of each task, set
    this option to a truthy value.

    .. code-block:: ini

        trace = True
