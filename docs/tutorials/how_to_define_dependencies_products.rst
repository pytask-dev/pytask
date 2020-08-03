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


Optional usage in signature
---------------------------

As seen before, if you have a task with products (or dependencies), you can use
``produces`` (``depends_on``) as a function argument and receive the path or list of
paths inside the functions. It helps to avoid repetition.


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


Multiple dependencies and products
----------------------------------

If you have multiple dependencies or products, pass a list to the decorator. Inside the
function you receive a list of :class:`pathlib.Path` as well.

.. code-block:: python

    @pytask.mark.depends_on(["text_a.txt", "text_b.txt"])
    @pytask.mark.produces(["bold_text_a.txt", "bold_text_b.txt"])
    def task_make_text_bold(depends_on, produces):
        for dependency, product in zip(depends_on, produces):
            text = dependency.read_text()
            bold_text = f"**{text}**"
            product.write_text(bold_text)

The last task is overly complex since it is the same operation performed for two
independent dependencies and products. There must be a better way |tm|, right? Check out
the :doc:`tutorial on parametrization <how_to_parametrize_a_task>`.

.. |tm| unicode:: U+2122


.. rubric:: References

.. [1] The official documentation for :mod:`pathlib`.
.. [2] A guide for pathlib at `RealPython <https://realpython.com/python-pathlib/>`_.
