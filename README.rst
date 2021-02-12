.. raw:: html

    <img src="docs/_static/images/pytask_w_text.png" alt="pytask" width="50%">

------

.. start-badges

.. image:: https://anaconda.org/pytask/pytask/badges/version.svg
    :target: https://anaconda.org/pytask/pytask

.. image:: https://anaconda.org/pytask/pytask/badges/platforms.svg
    :target: https://anaconda.org/pytask/pytask

.. image:: https://readthedocs.org/projects/pytask-dev/badge/?version=latest
    :target: https://pytask-dev.readthedocs.io/en/latest

.. image:: https://github.com/pytask-dev/pytask/workflows/Continuous%20Integration%20Workflow/badge.svg?branch=main
    :target: https://github.com/pytask-dev/pytask/actions?query=branch%3Amain

.. image:: https://codecov.io/gh/pytask-dev/pytask/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/pytask-dev/pytask

.. image:: https://results.pre-commit.ci/badge/github/pytask-dev/pytask/main.svg
    :target: https://results.pre-commit.ci/latest/github/pytask-dev/pytask/main
    :alt: pre-commit.ci status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


.. end-badges


.. start-features

In its highest aspirations, pytask tries to be pytest as a build system. It's main
purpose is to facilitate reproducible research by automating workflows in research
projects. Its features include:

- **Automatic discovery of tasks.**

- **Lazy evaluation.** If a task, its dependencies, and its products have not changed,
  do not execute it.

- **Debug mode.** `Jump into the debugger
  <https://pytask-dev.readthedocs.io/en/latest/tutorials/how_to_debug.html>`_ if a task
  fails, get feedback quickly, and be more productive.

- **Select tasks via expressions.** Run only a subset of tasks with `expressions and
  marker expressions
  <https://pytask-dev.readthedocs.io/en/latest/tutorials/how_to_select_tasks.html>`_
  known from pytest.

- **Easily extensible with plugins**. pytask's architecture is based on `pluggy
  <https://pluggy.readthedocs.io/en/latest/>`_, a plugin management framework, so that
  you can adjust pytask to your needs. Plugins are, for example, available for
  `parallelization <https://github.com/pytask-dev/pytask-parallel>`_, `LaTeX
  <https://github.com/pytask-dev/pytask-latex>`_, `R
  <https://github.com/pytask-dev/pytask-r>`_, and `Stata
  <https://github.com/pytask-dev/pytask-stata>`_. Read `here
  <https://pytask-dev.readthedocs.io/en/latest/tutorials/how_to_use_plugins.html>`_ how
  you can use plugins.

.. end-features


Why do I need a build system?
-----------------------------

Read the `section in the documentation <https://pytask-dev.readthedocs.io/en/latest/
explanations/why_do_i_need_a_build_system.html>`_ if you do not know or are not
convinced that you need a build system.


Installation
------------

.. start-installation

pytask is available on `Anaconda.org <https://anaconda.org/pytask/pytask>`_. Install the
package with

.. code-block:: console

    $ conda config --add channels conda-forge --add channels pytask
    $ conda install pytask

.. end-installation

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

Here are some details:

- Dependencies and products of a task are tracked via markers. For dependencies use
  ``@pytask.mark.depends_on`` and for products use ``@pytask.mark.produces``. Use
  strings and ``pathlib.Path`` to specify the location. Pass multiple dependencies or
  products as a list.
- With ``produces`` (and ``depends_on``) as function arguments, you get access to the
  dependencies and products inside the function via ``pathlib.Path`` objects. Here,
  ``produces`` holds the path to ``"hello_earth.txt"``.

To execute the task, type the following command on the command-line

.. code-block:: console

    $ pytask
    ========================= Start pytask session =========================
    Platform: linux -- Python 3.x.y, pytask 0.x.y, pluggy 0.x.y
    Root: xxx
    Collected 1 task(s).

    .
    ====================== 1 succeeded in 1 second(s) ======================


Demo
----

The demo walks you through the following steps.

1. Write an executable script which produces a text file like you would normally do
   without pytask.
2. Rewrite the script to a pytask task.
3. Execute the task.
4. Add a task which produces a second text file and another task which merges both text
   files.
5. Execute all three tasks.

.. image:: https://github.com/pytask-dev/misc/raw/main/gif/workflow.gif


Documentation
-------------

The documentation can be found under https://pytask-dev.readthedocs.io/en/latest with
`tutorials <https://pytask-dev.readthedocs.io/en/latest/tutorials/index.html>`_ and
guides for `best practices
<https://pytask-dev.readthedocs.io/en/latest/how_to_guides/index.html>`_.


Changes
-------

Consult the `release notes <https://pytask-dev.readthedocs.io/en/latest/changes.html>`_
to find out about what is new.
