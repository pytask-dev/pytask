How to debug
============

To facilitate debugging, pytask offers two command-line options.

.. code-block:: bash

    $ pytask --pdb

enables the post-mortem debugger. Whenever an exception is raised inside a task, the
prompt will enter the debugger.

.. note::

    For a better debugging experience, test `pdb++ <https://github.com/pdbpp/pdbpp>`_
    and try out the `sticky mode <https://github.com/pdbpp/pdbpp#sticky-mode>`_.

If you want to enter the debugger at the start of every task, use

.. code-block:: bash

    $ pytask --trace
