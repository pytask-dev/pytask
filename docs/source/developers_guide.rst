Developer's Guide
=================


Creating showcases on the command line
--------------------------------------

- Replace prompt in powershell core with a simple arrow by typing

  .. code-block:: console

      $ function prompt {"> "}

- Rename the tab with

  .. code-block:: console

      $ $Host.UI.RawUI.WindowTitle = $title
