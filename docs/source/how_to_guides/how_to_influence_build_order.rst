How to influence the build order
================================

.. important::

    This guide shows how to influence the order in which tasks are executed. The feature
    should be treated with caution since it might make projects work whose dependencies
    and products are not fully specified.

You can influence the order in which tasks are executed by assigning preferences to
tasks. Use ``pytask.mark.try_first`` to execute a task as early as possible and
``pytask.mark.try_last`` to defer execution.

.. note::

    For more background, tasks, dependencies and products form a directed acyclic graph
    (DAG). A `topological ordering <https://en.wikipedia.org/wiki/Topological_sorting>`_
    determines the order in which tasks are executed such that tasks are not run until
    their predecessors have been executed. The ordering is not unique and instead of a
    random ordering, an ordering is chosen which is compatible with the preferences.
    Among multiple tasks which should all be preferred or delayed, a random task is
    chosen.

As an example, here are two tasks where the decorator ensures that the output of the
second task is always shown before the output of the first task.

.. code-block:: python

    # Content of task_example.py

    import pytask


    def task_first():
        print("I'm second.")


    @pytask.mark.try_first
    def task_second():
        print("I'm first.")


The execution yields (use ``-s`` to make the output visible in the terminal)

.. code-block:: console

    $ pytask -s task_example.py
    ========================= Start pytask session =========================
    Platform: win32 -- Python 3.x.x, pytask 0.x.x, pluggy 0.x.x
    Root: x
    Collected 2 tasks.

    I'm first.
    .I'm second.
    .
    ========================= 2 succeeded in 0.04s =========================

Replacing ``pytask.mark.try_first`` with ``pytask.mark.try_last`` yields

.. code-block:: python

    # Content of task_example.py

    import pytask


    def task_first():
        print("I'm second.")


    @pytask.mark.try_last
    def task_second():
        print("I'm first.")

and

.. code-block:: console

    $ pytask -s task_example.py
    ========================= Start pytask session =========================
    Platform: win32 -- Python 3.x.x, pytask 0.x.x, pluggy 0.x.x
    Root: x
    Collected 2 tasks.

    I'm second.
    .I'm first.
    .
    ========================= 2 succeeded in 0.03s =========================
