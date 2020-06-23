How to install
==============

To build a project with Waf, you need an executable called ``waf.py`` which offers many
pre-defined commands like ``configure``, ``build``, and ``distclean``. In addition to
that, there is a ``mywaflib`` folder which contains Waf's code. Both can be bundled with
your projects or downloaded if needed. The ``waf.py`` also indicates the root of the
project folder.

To install pytask, type

.. code-block:: bash

    $ conda install -c pytask pytask

To indicate the root of the project, place a ``pytask.ini``, ``tox.ini`` or
``setup.cfg`` with a ``[pytask]`` section in the directory. You can leave
the file empty and use the default configuration. Here is a sample of the default
configuration.

.. code-block:: ini

    # Content of pytask.ini / tox.ini / setup.cfg.

    [pytask]

The configuration file indicates the root the project. In the same directory, a database
will be saved called ``.pytask.sqlite3``. The database keeps track of whether files
change in the project and whether steps need to be re-executed. It is recommended to
create such a file.

pytask needs no ``configure`` because the configuration is created dynamically.
