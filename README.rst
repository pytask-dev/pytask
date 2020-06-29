.. raw:: html

    <img src="docs/_static/images/pytask_w_text.png" alt="pytask"
         width="50%">

------

.. image:: https://anaconda.org/pytask/pytask/badges/version.svg
    :target: https://anaconda.org/pytask/pytask

.. image:: https://anaconda.org/pytask/pytask/badges/platforms.svg
    :target: https://anaconda.org/pytask/pytask

.. image:: https://readthedocs.org/projects/pytask-dev/badge/?version=latest
    :target: https://pytask-dev.readthedocs.io/en/latest

.. image:: https://codecov.io/gh/pytask-dev/pytask/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/pytask-dev/pytask

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


Features
--------

In its highest aspirations, **pytask** tries to be pytest as a build system. Its
features include:

- Automatic discovery of tasks.

- It tracks dependencies and products as well as the source file of a task to evaluate
  whether it needs to be re-executed.

- pytask does not stop if one task fails, but continues execution for all collected
  tasks. Tasks which depend on failed tasks are automatically skipped.

- Easily extensible since its architecture is based on `pluggy
  <https://pluggy.readthedocs.io/en/latest/>`_, a plugin management and hook calling
  framework.


Installation
------------

**pytask** is available on `Anaconda.org <https://anaconda.org/pytask/pytask>`_. Install
the package with

.. code-block:: bash

    $ conda config --add channels conda-forge --add channels pytask
    $ conda install pytask


Usage
-----

A task is a function which is detected if the module and the function name are prefixed
with ``task_``. Here is an example.

.. code-block:: python

    # Content of task_hello.py.

    import pytask


    @pytask.mark.produces("hello_earth.txt")
    def task_hello_earth(produces):
        produces.write_text("Hello, earth!")

Dependencies and products of a task are tracked via markers. For dependencies use
``@pytask.mark.depends_on`` and for products use ``@pytask.mark.produces``.

To execute the task, type the following command on the command-line

.. code-block::

    $ pytask
    =============================== Start pytask session ===============================
    Platform: linux -- Python 3.x.y, pytask 0.x.y, pluggy 0.x.y
    Root: xxx
    Collected 1 task(s).

    s
    ============================ 1 succeeded in 1 second(s) ============================


Documentation
-------------

The documentation can be found under https://pytask-dev.readthedocs.io/en/latest and
tutorials and explanations.


Changes
-------

Consult the `release notes <https://pytask-dev.readthedocs.io/en/latest/changes.html>`_
to find out about what is new.
