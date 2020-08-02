.. _how_to_set_up_a_project:

How to set up a project
=======================

The previous sections in the tutorial explained the basic capabilities of pytask, but
how can we manage a bigger project with pytask?


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

* The configuration file, ``pytask.ini``, ``tox.ini`` or ``setup.cfg``, should be placed
  at the root of the project folder and should contain a ``[pytask]`` section even if it
  is empty.

  The file in combination with the section will indicate the root of the project. This
  has two benefits.

  1. pytask needs to save some data across executions. It will store this information in
     a ``.pytask.sqlite3`` database in the root folder.

  2. Even if you start pytask from a different location inside the project folder than
     the root, the database will be found.

  Here is a configuration file without any information except the section header.

  .. code-block:: ini

      # Content of pytask.ini, tox.ini or setup.cfg.

      [pytask]

* Then, there exist two folders. The ``src`` directory contains the tasks and other data
  and code.

  It also contains a ``config.py`` or a similar module from where the project
  configuration is read. You can store paths and other information which can be imported
  in other files to specify dependencies and targets. Here is an example of a
  ``config.py``.

  .. code-block:: python

      # Content of config.py.

      from pathlib import Path


      SRC = Path(__file__).parent
      BLD = SRC.joinpath("..", "bld").resolve()

* The build directory ``bld`` is used to store products of tasks. This makes it easy to
  rerun the whole project by just deleting the entire build directory.


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

.. code-block:: bash

    $ conda develop .

    # or

    $ pip install -e .
