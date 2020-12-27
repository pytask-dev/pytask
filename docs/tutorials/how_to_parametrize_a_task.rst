How to parametrize a task
=========================

Often, you want to define a task which should be repeated over a range of inputs. pytask
allows to parametrize task functions to accomplish this behavior.

An example
----------

Let us focus on a simple example. In this setting, we want to define a task which
receives a number and saves it to a file. This task should be repeated for the numbers
from 0 to 2.

First, we write the task for one number.

.. code-block:: python

    import pytask


    @pytask.mark.produces("0.txt")
    def task_save_number(produces, i=0):
        produces.write_text(str(i))

In the next step, we parametrize the task by varying ``i``.

.. code-block:: python

    @pytask.mark.parametrize("produces, i", [("0.txt", 0), ("1.txt", 1), ("2.txt", 2)])
    def task_save_number(produces, i):
        produces.write_text(str(i))

The parametrize decorator receives two arguments. The first argument is ``produces, i``
- the signature. It is a comma-separated string where each value specifies the name of a
task function argument.

.. seealso::

    The signature is explained in detail :ref:`below <parametrize_signature>`.

The second argument of the parametrize decorator is an iterable. Each entry in iterable
has to provide one value for each argument name in the signature.

Putting all together, the task is executed three times and each run the path from the
list is mapped to the argument ``produces`` and ``i`` receives the number.

.. important::

    If you use ``produces`` or ``depends_on`` in the signature of the parametrize
    decorator, the values are automatically treated as if they were attached to the
    function with ``@pytask.mark.depends_on`` or ``@pytask.mark.produces``. For
    example, the generated task in which ``i = 1`` is identical to

    .. code-block:: python

        @pytask.mark.produces("1.txt")
        def task_save_number(produces, i=1):
            produces.write_text(str(i))


Un-parametrized dependencies
----------------------------

To specify a dependency which is the same for all parametrizations, add it with
``pytask.mark.depends_on``.

.. code-block:: python

    @pytask.mark.depends_on(Path("additional_text.txt"))
    @pytask.mark.parametrize("produces, i", [("0.txt", 0), ("1.txt", 1), ("2.txt", 2)])
    def task_save_number(depends_on, produces, i):
        additional_text = depends_on.read_text()
        produces.write_text(additional_text + str(i))


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


Further reading
---------------

- :doc:`../how_to_guides/how_to_extend_parametrizations`.
