How to specify a task - Part 2
==============================

Now, we are going to specify a second task which depends on the first task. It will read
the content  in ``hello_earth.txt``, add ``"Hello, Moon!"``, and write the text to
``hello_moon.txt``.

The ``wscript`` for the second tasks contains the following code.

.. code-block:: python

    # Content of wscript.


    def build(ctx):

        ctx(
            features="run_py_script",
            source="hello_moon.py",
            deps=ctx.path_to(ctx, "BLD", "hello_earth.txt"),
            targets=ctx.path_to(ctx, "BLD", "hello_moon.txt"),
            name="hello_moon",
        )

The same specification for the second task with pytask is

.. code-block:: python
    :linenos:

    # Additional content of task_hello.py.


    @pytask.mark.depends_on(BLD, "hello_earth.txt")
    @pytask.mark.produces(BLD, "hello_moon.txt")
    def task_hello_moon(depends_on, produces):
        produces.write_text(depends_on.read_text() + " Hello, moon!")

* In line 3, the dependency of the task is specified in the same way a product is
  declared.

* In line 5, the value of the ``pytask.mark.depends_on`` decorator can also be requested
  inside the task function by using the argument name ``depends_on``.
