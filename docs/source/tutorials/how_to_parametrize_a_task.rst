How to parametrize a task
=========================

Often, you want to define a task which should be repeated over a range of inputs. pytask
allows to parametrize task functions to accomplish this behavior.

.. seealso::

    If you want to know more about best practices for parametrizations, check out this
    :doc:`guide <../how_to_guides/bp_parametrizations>` after you made yourself familiar
    this tutorial.


An example
----------

We reuse the previous example of a task which generates random data and repeat the same
operation over a number of seeds to receive multiple, reproducible samples.

First, we write the task for one seed.

.. code-block:: python

    import numpy as np
    import pytask


    @pytask.mark.produces(BLD / "data_0.pkl")
    def task_create_random_data(produces):
        np.random.seed(0)
        ...

In the next step, we repeat the same task over the numbers 0, 1, and 2 and pass them to
the ``seed`` argument. We also vary the name of the produced file in every iteration.

.. code-block:: python

    @pytask.mark.parametrize(
        "produces, seed",
        [(BLD / "data_0.pkl", 0), (BLD / "data_1.pkl", 1), (BLD / "data_2.pkl", 2)],
    )
    def task_create_random_data(produces):
        np.random.seed(0)
        ...

The parametrize decorator receives two arguments. The first argument is ``"produces,
seed"`` - the signature. It is a comma-separated string where each value specifies the
name of a task function argument.

.. seealso::

    The signature is explained in detail :ref:`below <parametrize_signature>`.

The second argument of the parametrize decorator is a list (or any iterable) which has
as many elements as there are iterations over the task function. Each element has to
provide one value for each argument name in the signature - two in this case.

Putting all together, the task is executed three times and each run the path from the
list is mapped to the argument ``produces`` and ``seed`` receives the seed.

.. note::

    If you use ``produces`` or ``depends_on`` in the signature of the parametrize
    decorator, the values are handled as if they were attached to the function with
    ``@pytask.mark.depends_on`` or ``@pytask.mark.produces``.

Un-parametrized dependencies
----------------------------

To specify a dependency which is the same for all parametrizations, add it with
``pytask.mark.depends_on``.

.. code-block:: python

    @pytask.mark.depends_on(SRC / "common_dependency.file")
    @pytask.mark.parametrize(
        "produces, seed",
        [(BLD / "data_0.pkl", 0), (BLD / "data_1.pkl", 1), (BLD / "data_2.pkl", 2)],
    )
    def task_create_random_data(produces):
        np.random.seed(0)
        ...


.. _parametrize_signature:

The signature
-------------

The signature can be passed in three different formats.

1. The signature can be a comma-separated string like an entry in a csv table. Note that
   white-space is stripped from each name which you can use to separate the names for
   readability. Here are some examples:

   .. code-block:: python

       "single_argument"
       "first_argument,second_argument"
       "first_argument, second_argument"

2. The signature can be a tuple of strings where each string is one argument name. Here
   is an example.

   .. code-block:: python

       ("first_argument", "second_argument")

3. Finally, it is also possible to use a list of strings.

   .. code-block:: python

       ["first_argument", "second_argument"]


.. _how_to_parametrize_a_task_the_id:

The id
------

Every task has a unique id which can be used to :doc:`select it <how_to_select_tasks>`.
The normal id combines the path to the module where the task is defined, a double colon,
and the name of the task function. Here is an example.

.. code-block::

    ../task_example.py::task_example

This behavior would produce duplicate ids for parametrized tasks. Therefore, there exist
multiple mechanisms to produce unique ids.


Auto-generated ids
~~~~~~~~~~~~~~~~~~

To avoid duplicate task ids, the ids of parametrized tasks are extended with
descriptions of the values they are parametrized with. Booleans, floats, integers and
strings enter the task id directly. For example, a task function which receives four
arguments, ``True``, ``1.0``, ``2``, and ``"hello"``, one of each dtype, has the
following id.

.. code-block::

    task_example.py::task_example[True-1.0-2-hello]

Arguments with other dtypes cannot be easily converted to strings and, thus, are
replaced with a combination of the argument name and the iteration counter.

For example, the following function is parametrized with tuples.

.. code-block:: python

    @pytask.mark.parametrized("i", [(0,), (1,)])
    def task_example(i):
        pass

Since the tuples are not converted to strings, the ids of the two tasks are

.. code-block::

    task_example.py::task_example[i0]
    task_example.py::task_example[i1]


.. _how_to_parametrize_a_task_convert_other_objects:

Convert other objects
~~~~~~~~~~~~~~~~~~~~~

To change the representation of tuples and other objects, you can pass a function to the
``ids`` argument of the :func:`~_pytask.parametrize.parametrize` decorator. The function
is called for every argument and may return a boolean, number, or string which will be
integrated into the id. For every other return, the auto-generated value is used.

To get a unique representation of a tuple, we can use the hash value.

.. code-block:: python

    def tuple_to_hash(value):
        if isinstance(value, tuple):
            return hash(a)


    @pytask.mark.parametrized("i", [(0,), (1,)], ids=tuple_to_hash)
    def task_example(i):
        pass

This produces the following ids:

.. code-block::

    task_example.py::task_example[3430018387555]  # (0,)
    task_example.py::task_example[3430019387558]  # (1,)


.. _ids:

User-defined ids
~~~~~~~~~~~~~~~~

Instead of a function, you can also pass a list or another iterable of id values via
``ids``.

This code

.. code-block:: python

    @pytask.mark.parametrized("i", [(0,), (1,)], ids=["first", "second"])
    def task_example(i):
        pass

produces these ids

.. code-block::

    task_example.py::task_example[first]  # (0,)
    task_example.py::task_example[second]  # (1,)

This is arguably the easiest way to change the representation of many objects at once
while also producing ids which are easy to remember and type.
