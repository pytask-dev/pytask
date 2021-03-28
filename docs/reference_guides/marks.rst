Marks
=====

pytask uses marks to attach additional information to task functions which is processed
in the host or in plugins. The following marks are available by default.


pytask.mark.depends_on
----------------------

.. autofunction:: _pytask.nodes.depends_on
   :noindex:


pytask.mark.produces
--------------------

.. autofunction:: _pytask.nodes.produces
   :noindex:


pytask.mark.parametrize
-----------------------

.. autofunction:: _pytask.parametrize.parametrize
   :noindex:


pytask.mark.try_first
---------------------

.. function:: try_first
    :noindex:

    Indicate that the task should be executed as soon as possible.

    This indicator is a soft measure to influence the execution order of pytask.

    .. important::

        This indicator is not intended for general use to influence the build order and
        to overcome misspecification of task dependencies and products.

        It should only be applied to situations where it is hard to define all
        dependencies and products and automatic inference may be incomplete like with
        pytask-latex and latex-dependency-scanner.


pytask.mark.try_last
---------------------

.. function:: try_last
    :noindex:

    Indicate that the task should be executed as late as possible.

    This indicator is a soft measure to influence the execution order of pytask.

    .. important::

        This indicator is not intended for general use to influence the build order and
        to overcome misspecification of task dependencies and products.

        It should only be applied to situations where it is hard to define all
        dependencies and products and automatic inference may be incomplete like with
        pytask-latex and latex-dependency-scanner.
