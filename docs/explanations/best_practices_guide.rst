Best practices guide
====================

This document serves  best practices or style guide for using pytask. Its purpose is to
provide beginners with orientation and to let experienced users share advice from
software engineering or research design.

Feedback on this guide is greatly appreciated. Feel free to open an issue or start the
conversation elsewhere if you want to share your experiences with some of the
suggestions, if you did not understand an advice or anything else.


Structure of task files
~~~~~~~~~~~~~~~~~~~~~~~

The following advice may remind readers of "deep modules", a term coined by John
Ousterhout and describe in "A Philosophy of Software Design".

- A task function should be the first function in a task module and serve as an
  entry-point to the whole module. Thus, the function needs a docstring.

- There might be multiple task functions in a task module, but it is recommended to
  split modules once they become too large.

- All other functions in the module are private functions used to accomplish only this
  specific task. The functions should be pure, meaning without side-effects.

- Functions used to accomplish tasks in multiple task modules should have their own
  module.

- The task function is mainly responsible for handling IO operations like loading and
  saving files and calling Python functions on the task's inputs. IO should not be
  handled in other functions since it introduces side-effects.
