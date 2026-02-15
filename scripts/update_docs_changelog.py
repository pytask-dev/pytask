"""Render CHANGELOG.md for Markdown-only docs consumers."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_URL = "https://github.com/pytask-dev/pytask"
_CHANGELOG = Path("CHANGELOG.md")
_OUTPUT = Path("docs/source/includes/changelog.txt")


def _strip_tilde(text: str) -> str:
    return text.removeprefix("~")


def _render_roles(text: str) -> str:
    text = re.sub(
        r"\{pull\}`(\d+)`",
        lambda m: f"[#{m.group(1)}]({_REPO_URL}/pull/{m.group(1)})",
        text,
    )
    text = re.sub(
        r"\{issue\}`(\d+)`",
        lambda m: f"[#{m.group(1)}]({_REPO_URL}/issues/{m.group(1)})",
        text,
    )

    def repl_user(match: re.Match[str]) -> str:
        user = match.group(1).strip().lstrip("@")
        return f"[@{user}](https://github.com/{user})"

    text = re.sub(r"\{user\}`([^`]+)`", repl_user, text)

    text = re.sub(
        r"\{[a-zA-Z_]+\}`([^`<>]+?)\s*<[^`<>]+>`",
        lambda m: f"`{_strip_tilde(m.group(1).strip())}`",
        text,
    )
    return re.sub(
        r"\{[a-zA-Z_]+\}`([^`]+?)`",
        lambda m: f"`{_strip_tilde(m.group(1).strip())}`",
        text,
    )


def main() -> None:
    rendered = _render_roles(_CHANGELOG.read_text())
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(rendered)


if __name__ == "__main__":
    main()
