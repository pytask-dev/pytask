Why do I need a build system?
=============================

A common problem people face when analyzing data (or building software, etc.) is that
their workflows involve multiple tasks. The tasks might have a order in which they need
to be executed because they build upon each other.

For example, a workflow of an empirical research project consists of tasks doing the
data preparation, the analysis, reporting results with tables and figures and, finally,
tasks which compile the reports.

Often, people keep all files in the workflow up-to-date by

- executing all tasks by hand.

  It is problematic because communicating the build process to collaborators is hard and
  the process itself is error-prone since one might messes up the order or forgets to
  run a task.

- having a main file which runs all tasks.

  The setup usually cannot infer which tasks need to be run. Thus, the build time is
  unnecessarily high. Often times, the main file introduces side-effects into the tasks
  via global variables or other mechanisms which makes it impossible to run tasks
  independent from the main file. This is a nightmare if you need to debug your project.

A build system is a framework to manage tasks and dependencies and, at best, the user
does not even feel the layer between her and the tasks.

From the research perspective, a build system is especially useful because it enables or
facilitates the reproducibility of projects. For users who are not programmers by
nature, it is necessary that the interface of the build system is intuitive and has a
steep learning curve which are both goals pytask tries to accomplish.

From a software engineering perspective, a build system helps to modularize your code.
Modularization means to structure code into logical chunks and to reuse code. It reduces
maintenance costs and facilitates testing. Without a build system, users might opt for
larger chunks because a more granular structure is harder to keep in sync.
