API
===


Hook Specifications
-------------------

Hook specifications are the :term:`entry-points <entry-point>` provided by pytask to
change the behavior of the program.

.. automodule:: pytask.hookspecs
   :members:


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
