from __future__ import annotations

from pathlib import Path

import pytask


@pytask.mark.produces("hello_earth.txt")
def task_hello_earth(produces: Path) -> None:
    produces.write_text("Hello, earth!")


if __name__ == "__main__":
    pytask.console.record = True
    pytask.build({"paths": __file__})
    pytask.console.save_svg("readme.svg", title="pytask")
