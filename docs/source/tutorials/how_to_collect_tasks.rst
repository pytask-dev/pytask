How to collect tasks
====================

If you want to inspect your project and see a summary of all the tasks in the projects,
you can use the :program:`pytask collect` command.

For example, let us take the following task

.. code-block:: python

    # Content of task_module.py

    import pytask


    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_write_file(depends_on, produces):
        produces.write_text(depends_on.read_text())


Now, running :program:`pytask collect` will produce the following output.

.. code-block:: console

    $ pytask collect
    ========================= Start pytask session =========================
    Platform: linux -- Python 3.x.y, pytask 0.x.y, pluggy 0.x.y
    Root: xxx
    Collected 1 task(s).

    <Module /.../task_module.py>
      <Function task_write_file>

    ========================================================================

If you want to have more information regarding dependencies and products of the task,
append the ``--nodes`` flag.

.. code-block:: console

    $ pytask collect
    ========================= Start pytask session =========================
    Platform: linux -- Python 3.x.y, pytask 0.x.y, pluggy 0.x.y
    Root: xxx
    Collected 1 task(s).

    <Module /.../task_module.py>
      <Function task_write_file>
        <Dependency /.../in.txt>
        <Product /.../out.txt>

    ========================================================================

To restrict the set of tasks you are looking at, use markers, expression and ignore
patterns as usual.


Further reading
---------------

- :program:`pytask collect` in :doc:`../reference_guides/command_line_interface`.
