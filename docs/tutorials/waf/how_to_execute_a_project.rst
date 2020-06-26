How to execute a project
========================

To execute the project with Waf, enter

.. code-block:: bash

    $ python waf.py configure build

which will run the tasks sequentially. You can inspect the results in the ``bld``
folder. The corresponding command with pytask is.

.. code-block:: bash

    $ pytask

If you want to clean your project, Waf offers the following command

.. code-block:: bash

    $ python waf.py distclean

pytask does not have such a command. If you separate source and build files strictly
from one another in different folders as explained in :ref:`here
<how_to_set_up_a_project>`, you can use the following commands to delete the build
folder.

.. code-block:: bash

    # Unix
    $ rm -rf bld

    # Windows
    $ rm bld


.. raw:: html

    <div class="d-flex flex-row gs-torefguide">
        <span class="badge badge-info">To beginner's guide</span>

        Find out more about <a href="../beginners_guide/how_to_set_up_a_project.html">
        how to set up a project</a>.
    </div>
