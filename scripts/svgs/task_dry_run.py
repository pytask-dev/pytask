from __future__ import annotations

from pathlib import Path

import pytask


@pytask.mark.produces("out.txt")
def task_dry_run(produces: Path) -> None:
    produces.write_text("This text file won't be produced in a dry-run.")


if __name__ == "__main__":
    pytask.console.record = True
    pytask.build({"paths": __file__, "dry_run": True})
    pytask.console.save_svg("dry-run.svg", title="pytask")
