How to clean a project
======================

At some point, projects are cluttered with obsolete files. For example, a product of a
task was renamed and the old version still exists.

To clean directories from files which are not recognized by pytask, enter the directory
and type

.. code-block::

    $ pytask clean
    =============================== Start pytask session ===============================
    Platform: win32 -- Python x.y.z, pytask x.y.z, pluggy x.y.z
    Root: .
    Collected 3 task(s).

    Files which can be removed:

    Would remove C:\Users\project\obsolete_file_1.txt.
    Would remove C:\Users\project\obsolete_folder\obsolete_file_2.txt.
    Would remove C:\Users\project\obsolete_folder\obsolete_file_3.txt.

By default, pytask takes the current directory and performs a dry-run which shows only
files which could be removed. Pass other paths to the command if you want to inspect
specific directories.

If you want to remove the files, there exist two other modes for :option:`pytask clean
-m`.

- ``force`` removes all files suggested in the ``dry-run`` without any confirmation.
- ``interactive`` allows you to decide for every file whether to keep it or not.

If you want to delete whole folders instead of only the files in them, use
:option:`pytask clean -d`.

.. code-block::

    $ pytask clean -d
    =============================== Start pytask session ===============================
    Platform: win32 -- Python x.y.z, pytask x.y.z, pluggy x.y.z
    Root: .
    Collected 3 task(s).

    Files and directories which can be removed:

    Would remove C:\Users\project\obsolete_file_1.txt.
    Would remove C:\Users\project\obsolete_folder.


Command line options
--------------------

.. program:: pytask clean

To clean your project, pytask offers a clean command similar to ``git clean``.

.. option:: pytask clean [OPTIONS] [PATHS]...

The command line interface has the following options.

.. option:: -m, --mode [dry-run|interactive|force]

    The mode for the clean command.

    - ``dry-run`` shows which files and directories would be removed.
    - ``force`` removes all files and directories without further confirmation.
    - ``interactive`` allows the user to choose for every file and directory.

.. option:: -d, --directories

    Allows to remove whole directories if all its content can be removed as well.

.. option:: -q, --quiet

    Do not show which files are removed.
