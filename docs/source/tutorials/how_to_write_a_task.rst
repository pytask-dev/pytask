How to write a task
===================

Starting from the project structure in the :doc:`previous tutorial
<how_to_set_up_a_project>`, this tutorial teaches you how to write your first task.

The task will be defined in ``src/task_data_preparation.py`` and it will generate
artificial data which will be stored in ``bld/data.pkl``. We will call the function in
the module :func:`task_create_random_data`.

.. code-block::

    my_project
    ├───pytask.ini or tox.ini or setup.cfg
    │
    ├───src
    │   └───my_project
    │       ├────config.py
    │       └────task_data_preparation.py
    │
    ├───setup.py
    │
    ├───.pytask.sqlite3
    │
    └───bld
        └────data.pkl

Here, we define the function

.. code-block:: python

    # Content of task_data_preparation.py.

    import pytask
    import numpy as np
    import pandas as np

    from my_project.config import BLD


    @pytask.mark.produces(BLD / "data.pkl")
    def task_create_random_data(produces):
        beta = 2
        x = np.random.normal(loc=5, scale=10, size=1_000)
        epsilon = np.random.standard_normal(1_000)

        y = beta * x + epsilon

        df = pd.DataFrame({"x": x, "y": y})
        df.to_pickle(produces)

To let pytask track the product of the task, you need to use the
``@pytask.mark.produces`` decorator.

.. seealso::

    You learn more about adding dependencies and products to a task in the next
    :doc:`tutorial <how_to_define_dependencies_products>`.

To execute the task, type the following command in your shell.

.. code-block:: console

    $ pytask task_data_preparation.py
    ========================= Start pytask session =========================
    Platform: linux -- Python 3.x.y, pytask 0.x.y, pluggy 0.x.y
    Root: xxx
    Collected 1 task(s).

    .
    ======================= 1 succeeded in 1 second ========================

Executing

.. code-block:: console

    $ pytask

would collect all tasks in the current working directory and in all subsequent folders.

.. important::

    By default, pytask assumes that tasks are functions in modules whose names are both
    prefixed with ``task_``.

    Use the configuration value :confval:`task_files` if you prefer a different naming
    scheme for the task modules.
