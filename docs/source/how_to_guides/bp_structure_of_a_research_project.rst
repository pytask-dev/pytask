Structure of a research project
===============================

The documentation talks lengthy about how to organize research projects with pytask.
But, there are some design decisions on an even higher level which may make it harder to
accomplish your research in the long run. These lessons are collected here.


Extract model code from the research project
--------------------------------------------

Having all code of a research project in a single repository is beneficial in some
situations. It keeps all the parts in sync, allows for easy code-reuse, and other
advantages. It is probably the starting point and the approach taken by most research
projects.

In situations where some parts of the code base take the majority of code or are
especially important, the better way is to extract some code and move it into separate
packages.

As an example, look at two repositories from a COVID-19 forecasting project.

- `sid-germany <https://github.com/covid-19-impact-lab/sid-germany>`_ contains the
  research code managed by pytask which runs epidemiological forecasts across a wide
  range of scenarios.

- `sid <https://github.com/covid-19-impact-lab/sid>`_ contains the code for the
  epidemiological model which is applied in the research project.

Separating the model code from the research project provided several benefits.

- The model code is isolated and has its own test suite. Assessing and ensuring the code
  quality is thus easier.

- Versioning enhances reproducibility and also allows to develop the model independently
  from the research project.

- One is forced to think more about the interface of model since you wear two hats at
  the same time, the one of a maintainer and a user. This improves the quality of the
  package tremendously.

- Developing sid as a package makes it easier for other researchers to contribute to the
  project, make their research or review your work.

In conclusion, this setup contributed a lot to build a new model from scratch and
produce several publications in a short time span.
