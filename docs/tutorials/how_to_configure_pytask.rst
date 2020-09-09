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
the same directory as the configuration file in a database called ``.pytask.sqlite3``.


The location
------------

There are two ways to find the configuration file when invoking pytask.

First, it is possible to pass the location of the configuration file via
:option:`pytask build -c` like

.. code-block:: bash

    $ pytask -c config/pytask.ini

The second option is to let pytask try to find the configuration itself. pytask will
first look in the current working directory or the common ancestors of multiple paths to
tasks. It will search for ``pytask.ini``, ``tox.ini`` and ``setup.cfg`` in this order.
Whenever a ``[pytask]`` section is found, the search stops.

If no file is found in the current directory, pytask will climb up the directory tree
and search in parent directories.


The options
-----------

You can find all possible configuration values in the :doc:`reference guide on the
configuration <../reference_guides/configuration>`.


Further reading
---------------

- :doc:`../reference_guides/configuration`.
