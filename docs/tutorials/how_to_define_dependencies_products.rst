How to define dependencies and products
=======================================

Tasks may have dependencies, but they certainly have products. pytask needs the
information to infer the order in which tasks are executed and whether a task must be
executed at all.

The information on dependencies and products can be attached to a task function with
markers. Let us have a look at some examples.


Products
--------

We first focus on products which we have already seen in the previous tutorial. Let us
take a look at the task from the previous tutorial.

.. code-block:: python

    import pytask


    @pytask.mark.produces(BLD / "data.pkl")
    def task_create_random_data(produces):
        ...

The ``@pytask.mark.produces`` marker attaches a product to a task which is in this case
a :class:`pathlib.Path` to file. After the task has finished, pytask will check whether
the file exists.

.. tip::

    If you do not know about :mod:`pathlib` check out [1]_ and [2]_. The module is very
    useful to handle paths conveniently and cross-platform.


Dependencies
------------

Most tasks have dependencies. Similar to products, you can use the
``@pytask.mark.depends_on`` marker to attach a dependency to a task.

.. code-block:: python

    @pytask.mark.depends_on(BLD / "data.pkl")
    @pytask.mark.produces(BLD / "plot.png")
    def task_make_text_bold(depends_on, produces):
        ...


Conversion
----------

Dependencies and products do not have to be absolute paths. If paths are relative, they
are assumed to point to a location relative to the task module.

You can also use absolute and relative paths as strings which obey the same rules as the
:class:`pathlib.Path`.

.. code-block:: python

    @pytask.mark.produces("../bld/data.pkl")
    def task_create_random_data(produces):
        ...

If you use ``depends_on`` or ``produces`` as arguments for the task function, you will
have access to the paths of the targets as :class:`pathlib.Path` even if strings were
used before.


Optional usage in signature
---------------------------

The task function does not need to have ``depends_on`` and ``produces`` as arguments
even though the corresponding markers were used like in the following example.

.. code-block::

    @pytask.mark.produces("../bld/data.pkl")
    def task_create_random_data():
        ...


Multiple dependencies and products
----------------------------------

Most tasks have multiple dependencies or products. The easiest way to attach multiple
dependencies or products to a task is to pass a :class:`dict`, :class:`list` or another
iterator to the marker containing the paths.

.. code-block:: python

    @pytask.mark.produces([BLD / "data_0.pkl", BLD / "data_1.pkl"])
    def task_create_random_data(produces):
        ...

Inside the function, the arguments ``depends_on`` or ``produces`` become a dictionary
where keys are the positions in the list.

.. code-block:: python

    produces = {0: BLD / "data_0.pkl", 1: BLD / "data_1.pkl"}

Why dictionaries and not lists? First, dictionaries with positions as keys behave very
similar to lists and conversion between both is easy.

.. tip::

    Use ``list(produces.values())`` to convert a dictionary to a list.

Secondly, dictionaries use keys instead of positions which is more verbose and
descriptive and does not assume a fixed ordering. Both attributes are especially
desirable in complex projects.

To assign labels to dependencies or products, pass a dictionary. For example,

.. code-block:: python

    @pytask.mark.produces({"first": BLD / "data_0.pkl", "second": BLD / "data_1.pkl"})
    def task_create_random_data(produces):
        ...

.. note::

    Named dependencies and products can also be passed as a list of tuples where the
    first element corresponds to the key and the second to the value See here an example
    with a list of tuples.

    .. code-block:: python

        @pytask.mark.produces([("first", BLD / "data_0.pkl"), ("second", BLD / "data_1.pkl")])
        def task_create_random_data(produces):
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


References
----------

.. [1] The official documentation for :mod:`pathlib`.
.. [2] A guide for pathlib at `RealPython <https://realpython.com/python-pathlib/>`_.
