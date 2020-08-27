How to write a task
===================

A task is a function and is detected if the module and the function name are prefixed
with ``task_``.

The following task :func:`task_hello_earth` lies in ``task_hello.py``. Its purpose is to
save the string ``"Hello, earth!"`` to a file called ``hello_earth.txt``.

.. code-block:: python

    # Content of task_hello.py.

    import pytask


    @pytask.mark.produces("hello_earth.txt")
    def task_hello_earth(produces):
        produces.write_text("Hello, earth!")

To let pytask track dependencies and products of tasks, you need to use the
``@pytask.mark.produces`` decorator. You learn how to add dependencies and products to a
task in the next :doc:`tutorial <how_to_define_dependencies_products>`.

To execute the task, type the following command on the command-line

.. code-block::

    $ pytask task_hello.py
    ========================= Start pytask session =========================
    Platform: linux -- Python 3.x.y, pytask 0.x.y, pluggy 0.x.y
    Root: xxx
    Collected 1 task(s).

    .
    ====================== 1 succeeded in 1 second(s) ======================

Executing

.. code-block:: bash

    $ pytask

would collect all tasks in the current working directory and in all folders below.
