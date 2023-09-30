from pathlib import Path

import pytask


@pytask.mark.persist
def task_make_input_bold(
    input_path: Path = Path("input.md"), output_path: Path = Path("output.md")
) -> None:
    output_path.write_text("**" + input_path.read_text() + "**")
