How to invoke pytask
====================

Entry-points
------------

There are two entry-points to invoke pytask.

1. Use command line interface with

   .. code-block:: console

       $ pytask

   Use the following flags to learn more about pytask and its configuration.

   .. code-block:: console

       $ pytask --version
       $ pytask -h | --help

2. Invoke pytask programmatically with

   .. code-block:: python

       import pytask


       session = pytask.main({"paths": ...})

   Pass command line arguments with their long name and hyphens replaced by underscores
   as keys of the dictionary.


Stopping after the first (or N) failures
----------------------------------------

To stop the build of the project after the first (N) failures use

.. code-block:: console

    $ pytask -x | --stop-after-first-failure  # Stop after the first failure
    $ pytask --max-failures 2                 # Stop after the second failure
