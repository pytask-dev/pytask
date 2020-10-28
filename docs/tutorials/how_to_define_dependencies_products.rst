How to define dependencies and products
=======================================

Task have dependencies and products. Both can be attached to a task function with
decorators. This is necessary so that pytask knows when a task is able to run, needs to
be run again or has produced the desired outcome.

Let us have a look at some examples.


Products
--------

We take the task from the previous tutorial.

.. code-block:: python

    import pytask


    @pytask.mark.produces("hello_earth.txt")
    def task_hello_earth(produces):
        produces.write_text("Hello, earth!")

The ``@pytask.mark.produces`` decorator attaches a product to a task. The string
``"hello_earth.txt"`` is converted to a :class:`pathlib.Path`.

.. note::

    If you do not know about :mod:`pathlib` check out [1]_ and [2]_. The module is very
    useful to handle paths conveniently and cross-platform.

.. important::

    Here are the rules to parse a path.

    1. Paths can either be strings or :class:`pathlib.Path`.
    2. A string is converted to :class:`pathlib.Path`.
    3. If the path is relative, it is assumed to be relative to the directory where the
       task is defined.


Dependencies
------------

Most tasks have dependencies. Similar to products, you can use the
``@pytask.mark.depends_on`` decorator to attach a dependency to a task.

.. code-block:: python

    @pytask.mark.depends_on("text.txt")
    @pytask.mark.produces("bold_text.txt")
    def task_make_text_bold(depends_on, produces):
        text = depends_on.read_text()
        bold_text = f"**{text}**"
        produces.write_text(bold_text)


Optional usage in signature
---------------------------

As seen before, if you have a task with products (or dependencies), you can use
``produces`` (``depends_on``) as a function argument and receive the path or a
dictionary of paths inside the functions. It helps to avoid repetition.


Multiple dependencies and products
----------------------------------

Most tasks have multiple dependencies or products. The easiest way to attach multiple
dependencies or products to a task is to pass a :class:`list`, :class:`tuple` or other
iterator to the decorator which contains :class:`str` or :class:`pathlib.Path`.

.. code-block:: python

    @pytask.mark.depends_on(["text_1.txt", "text_2.txt"])
    def task_example(depends_on):
        pass

The function argument ``depends_on`` or ``produces`` becomes a dictionary where keys are
the positions in the list and values are :class:`pathlib.Path`.

.. code-block:: python

    depends_on = {0: Path("text_1.txt"), 1: Path("text_2.txt")}

Why dictionaries and not lists? First, dictionaries with positions as keys behave very
similar to lists and conversion between both is easy.

Secondly, dictionaries allow to access paths to dependencies and products via labels
which is preferred over positional access when tasks become more complex and the order
changes.

To assign labels to dependencies or products, pass a dictionary or a list of tuples with
the name in the first and the path in the second position to the decorator. For example,

.. code-block:: python

    @pytask.mark.depends_on({"first": "text_1.txt", "second": "text_2.txt"})
    @pytask.mark.produces("out.txt")
    def task_example(depends_on, produces):
        text = depends_on["first"].read_text() + " " + depends_on["second"].read_text()
        produces.write_text(text)

or with tuples

.. code-block:: python

    @pytask.mark.depends_on([("first", "text_1.txt"), ("second", "text_2.txt")])
    def task_example():
        ...


Multiple decorators
-------------------

You can also attach multiple decorators to a function which will be merged into a single
dictionary. This might help you to group certain dependencies and apply them to multiple
tasks.

.. code-block:: python

    common_dependencies = ["text_1.txt", "text_2.txt"]


    @pytask.mark.depends_on(common_dependencies)
    @pytask.mark.depends_on("text_3.txt")
    def task_example():
        ...


.. rubric:: References

.. [1] The official documentation for :mod:`pathlib`.
.. [2] A guide for pathlib at `RealPython <https://realpython.com/python-pathlib/>`_.
