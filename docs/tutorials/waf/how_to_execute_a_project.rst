How to execute a project
========================

To execute the project with Waf, enter

.. code-block:: bash

    $ python waf.py configure build

which will run the tasks sequentially. You can inspect the results in the ``bld``
folder. If you want to clean the project, run

.. code-block:: bash

    $ python waf.py distclean

Similar commands are available for pipeline. Remember that the ``configure`` step is
unnecessary and, thus, we have the following two commands.

.. code-block:: bash

    $ pipeline build
    $ pipeline clean
