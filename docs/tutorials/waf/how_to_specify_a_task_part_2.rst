How to specify a task - Part 2
==============================

Now, we are going to specify a second task which depends on the first task. It will read
the content  in ``hello_earth.txt``, add ``"Hello, Moon!"``, and write the text to
``hello_moon.txt``.

The ``wscript`` for the second tasks contains the following code.

.. code-block:: python

    # Content of wscript


    def build(ctx):

        ctx(
            features="run_py_script",
            source="hello_moon.py",
            deps=ctx.path_to(ctx, "BLD", "hello_earth.txt"),
            targets=ctx.path_to(ctx, "BLD", "hello_moon.txt"),
            name="hello_moon",
        )

The same specification for the second task with pipeline is

.. code-block:: yaml

    # Content of tasks.yaml

    hello_moon:                                            # 1. ID of the task
      template: hello_moon.py                              # 2. executable script
      depends_on: {{ build_directory }}/hello_earth.txt    # 3. dependency
      produces: {{ build_directory }}/hello_moon.txt       # 4. target

As a bonus, it is sometimes easier to declare dependencies by referencing the id of the
required task. The specification changes to

.. code-block:: yaml

    hello_moon:
      ...
      depends_on: hello_earth
      ...

The id ``hello_earth`` is replaced with the path to the product of the declared task.
