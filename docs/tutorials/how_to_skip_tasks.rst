How to skip tasks
==================

Tasks are skipped automatically if neither their file nor any of their dependencies have
changed and all products exist.

In addition, you may want pytask to skip tasks either generally or if certain conditions
are fulfilled. Skipping means the task itself and all tasks that depend on it will not
be executed, even if the task file or their dependencies have changed or products are
missing.

This can be useful for example if you are working on a task that creates the dependency
of a long running task and you are not interested in the long running task's product
for the moment. In that case you can simply use ``@pytask.mark.skip`` in front of the
long running task to stop it from running:

.. code-block:: python

    # Content of task_create_dependency.py

    @pytask.mark.produces("dependency_of_long_running_task.md")
    def task_you_are_working_on(produces):
        ...

.. code-block:: python

    # Content of task_long_running.py

    @pytask.mark.skip
    @pytask.mark.depends_on("dependency_of_long_running_task.md")
    def task_that_takes_really_long_to_run(depends_on):


In large projects, you may have many long running tasks that you only want to
execute sporadically, e.g. when you are not working locally but running the project
on a server.

In that case, we recommend using ``@pytask.mark.skip_if`` which lets you supply a
condition and a reason as arguments:


.. code-block:: python

    # Content of a config.py

    NO_LONG_RUNNING_TASKS = True

.. code-block:: python

    # Content of task_create_dependency.py

    @pytask.mark.produces("run_always.md")
    def task_always(produces):
        ...

.. code-block:: python

    # Content of task_long_running.py

    from config import NO_LONG_RUNNING_TASKS
    
    @pytask.mark.skipif(NO_LONG_RUNNING_TASKS, "Skip long-running tasks.")
    @pytask.mark.depends_on("dependency_of_long_running_task.md")
    def task_that_takes_really_long_to_run(depends_on):
        ...
