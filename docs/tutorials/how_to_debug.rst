How to debug
============

Whenever you encounter an error in one of your tasks, pytask offers multiple ways which
help you to gain more information on the root cause.

Through quick and easy feedback you are more productive and gain more confidence in your
code.


Tracebacks
----------

You can enrich the display of tracebacks by showing local variables in each stack frame.
Just execute pytask with

.. code-block:: console

    $ pytask --show-locals


Debugging
---------

Running

.. code-block:: console

    $ pytask --pdb

enables the post-mortem debugger. Whenever an exception is raised inside a task, the
prompt will enter the debugger enabling you to discover the source of the exception.

.. seealso::

    :doc:`A following tutorial <how_to_select_tasks>` shows you how to run only one or a
    subset of tasks which can be combined with the debug mode.

.. tip::

    Instead of Python's :mod:`pdb`, use `pdb++ <https://github.com/pdbpp/pdbpp>`_ which
    is more convenient, colorful, and has some useful features like the `sticky mode
    <https://github.com/pdbpp/pdbpp#sticky-mode>`_.


Tracing
-------

If you want to enter the debugger at the start of every task, use

.. code-block:: console

    $ pytask --trace


Custom debugger
---------------

If you want to use your custom debugger, make sure it is importable and use
:option:`pytask build --pdbcls`. Here, we change the standard ``pdb`` debugger to
IPython's implementation.

.. code-block:: console

    $ pytask --pdbcls=IPython.terminal.debugger:TerminalPdb
