How to define dependencies and products
=======================================

Task have dependencies and products. Both can be attached to a task function by using
decorators. This is necessary so that pytask knows when a task is able to run, needs to
be run again or has produced the desired outcome.

Let us have a look at an exemplary task.

.. code-block:: python

    import pytask
    from pathlib import Path

    PARENT_DIRECTORY = Path(__file__).parent


    @pytask.mark.depends_on([Path("in_1.txt"), PARENT_DIRECTORY / "in_2.txt"])
    @pytask.mark.produces("out.txt")
    def task_combine_files(depends_on, produces):
        in_1 = depends_on[0].read_text()
        in_2 = depends_on[1].read_text()
        produces.write_text(in_1 + in_2)

In this example, we have three different ways to specify a dependency or product.

1. Let us start with the product. The value in the decorator is ``"out.txt"``. Strings
   are interpreted as paths. If paths are not absolute, meaning ``"/home/out.txt"``,
   paths are assumed to be relative to the directory in which the task is defined.

   If you specify ``produces`` as an argument of the function, the function receives the
   path to the product, the interpreted value, and not the original string. This is
   often times more useful and allows to inspect how pytask interprets the value.

2. The first dependency is also a relative path, but given as a :class:`pathlib.Path`.
   It is also interpreted relatively to the file where the task is defined.

3. The second dependency is an absolute path and is not interpreted or altered in any
   way. This pattern might be more common in bigger projects where PARENT_DIRECTORY can
   be an imported variable which points to the source or build directory of a project.
