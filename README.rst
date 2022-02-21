.. image:: https://raw.githubusercontent.com/pytask-dev/pytask/main/docs/source/_static/images/pytask_w_text.png
    :target: https://pytask-dev.readthedocs.io/en/stable
    :align: center
    :width: 50%
    :alt: pytask

------

.. start-badges

.. image:: https://img.shields.io/pypi/v/pytask?color=blue
    :alt: PyPI
    :target: https://pypi.org/project/pytask

.. image:: https://img.shields.io/pypi/pyversions/pytask
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/pytask

.. image:: https://img.shields.io/conda/vn/conda-forge/pytask.svg
    :target: https://anaconda.org/conda-forge/pytask

.. image:: https://img.shields.io/conda/pn/conda-forge/pytask.svg
    :target: https://anaconda.org/conda-forge/pytask

.. image:: https://img.shields.io/pypi/l/pytask
    :alt: PyPI - License
    :target: https://pypi.org/project/pytask

.. image:: https://readthedocs.org/projects/pytask-dev/badge/?version=latest
    :target: https://pytask-dev.readthedocs.io/en/stable

.. image:: https://img.shields.io/github/workflow/status/pytask-dev/pytask/Continuous%20Integration%20Workflow/main
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
  <https://pytask-dev.readthedocs.io/en/stable/tutorials/how_to_debug.html>`_ if a task
  fails, get feedback quickly, and be more productive.

- **Select tasks via expressions.** Run only a subset of tasks with `expressions and
  marker expressions
  <https://pytask-dev.readthedocs.io/en/stable/tutorials/how_to_select_tasks.html>`_
  known from pytest.

- **Easily extensible with plugins**. pytask is built on top of `pluggy
  <https://pluggy.readthedocs.io/en/latest/>`_, a plugin management framework, which
  allows you to adjust pytask to your needs. Plugins are available for `parallelization
  <https://github.com/pytask-dev/pytask-parallel>`_, `LaTeX
  <https://github.com/pytask-dev/pytask-latex>`_, `R
  <https://github.com/pytask-dev/pytask-r>`_, and `Stata
  <https://github.com/pytask-dev/pytask-stata>`_ and more can be found `here
  <https://github.com/topics/pytask>`_. Read in `this tutorial
  <https://pytask-dev.readthedocs.io/en/stable/tutorials/how_to_use_plugins.html>`_ how
  to use and create plugins with a `cookiecutter
  <https://github.com/pytask-dev/cookiecutter-pytask-plugin>`_.

.. end-features


Installation
------------

.. start-installation

pytask is available on `PyPI <https://pypi.org/project/pytask>`_ and on `Anaconda.org
<https://anaconda.org/conda-forge/pytask>`_. Install the package with

.. code-block:: console

    $ pip install pytask

or

.. code-block:: console

    $ conda install -c conda-forge pytask

Color support is automatically available on non-Windows platforms. On Windows, please,
use `Windows Terminal <https://github.com/microsoft/terminal>`_ which can be, for
example, installed via the `Microsoft Store <https://aka.ms/terminal>`_.

To quickly set up a new project, use the `cookiecutter-pytask-project
<https://github.com/pytask-dev/cookiecutter-pytask-project>`_ template or start from
`other templates or example projects
<https://pytask-dev.readthedocs.io/en/stable/how_to_guides/bp_templates_and_projects.html>`_.

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
  products as a list or a dictionary for positional or key-based access.
- With ``produces`` (and ``depends_on``) as function arguments, you get access to the
  dependencies and products inside the function via ``pathlib.Path`` objects. Here,
  ``produces`` holds the path to ``"hello_earth.txt"``.

To execute the task, enter ``pytask`` on the command-line

.. image:: https://github.com/pytask-dev/pytask/raw/main/docs/source/_static/images/readme.png


Documentation
-------------

The documentation can be found under https://pytask-dev.readthedocs.io/en/stable with
`tutorials <https://pytask-dev.readthedocs.io/en/stable/tutorials/index.html>`_ and
guides for `best practices
<https://pytask-dev.readthedocs.io/en/stable/how_to_guides/index.html>`_.


Changes
-------

Consult the `release notes <https://pytask-dev.readthedocs.io/en/stable/changes.html>`_
to find out about what is new.


License
-------

pytask is distributed under the terms of the `MIT license <LICENSE>`_.


Acknowledgment
--------------

The license also includes a copyright and permission notice from pytest since some
modules, classes, and functions are copied from pytest. Not to mention how pytest has
inspired the development of pytask in general. Without the amazing work of Holger Krekel
and pytest's many contributors, this project would not have been possible. Thank you!


Citation
--------

If you rely on pytask to manage your research project, please cite it with the following
key to help others to discover the tool.

.. code-block::

    @Unpublished{Raabe2020,
        Title  = {A Python tool for managing scientific workflows.},
        Author = {Tobias Raabe},
        Year   = {2020},
        Url    = {https://github.com/pytask-dev/pytask}
    }
