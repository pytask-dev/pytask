How to specify a task - Part 1
==============================

This section shows you the first part of how to specify tasks. We will create a simple
task which writes ``"Hello, Earth!"`` to a file. The second task will follow later and
depend on the result of the first task.

Tasks in Waf are defined in ``wscript`` files. A file might look like this:

.. code-block:: python

    # Content of wscript.


    def build(ctx):

        ctx(
            features="run_py_script",
            source="hello_earth.py",
            target=ctx.path_to(ctx, "BLD", "hello_earth.txt"),
            name="hello_earth",
        )

The executed script ``hello_earth.py`` contains the following code.

.. code-block:: python

    # Content of hello_earth.py.

    from src.config import BLD

    if __name__ == "__main__":
        (BLD / "hello_earth.txt").write_text("Hello, earth!")

Tasks with pytask are defined as functions similar to pytest test functions. The name of
the functions and the modules are both prefixed with ``task_``. Here is the
corresponding function:

.. code-block:: python
    :linenos:

    # Content of task_hello.py.

    import pytask
    from src.config import BLD  # pathlib.Path to build directory.


    @pytask.mark.produces(BLD / "hello_earth.txt")
    def task_hello_earth(produces):
        produces.write_text("Hello, earth!")

Let us step through the function line by line.

* In line 3, import pytask.

* In line 4, the path to the build directory is imported from a configuration file.

* In line 7, apply the ``pytask.mark.produces`` decorator to the function to declare
  that the task produces a file.

* In line 8, ``produces`` is used as a function argument which receives the value of the
  decorator. This is for convenience and to declare the path only once and completely
  optional.

* In line 9, some text is saved to the file.
