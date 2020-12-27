Structure of task files
=======================

This section provides best-practices on how to structure task files.


TL;DR
-----

- A task function should be the first function in a task module and serve as an
  entry-point to the whole module.

- There might be multiple task functions in a task module, but it is recommended to
  split modules once they become too large.

- The task function is mainly responsible for handling IO operations like loading and
  saving files and calling Python functions on the task's inputs. IO should not be
  handled in other functions since it introduces side-effects.

- All other functions in the module are private functions used to accomplish only this
  specific task. The functions should be pure, meaning without side-effects.

- Functions used to accomplish tasks in multiple task modules should have their own
  module.


.. seealso::

    The advice above may remind readers of "deep modules", a term coined by John
    Ousterhout and described in "A Philosophy of Software Design".
