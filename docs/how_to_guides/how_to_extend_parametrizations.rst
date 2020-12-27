How to extend parametrizations
==============================

Parametrization helps you to reuse code and quickly scale from one to a multitude of
tasks. Sometimes, these tasks are expensive because they take long or require a lot of
resources. Thus, you only want to run them if really necessary.


The problem
-----------

There are two problems when extending parametrizations which might trigger accidental
reruns of tasks.


IDs
~~~

If you do not know how ids for parametrized tasks are produced, read the following
:ref:`section in the tutorial about parametrization <how_to_parametrize_a_task_the_id>`.

The problem is that argument values which are not booleans, numbers or strings produce
positionally dependent ids. The position might change if you extend the parametrization
which re-executes a task.

To resolve the problem, you can choose one of the two solutions in the tutorial. Either
pass a function to convert non-standard objects to suitable representations or pass your
own ids.


Modification of the task module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To extend your parametrization, you would normally change the module in which the task
is defined. By default, this triggers a re-run of the task.


Solution: side-effect
---------------------

The problem can be resolved by introducing a side-effect. Add another module with the
following content.

.. code-block:: python

    # Content of side_effect.py

    ARG_VALUES = [(0,), (1,)]
    IDS = ["first_tuple", "second_tuple"]

And change the task module to

.. code-block:: python

    import pytask
    from side_effect import ARG_VALUES, IDS


    @pytask.mark.parametrize("i", ARG_VALUES, ids=IDS)
    def task_example(i):
        pass

The key idea is to not reference the ``side_effect.py`` module as a dependency of the
task. Now, you can extend the parametrization without re-executing former tasks.

.. caution::

    Be careful, because pytask does not care about which object is passed to the
    parametrized function. Thus, it would be better to replace ``IDS`` with a function
    which hashes the tuples to recognize changes as shown in the :ref:`tutorial
    <how_to_parametrize_a_task_convert_other_objects>`.
