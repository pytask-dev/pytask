from __future__ import annotations

import pytask


@pytask.mark.produces("out.txt")
def task_dry_run(produces):
    produces.write_text("This text file won't be produced in a dry-run.")


if __name__ == "__main__":
    pytask.console.record = True
    pytask.main({"paths": __file__, "dry_run": True})
    pytask.console.save_svg("dry-run.svg", title="pytask")
