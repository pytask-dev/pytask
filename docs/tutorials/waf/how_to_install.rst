How to install
==============

To build a project with Waf, you need an executable called ``waf.py`` which offers many
pre-defined commands like ``configure``, ``build``, and ``distclean``. In addition to
that, there is a ``mywaflib`` folder which contains Waf's code. Both can be bundled with
your projects or downloaded if needed. The ``waf.py`` also indicates the root of the
project folder.

To install pipeline, type

.. code-block:: bash

    $ conda install -c opensourceeconomics pipeline

To indicate the root of the project, place a ``.pipeline.yaml`` in the directory. You
can leave the file empty and use the default configuration. Here is a sample of the
default configuration.

.. code-block:: yaml

    # Content of .pipeline.yaml

    source_directory: src
    build_directory: bld

pipeline needs no ``configure`` because the configuration is created dynamically. It
also has a ``build`` and ``clean`` command which work similarly.
