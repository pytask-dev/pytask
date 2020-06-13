How to specify a task - Part 1
==============================

This section shows you the first part of how to specify tasks. We will create a simple
task which writes ``"Hello, Earth!"`` to a file. The second task will follow later and
depend on the result of the first task.

Tasks in Waf are defined in ``wscript`` files. A file might look like this:

.. code-block:: python

    # Content of wscript


    def build(ctx):

        ctx(
            features="run_py_script",
            source="hello_earth.py",
            target=ctx.path_to(ctx, "BLD", "hello_earth.txt"),
            name="hello_earth",
        )

In contrast, tasks for pipeline are defined in ``.yaml`` files, not ``.yml``. The same
task for pipeline looks like this:

.. code-block:: yaml

    # Content of tasks.yaml

    hello_earth:                                            # 1. id of the task
      template: hello_earth.py                              # 2. executable script
      produces: {{ build_directory }}/hello_earth.txt       # 3. target

First of all, a collection of tasks is a dictionary where the keys are the names and the
values are the specification of the tasks.

1. In this case, the task's name or id is ``hello_earth``. The ids of the tasks have to
   be unique within the project.

Then, we take a look at the value of the dictionary or specification which is a
dictionary itself.

2. The key ``template`` is used to refer to the executable script. It is also the only
   mandatory information.

3. ``produces`` can be used to specify a dependency of a task. Similar to
   ``ctx.path_to()`` which allows to shorten paths by using aliases, ``{{
   build_directory }}`` will be replaced by the path defined in ``.pipeline.yaml`` which
   is ``bld`` by default.
