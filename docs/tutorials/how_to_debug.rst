How to debug
============

To facilitate debugging, pytask offers two command-line options.

.. code-block:: console

    $ pytask --pdb

enables the post-mortem debugger. Whenever an exception is raised inside a task, the
prompt will enter the debugger.

.. note::

    For a better debugging experience, test `pdb++ <https://github.com/pdbpp/pdbpp>`_
    and try out the `sticky mode <https://github.com/pdbpp/pdbpp#sticky-mode>`_.

If you want to enter the debugger at the start of every task, use

.. code-block:: console

    $ pytask --trace

Tracing can have undesired side-effects. If you enter a task with tracing, you can exit
the debugger by continuing or quitting. The latter ends the task without error and might
accidentally mark a task as being successful (if old products of the task already
exist). Re-run the task by deleting a product or re-saving the Python file of the task.
