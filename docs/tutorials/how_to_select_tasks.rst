How to select tasks
===================

If you want to run only a subset of tasks, there exist multiple options.


Paths
-----

You can run all tasks in one file or one directory by passing the corresponding path to
pytask. The same can be done for multiple paths.

.. code-block:: bash

    $ pytask src/task_1.py

    $ pytask src

    $ pytask src/task_1.py src/task_2.py


Markers
-------

If you assign markers to task functions, you can use marker expressions to select tasks.
For example, here is a task with the ``wip`` marker which indicates work-in-progress.

.. code-block:: python

    @pytask.mark.wip
    def task_1():
        pass

To execute only tasks with the ``wip`` marker, use

.. code-block:: bash

    $ pytask -m wip

You can pass more complex expressions to ``-m`` by using multiple markers and ``and``,
``or``, ``not``, and brackets (``()``). The following pattern selects all tasks which
belong to the data management, but not the ones which produce plots and plots produced
for the analysis.

.. code-block:: bash

    $ pytask -m "(data_management and not plots) or (analysis and plots)"


Expressions
-----------

General
~~~~~~~

Expressions are similar to markers and offer the same syntax but target the task ids.
Assume you have the following tasks.

.. code-block:: python

    def task_1():
        pass


    def task_2():
        pass


    def task_12():
        pass

Then,

.. code-block:: bash

    $ pytask -k 1

will execute the first and third task and

.. code-block:: bash

    $ pytask -k "1 and not 2"

executes only the first task.

To execute a single task, say ``task_run_this_one`` in ``task_example.py``, use

.. code-block:: bash

    $ pytask -k task_example.py::task_run_this_one


.. _how_to_select_tasks_parametrization:

Parametrization
~~~~~~~~~~~~~~~

If you have a task which is parametrized, you can select individual parametrizations.

.. code-block:: python

    @pytask.mark.parametrize("i", range(2))
    def task_parametrized(i):
        pass

To run the task where ``i = 1``, type

.. code-block:: bash

    $ pytask -k task_parametrized[1]

The general idea is that booleans, floats, integers, and strings are used in the task id
as they are, but all other Python objects like tuples are replaced with a combination of
the argument name and an iteration counter. Multiple arguments are separated via dashes.
