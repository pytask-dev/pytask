"""Check visible line lengths in Termynal documentation snippets."""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
from pathlib import Path

# Existing Termynal snippets top out at 78 visible characters.
MAX_TERMYNAL_LINE_LENGTH = 78

_CONSOLE_BLOCK_PATTERN = re.compile(r"```console\n(.*?)\n```", re.DOTALL)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def _visible_text(line: str) -> str:
    return unescape(_HTML_TAG_PATTERN.sub("", line))


def _iter_violations(path: Path, max_length: int) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if 'class="termy"' not in text:
        return []

    violations = []
    for match in _CONSOLE_BLOCK_PATTERN.finditer(text):
        start_line = text.count("\n", 0, match.start(1)) + 1
        for offset, raw_line in enumerate(match.group(1).splitlines()):
            rendered_line = _visible_text(raw_line)
            line_length = len(rendered_line)
            if line_length > max_length:
                violations.append(
                    f"{path}:{start_line + offset}: rendered line has "
                    f"{line_length} characters, maximum is {max_length}:\n"
                    f"    {rendered_line}"
                )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=sorted(Path("docs/source/_static/md").rglob("*.md")),
        help="Markdown files with Termynal snippets.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=MAX_TERMYNAL_LINE_LENGTH,
        help="Maximum visible line length for rendered terminal lines.",
    )
    args = parser.parse_args()

    violations = [
        violation
        for path in args.paths
        if path.is_file()
        for violation in _iter_violations(path, args.max_length)
    ]
    if violations:
        sys.stderr.write("\n\n".join(violations))
        sys.stderr.write("\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
