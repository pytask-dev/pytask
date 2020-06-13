How to write a task - Part 1
============================

We continue with the example of the former section and look at the script which is
executed by the task. Here is how the task is written with Waf.

.. code-block:: python

    # Content of hello_earth.py

    from pathlib import Path
    from bld.project_paths import project_paths_join as ppj


    def main():
        target = Path(ppj("BLD", "hello_earth.txt"))

        target.write_text("Hello, Earth!")


    if __name__ == "__main__":
        main()


The same file in pipeline looks like this.

.. code-block:: python

    # Content of hello_earth.py

    from pathlib import Path


    def main():
        target = Path("{{ build_directory }}", "hello_earth.txt")

        target.write_text("Hello, Earth!")


    if __name__ == "__main__":
        main()

It is possible to shorten the paths and use the keys of the task specification.

.. code-block:: python

    ...


    def main():
        target = Path("{{ produces }}")


    ...
