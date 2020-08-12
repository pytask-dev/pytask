How to configure pytask
=======================

pytask can be configured via the command-line interface or permanently with a
configuration file.


The configuration file
----------------------

pytask accepts configurations in three files which are ``pytask.ini``, ``tox.ini`` and
``setup.cfg``. Place a ``[pytask]`` section in those files and add your configuration
below.

.. code-block:: ini

    # Content of tox.ini

    [pytask]
    ignore =
        some_path

You can also leave the section empty. It will still have the benefit that pytask has a
stable root and will store the information about tasks, dependencies, and products in
the same directory as the configuration file.


.. _tutorial_configure_markers:

markers
-------

pytask uses markers to attach additional information to task functions. To see which
markers are available, type

.. code-block:: bash

    $ pytask --markers

on the command-line interface.

If you use a marker which has not been configured, you will get a warning. To silence
the warning and document the marker, provide the following information in your pytask
configuration file.

.. code-block:: ini

    markers =
        wip: Work-in-progress. These are tasks which I am currently working on.


ignore
------

pytask can ignore files and directories and exclude some tasks or reduce the duration of
the collection.

To ignore some file/folder via the command line, use the ``--ignore`` flag multiple
times.

.. code-block:: bash

    $ pytask --ignore */some_file.py --ignore */some_directory/*

Or, use the configuration file:

.. code-block:: ini

    # For single entries only.
    ignore = */some_file.py

    # Or single and multiple entries.
    ignore =
        */some_directory/*
        */some_file.py
