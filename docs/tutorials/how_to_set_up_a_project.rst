.. _how_to_set_up_a_project:

How to set up a project
=======================

This tutorial shows you how to set up your project with a simple structure.


The directory structure
-----------------------

The following directory tree is an example of how a project can be set up.

.. code-block::

    my_project
    ├───pytask.ini or tox.ini or setup.cfg
    │
    ├───src
    │   ├────config.py
    │   └────...
    │
    └───bld
        └────...

- The configuration file, ``pytask.ini``, ``tox.ini`` or ``setup.cfg``, should be placed
  at the root of the project folder and should contain a ``[pytask]`` section even if it
  is empty.

  .. code-block:: ini

      # Content of pytask.ini, tox.ini or setup.cfg.

      [pytask]

  The file in combination with the section will indicate the root of the project. This
  has two benefits.

  1. pytask needs to save some data across executions. It will store this information in
     a ``.pytask.sqlite3`` database in the root folder.

  2. Even if you start pytask from a different location inside the project folder than
     the root, the database will be found.

- Then, there exist two folders. The ``src`` directory contains the tasks and source
  files of the project.

  It also contains a ``config.py`` or a similar module to store the configuration of the
  project. For example, define paths pointing to the source and build directory.

  .. code-block:: python

      # Content of config.py.

      from pathlib import Path


      SRC = Path(__file__).parent
      BLD = SRC.joinpath("..", "bld").resolve()

- The build directory ``bld`` is used to store products of tasks. The separation between
  a source and build directory makes it easy to start from a clean project by deleting
  the build directory.


setup.py
--------

The ``setup.py`` is useful to turn the source directory into a Python package. It allows
to perform imports from ``src``. E.g., ``from src.config import SRC``.

Here is the content of the file.

.. code-block:: python

    # Content of setup.py

    from setuptools import setup


    setup(name="my_project", version="0.0.1")

Then, install the package into your environment with

.. code-block:: console

    $ conda develop .

    # or

    $ pip install -e .

Both commands will make an editable install of the project which means any changes in
the source files of the package are directly reflected in the installed version of the
package.

.. tip::

    Do not forget to rerun the editable install every time you recreate your Python
    environment.
