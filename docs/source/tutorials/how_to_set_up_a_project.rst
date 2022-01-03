.. _how_to_set_up_a_project:

How to set up a project
=======================

This tutorial shows you how to set up your first project. It also explains the purpose
of the most elementary pieces.

.. seealso::

    If you want to start from a template or take inspiration from previous projects, look at :doc:`../how_to_guides/bp_templates_and_projects`.


The directory structure
-----------------------

The following directory tree is an example of how a project can be set up.

.. code-block::

    my_project
    ├───pytask.ini or tox.ini or setup.cfg
    │
    ├───src
    │   └───my_project
    │       ├────config.py
    │       └────...
    │
    ├───setup.py
    │
    ├───.pytask.sqlite3
    │
    └───bld
        └────...


The configuration
~~~~~~~~~~~~~~~~~

The configuration resides in either a ``pytask.ini``, ``tox.ini``, or ``setup.cfg``
file. The file is placed in the root folder of the project and contains a ``[pytask]``
section which can be left empty. Here, we set ``paths`` such that it points to the
project.

.. code-block:: ini

    # Content of pytask.ini, tox.ini or setup.cfg.

    [pytask]
    paths = ./src/my_project

The file in combination with an empty section will signal the root of the project to
pytask. This has two benefits.

1. pytask needs to save some data across executions. It will store this information in
   a ``.pytask.sqlite3`` database in the root folder.

2. If you start pytask without a path - simply ``pytask`` - from a different location
   inside the project folder than the root, the database will be found and pytask runs
   as if it is run in the project root.


The source directory
~~~~~~~~~~~~~~~~~~~~

The ``src`` directory is empty except for a folder containing the tasks and source files
of the project. The nested structure is called the src layout and the preferred way to
structure Python packages.

.. seealso::

    You find a better explanation of the src layout in `this article by Hynek Schlawack
    <https://hynek.me/articles/testing-packaging/>`_.

It also contains a ``config.py`` or a similar module to store the configuration of the
project. For example, you should define paths pointing to the source and build
directory of the project.

.. code-block:: python

    # Content of config.py.

    from pathlib import Path


    SRC = Path(__file__).parent.resolve()
    BLD = SRC.joinpath("..", "..", "bld").resolve()


The build directory
~~~~~~~~~~~~~~~~~~~

The build directory ``bld`` is created automatically during the execution. It is used
to store the products of tasks and can be deleted to rebuild the entire project.


``setup.py``
~~~~~~~~~~~~

The ``setup.py`` is useful to turn the source directory into a Python package. It allows
to perform imports from ``src``. E.g., ``from src.config import SRC``.

Here is the content of the file.

.. code-block:: python

    # Content of setup.py

    from setuptools import setup


    setup(
        name="my_project",
        version="0.0.1",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
    )

Then, install the package into your environment with

.. code-block:: console

    $ conda develop .

    # or

    $ pip install -e .

Both commands will produce an editable install of the project which means any changes in
the source files of the package are reflected in the installed version of the package.

.. tip::

    Do not forget to rerun the editable install every time you recreate your Python
    environment.

.. tip::

    For a more sophisticated setup where versions are managed via tags on the
    repository, check out `setuptools_scm <https://github.com/pypa/setuptools_scm>`_.


Further Reading
---------------

- You can find more examples for structuring a research project in
  :doc:`../how_to_guides/bp_templates_and_projects`.
