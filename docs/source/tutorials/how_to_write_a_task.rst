How to write a task
===================

Starting from the project structure in the :doc:`previous tutorial
<how_to_set_up_a_project>`, this tutorial teaches you how to write your first task.

The task will be defined in ``src/my_project/task_data_preparation.py`` and it will
generate artificial data which will be stored in ``bld/data.pkl``. We will call the
function in the module :func:`task_create_random_data`.

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
    import pandas as pd

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

Now, execute pytask which will automatically collect tasks in the current directory and
subsequent directories.

.. image:: /_static/images/how-to-write-a-task.png

.. important::

    By default, pytask assumes that tasks are functions and both, the function name and
    the module name, must be prefixed with ``task_``.

    Use the configuration value :confval:`task_files` if you prefer a different naming
    scheme for the task modules.
