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
