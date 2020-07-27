API
===

General
-------


pytask.main
~~~~~~~~~~~

.. autofunction:: pytask.main.main


pytask.main.Session
~~~~~~~~~~~~~~~~~~~

The session is more dynamic than the configuration and has attributes which are changed
or are added to the instance during the build process.

.. currentmodule:: pytask.main

.. autosummary::
   :toctree: _generated/

   Session
   Session.from_config


config
~~~~~~

The configuration is more static than the :class:`~pytask.main.Session`. It is a
dictionary of options which is determined in the beginning of a pytask run.


Marks
-----

pytask uses marks to attach additional information to task functions which is processed
in the host or in plugins. The following marks are available by default.


pytask.mark.depends_on
~~~~~~~~~~~~~~~~~~~~~~


.. autofunction:: pytask.nodes.depends_on


pytask.mark.produces
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pytask.nodes.produces


pytask.mark.parametrize
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pytask.parametrize.parametrize
