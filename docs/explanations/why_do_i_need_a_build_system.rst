Why do I need a build system?
=============================

A common problem people face when analyzing data (or building software, etc.) is that
their workflows involve multiple tasks which are in some way related to each other.

A workflow for a common empirical research project consists of tasks doing the data
preparation, the analysis, reporting results with tables and figures and, finally, tasks
which compile the reports.

Common solutions to keep all files in the workflow up-to-date are

- executing all tasks by hand.

  Communicating the build process to collaborators is hard and the process is
  error-prone.

- having a main file which runs all tasks.

  The setup usually cannot infer which tasks need to be run. Thus, the build time is
  artificially high. Often times, the main file introduces side-effects into the tasks
  via global variables or other mechanisms which makes it impossible to run task
  independent from the main file. This is a nightmare for debugging the project.

A build system is a framework to manage tasks and dependencies and, at best, the user
does not even feel the layer between her and the tasks.

From the research perspective, a build system is especially attractive because it
enables or facilitates the reproducibility or projects. For users who are not
programmers by nature, it is necessary that using the build system is intuitive and has
a steep learning curve which are both goals pytask tries to accomplish.

From a software engineering perspective, a build system helps to modularize your code.
Modularization means to structure code into logical chunks, to reuse code which also
facilitates testing. Without a build system, users might opt for larger chunks because
they do not want to worry about smaller chunks.
