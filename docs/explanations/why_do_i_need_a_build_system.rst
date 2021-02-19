Why do I need a build system?
=============================

TL;DR
-----

Research projects consists of complex workflows which handle data, employ models, and
produce figures, tables, and reports.

Ensuring that all steps of the analysis are up-to-date should not be done by hand since
this process is error-prone and time-consuming.

Build systems like pytask provide an easy interface for researchers to express the
relationships among the tasks in a research project and conveniently manage the
execution of a project.


The case against traditional solutions
--------------------------------------

There are some traditional ways to manage workflows and I argue why they should be
abolished.

For a better understanding, imagine the workflow of an empirical research project which
consists of multiple tasks doing the data preparation, the analysis, and preparing the
results.

- Executing all tasks by hand.

  Many workflows are managed by hand which is time-consuming and error-prone since the
  room for human errors is big.

  Communicating the build process to collaborators requires detailed descriptions of all
  steps which is, again, time-consuming. Thus, the build process is often only shared
  knowledge within the project team.

  It severely hampers reusability and engagement with the project from outside parties
  and negatively impacts reproducibility.

- A main file to control all tasks.

  The setup usually cannot infer which tasks need to be run. Thus, the build time is
  unnecessarily high.

  Often times, the main file introduces side-effects into the tasks via global variables
  or other mechanisms which makes it impossible to run tasks independent from the main
  file. It is a nightmare in terms of reproducibility since unintended side-effects may
  affect your results without you knowing it.


The case for build systems
--------------------------

First of all, a build system helps you to automate the boring and repetitive stuff. You
have more time and mental capacity for the things which really matter.

Build systems enable or facilitate reproducibility since the workflow is clearly defined
and can be repeated by outside parties.

Build systems help you to modularize your code. Modularization means to structure code
into logical chunks and to reuse code. It reduces maintenance costs and facilitates
testing which is key for reproducibility. Without a build system, users might opt for
larger chunks of code because a more granular structure is harder to keep up-to-date.
