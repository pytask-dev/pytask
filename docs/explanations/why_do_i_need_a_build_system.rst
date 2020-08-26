Why do I need a build system?
=============================

A common problem people face when analyzing data (or building software, etc.) is that
their workflows involve multiple steps which are in some way related to each other.

For example, an empirical research project has the following phases.

1. A data preparation phase which handles data, relabels variables, etc..
2. An analysis phase where statistical models are applied to the data.
3. A phase which translates the results of the analysis into figures and tables.
4. Finally, everything is put into a report or paper ready to be published.

Each of the phases may involve numerous steps which makes it harder to

- execute all steps in the correct order.
- execute only the parts of the project which have changed (if runtime becomes
  important).
- communicate the build process to collaborators.

From the research perspective, a build system is attractive because it simplifies
reproducibility.

From a software engineering perspective, a build system helps to modularize your code
because smaller parts become more manageable.
