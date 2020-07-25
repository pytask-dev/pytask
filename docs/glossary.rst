Glossary
========

.. glossary::

    Build system
        A build system is a tool for developing software which manages the process from
        compiling the source code to binary code, packaging the binary code and running
        tests.

        But, the same logic - managing tasks with multiple dependencies to get a product
        - applies to many areas including research projects.

    DAG
        A `directed acyclic graph (DAG) <https://en.wikipedia.org/wiki/
        Directed_acyclic_graph>`_  is a graph with a finite amount of vertices and edges
        which are connected such that no circles exist.

    host
        The program which offers extensibility via entry-points.

    entry-point
        Access points for plugins in the host program. At an entry-point, the host sends
        a message which can be processed by plugins. Then, the plugins may respond.

    plugin
        A plugin is a software which changes the behavior of the host program by
        processing the message send by the host at an entry-point. A plugin can consist
        of one or more :term:`hook implementations <hook implementation>`.

    hooking
        See `hooking on Wikipedia <https://en.wikipedia.org/wiki/Hooking>`_.

    hook specification
        Another term for :term:`entry-point`.

    hook implementation
        A part of the plugin which intercepts the message at one specific entry-point.
