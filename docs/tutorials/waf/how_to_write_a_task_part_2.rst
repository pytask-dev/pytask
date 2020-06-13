How to write a task - Part 2
============================

The second task written for Waf looks like this:

.. code-block:: python

    # Content of hello_moon.py

    from pathlib import Path
    from bld.project_paths import project_paths_join as ppj


    def main():
        dependency = Path(ppj("BLD", "hello_earth.txt"))
        target = Path(ppj("BLD", "hello_moon.txt"))

        target.write_text(dependency.read_text() + "\n\n" + "Hello, Moon!")


    if __name__ == "__main__":
        main()


The second task file for pipeline becomes

.. code-block:: python

    # Content of hello_moon.py

    from pathlib import Path


    def main():
        dependency = Path("{{ build_directory }}", "hello_earth.txt")
        target = Path("{{ build_directory }}", "hello_moon.txt")

        target.write_text(dependency.read_text() + "\n\n" + "Hello, Moon!")


    if __name__ == "__main__":
        main()

You can also replace the whole path with the keyword from the task specification.

.. code-block:: python

    ...


    def main():
        target = Path("{{ depends_on }}")


    ...
