How to parametrize a task
=========================

You want to define a task which should be repeated over a range of inputs? Parametrize
your task function!

.. important::

    If you are looking for information on the old way to parametrizations with the
    :func:`@pytask.mark.parametrize <_pytask.parametrize.parametrize>` decorator, you
    can find it :doc:`here <../how_to_guides/how_to_parametrize_a_task_the_old_way>`.

.. seealso::

    If you want to know more about best practices for parametrizations, check out this
    :doc:`guide <../how_to_guides/bp_parametrizations>` after you made yourself familiar
    with this tutorial.


An example
----------

We reuse the previous example of a task which generates random data and repeat the same
operation over a number of seeds to receive multiple, reproducible samples.

Apply the :func:`@pytask.mark.task <_pytask.task_utils.task>` decorator, loop over the
function and supply values to the function.

.. code-block:: python

    import numpy as np
    import pytask


    for i in range(10):

        @pytask.mark.task
        def task_create_random_data(produces=f"data_{i}.pkl", seed=i):
            rng = np.random.default_rng(seed)
            ...


``depends_on`` and ``produces``
-------------------------------

You can also use decorators to supply values to the function.

To specify a dependency which is the same for all parametrizations, add it with
``@pytask.mark.depends_on``. And add a product with ``@pytask.mark.produces``

.. code-block:: python

    for i in range(10):

        @pytask.mark.task
        @pytask.mark.depends_on(SRC / "common_dependency.file")
        @pytask.mark.produces(f"data_{i}.pkl")
        def task_create_random_data(produces, seed=i):
            rng = np.random.default_rng(seed)
            ...


.. _how_to_parametrize_a_task_the_id:

The id
------

Every task has a unique id which can be used to :doc:`select it <how_to_select_tasks>`.
The normal id combines the path to the module where the task is defined, a double colon,
and the name of the task function. Here is an example.

.. code-block::

    ../task_example.py::task_example

This behavior would produce duplicate ids for parametrized tasks. By default,
auto-generated ids are used which are explained :ref:`here <auto_generated_ids>`.

More powerful are user-defined ids.


.. _ids:

User-defined ids
~~~~~~~~~~~~~~~~

The :func:`@pytask.mark.task <_pytask.task_utils.task>` decorator has an ``id`` keyword
which allows the user to set the a special name for the iteration.

.. code-block:: python

    for i, id_ in [(0, "first"), (1, "second")]:

        @pytask.mark.task(id=id_)
        def task_example(i=i, produces=f"out_{i}.txt"):
            ...

produces these ids

.. code-block::

    task_example.py::task_example[first]
    task_example.py::task_example[second]


Complex example
---------------

Parametrizations are becoming more complex quickly. Often, you need to supply many
arguments and ids to tasks.

Two changes will make your life easier.

1. Build the arguments and ids for every parametrization in a separate function.
2. Use the ``kwargs`` argument of the ``pytask.mark.task`` decorator to pass the
   arguments to the task.

.. code-block:: python

    def create_parametrization():
        id_to_kwargs = {}
        for i, id_ in enumerate(["first", "second"]):
            id_to_kwargs[id_] = {"produces": f"out_{i}.txt"}

        return id_to_kwargs


    ID_TO_KWARGS = create_parametrization()


    for id_, kwargs in ID_TO_KWARGS.items():

        @pytask.mark.task(id=id_, kwargs=kwargs)
        def task_example(i, produces):
            ...

The :doc:`best-practices guide on parametrizations
<../how_to_guides/bp_parametrizations>` goes into even more detail on how to scale
parametrizations.
