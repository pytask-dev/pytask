How to write a task
===================

A task is a function and is detected if the module and the function name are prefixed
with ``task_``. Here is an example.

.. code-block:: python

    # Content of task_hello.py.

    import pytask


    @pytask.mark.produces("hello_earth.txt")
    def task_hello_earth(produces):
        produces.write_text("Hello, earth!")

To execute the task, type the following command on the command-line

.. code-block::

    $ pytask task_hello.py
    =============================== Start pytask session ===============================
    Platform: linux -- Python 3.x.y, pytask 0.x.y, pluggy 0.x.y
    Root: xxx
    Collected 1 task(s).

    s
    ============================ 1 succeeded in 1 second(s) ============================

Executing

.. code-block:: bash

    $ pytask

would collect all tasks in the current working directory and in all folders below.
