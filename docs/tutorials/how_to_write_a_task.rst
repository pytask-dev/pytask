How to write a task
===================

Starting from the project structure in the :doc:`previous tutorial
<how_to_set_up_a_project>`, you will write your first task.

The task is defined in ``src/task_data_preparation.py`` and produce ``bld/data.pkl``.

.. code-block::

    my_project
    ├───pytask.ini or tox.ini or setup.cfg
    │
    ├───src
    │   ├────config.py
    │   └────task_data_preparation.py
    │
    └───bld
        └────data.pkl


A task is a function and is detected if the module and the function name are prefixed
with ``task_``.

In ``task_data_preparation.py``, we define :func:`task_create_random_data` to create
random data.

.. code-block:: python

    # Content of task_data_preparation.py.

    import pytask
    import numpy as np
    import pandas as np

    from src.config import BLD


    @pytask.mark.produces(BLD / "data.pkl")
    def task_create_random_data(produces):
        x = np.random.normal(loc=5, scale=10, size=1_000)
        y = 2 * x + np.random.standard_normal(1000)
        df = pd.DataFrame({"x": x, "y": y})
        df.to_pickle(produces)

To let pytask track dependencies and products of tasks, you need to use the
``@pytask.mark.produces`` decorator. You learn how to add dependencies and products to a
task in the next :doc:`tutorial <how_to_define_dependencies_products>`.

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
