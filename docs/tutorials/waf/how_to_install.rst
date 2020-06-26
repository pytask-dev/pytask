How to install
==============

To build a project with Waf, you need an executable called ``waf.py`` which offers many
pre-defined commands like ``configure``, ``build``, and ``distclean``. In addition to
that, there is a ``mywaflib`` folder which contains Waf's code. Both can be bundled with
your projects or downloaded if needed. The ``waf.py`` also indicates the root of the
project folder.

To install pytask, type

.. code-block:: bash

    $ conda config --add channels conda-forge --add channels pytask
    $ conda install pytask

To indicate the root of the project, place a ``pytask.ini``, ``tox.ini`` or
``setup.cfg`` with a ``[pytask]`` section in the directory. You can leave
the file empty and use the default configuration.

.. code-block:: ini

    # Content of pytask.ini / tox.ini / setup.cfg.

    [pytask]

The configuration file indicates the root the project. In the same directory, pytask
will store information across executions in ``.pytask.sqlite3``. The database keeps
track of whether files change in the project and whether steps need to be re-executed.
