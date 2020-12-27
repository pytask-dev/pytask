How to make tasks persist
=========================

You are able to create persisting tasks with pytask. It means that if all dependencies
and products exist, the task will not be executed even though a dependency, the task's
source file or a product has changed. Instead, the state of the dependencies, the source
file and the products is updated in the database such that the next execution will skip
the task successfully.

When is this useful?
--------------------

1. You ran a formatter like Black against your project and there are some expensive
   tasks which should not be executed.

2. You want to integrate a task which you have already run elsewhere. Place the
   dependencies and products and the task definition in the correct place and make the
   task persist.


.. caution::

    This feature can corrupt the integrity of your project. Document why you
    have applied the decorator out of consideration for yourself and other contributors.


How to do it?
-------------

To create a persisting task, apply the correct decorator and, et voilà, it is done.

Let us take the second scenario as an example. First, we define the tasks, the
dependency and the product and save everything in the same folder.

.. code-block:: python

    # Content of task_file.py

    import pytask


    @pytask.mark.persist
    @pytask.mark.depends_on("input.md")
    @pytask.mark.produces("output.md")
    def task_make_input_bold(depends_on, produces):
        produces.write_text("**" + depends_on.read_text() + "**")


.. code-block::

    # Content of input.md. Do not copy this line.

    Here is the text.


.. code-block::

    # Content of output.md. Do not copy this line.

    **Here is the text.**


If you run pytask in this folder, you get the following output.

.. code-block:: console

    $ pytask demo
    ========================= Start pytask session =========================
    Platform: win32 -- Python 3.8.5, pytask 0.0.6, pluggy 0.13.1
    Root: xxx/demo
    Collected 1 task(s).

    p
    ====================== 1 succeeded in 1 second(s) ======================

The green p signals that the task persisted. Another execution will show the following.

.. code-block:: console

    $ pytask demo
    ========================= Start pytask session =========================
    Platform: win32 -- Python 3.8.5, pytask 0.0.6, pluggy 0.13.1
    Root: xxx/demo
    Collected 1 task(s).

    s
    ====================== 1 succeeded in 1 second(s) ======================

Now, the task is skipped successfully because nothing has changed compared to the
previous run.
