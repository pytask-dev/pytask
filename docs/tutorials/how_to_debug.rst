How to debug
============

Debugging
---------

To facilitate debugging, pytask offers two command-line options.

.. code-block:: console

    $ pytask --pdb

enables the post-mortem debugger. Whenever an exception is raised inside a task, the
prompt will enter the debugger.

.. tip::

    Instead of Python's :mod:`pdb`, use `pdb++ <https://github.com/pdbpp/pdbpp>`_ which
    is more convenient, colorful has some useful features like the `sticky mode
    <https://github.com/pdbpp/pdbpp#sticky-mode>`_.


Tracing
-------

If you want to enter the debugger at the start of every task, use

.. code-block:: console

    $ pytask --trace

If you want to use your custom debugger, make sure it is importable and use
:option:`pytask build --pdbcls`. Here, we change from the standard ``pdb`` debugger to
IPython's implementation.

.. code-block:: console

    $ pytask --pdbcls=IPython.terminal.debugger:TerminalPdb
