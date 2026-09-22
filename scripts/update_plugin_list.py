"""This script creates a list of plugins for pytask.

It is shamelessly stolen from pytest and therefore includes its license.

https://github.com/pytest-dev/pytest/blob/main/scripts/update-plugin-list.py


MIT License

Copyright (c) 2004 Holger Krekel and others

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

"""
# ruff: noqa: E501

from __future__ import annotations

import datetime
import html.parser
import pathlib
import re
from typing import TYPE_CHECKING
from urllib.parse import unquote
from urllib.parse import urlparse

import httpx
import packaging.version
import wcwidth
from packaging.utils import canonicalize_name

if TYPE_CHECKING:
    from collections.abc import Generator

_FILE_HEAD = """# Plugin List

PyPI projects that match `pytask-*` are considered plugins and are listed automatically.
Packages classified as inactive are excluded.

!!! warning

    Please be aware that this list is not a curated collection of projects and does not
    undergo a systematic review process. It serves purely as an informational resource to
    aid in the discovery of `pytask` plugins.

    Do not presume any endorsement from the `pytask` project or its developers, and always
    conduct your own quality assessment before incorporating any of these plugins into your
    own projects.

"""


_DEVELOPMENT_STATUS_CLASSIFIERS = (
    "Development Status :: 1 - Planning",
    "Development Status :: 2 - Pre-Alpha",
    "Development Status :: 3 - Alpha",
    "Development Status :: 4 - Beta",
    "Development Status :: 5 - Production/Stable",
    "Development Status :: 6 - Mature",
    "Development Status :: 7 - Inactive",
)


_EXCLUDED_PACKAGES = [
    "pytask-environment",
    "pytask-io",
    "pytask-list",
    "pytask-queue",
]


def _escape_markdown(text: str) -> str:
    """Rudimentary attempt to escape special Markdown table characters."""
    return text.replace("|", "\\|")


def _pad(text: str, width: int) -> str:
    """Pad text to the requested display width."""
    return text + " " * (width - wcwidth.wcswidth(text))


def _create_table(entries: list[dict[str, str]]) -> str:
    """Create a markdown table in the repository's canonical format."""
    if not entries:
        msg = "Cannot create a plugin table without entries."
        raise ValueError(msg)

    headers = list(entries[0])
    widths = [
        max(
            wcwidth.wcswidth(header),
            *(wcwidth.wcswidth(row[header]) for row in entries),
        )
        for header in headers
    ]

    header_cells = (
        _pad(header, width) for header, width in zip(headers, widths, strict=False)
    )
    header = "| " + " | ".join(header_cells) + " |"
    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    rows = [
        "| "
        + " | ".join(
            _pad(row[header], width)
            for header, width in zip(headers, widths, strict=False)
        )
        + " |"
        for row in entries
    ]
    return "\n".join([header, separator, *rows])


class _SimpleIndexParser(html.parser.HTMLParser):
    """Extract normalized project names from the PyPI simple index."""

    def __init__(self) -> None:
        super().__init__()
        self.project_names: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return

        href = dict(attrs).get("href")
        if href is None:
            return

        path = urlparse(href).path.rstrip("/")
        if not path.startswith("/simple/"):
            return

        project_name = unquote(path.removeprefix("/simple/"))
        if "/" not in project_name and project_name:
            self.project_names.append(canonicalize_name(project_name))


def _iter_project_names(simple_index: str) -> list[str]:
    """Return normalized project names from a PyPI simple index response."""
    parser = _SimpleIndexParser()
    parser.feed(simple_index)
    parser.close()
    return parser.project_names


def _iter_plugins() -> Generator[dict[str, str], None, None]:  # noqa: C901
    """Iterate over all plugins and format entries."""
    response = httpx.get("https://pypi.org/simple/", timeout=20)
    response.raise_for_status()

    project_names = [
        project_name
        for project_name in _iter_project_names(response.text)
        if project_name.startswith("pytask-") and project_name not in _EXCLUDED_PACKAGES
    ]

    for project_name in project_names:
        package_response = httpx.get(
            f"https://pypi.org/pypi/{project_name}/json",
            timeout=20,
        )
        if package_response.status_code == 404:  # noqa: PLR2004
            # Some packages might return a 404.
            continue

        package_response.raise_for_status()
        package = package_response.json()
        info = package["info"]

        if "Development Status :: 7 - Inactive" in info["classifiers"]:
            continue
        for classifier in _DEVELOPMENT_STATUS_CLASSIFIERS:
            if classifier in info["classifiers"]:
                status = classifier[22:]
                break
        else:
            status = "N/A"
        requires = "N/A"

        if info["requires_dist"]:
            for requirement in info["requires_dist"]:
                if re.match(r"pytask(?![-.\w])", requirement):
                    requires = requirement
                    break

        def _version_sort_key(version_string: str) -> packaging.version.Version:
            """
            Return the sort key for the given version string
            returned by the API.
            """
            try:
                return packaging.version.parse(version_string)
            except packaging.version.InvalidVersion:
                # Use a hard-coded pre-release version.
                return packaging.version.Version("0.0.0alpha")

        releases = package["releases"]

        for release in sorted(releases, key=_version_sort_key, reverse=True):
            if releases[release]:
                release_date = datetime.date.fromisoformat(
                    releases[release][-1]["upload_time_iso_8601"].split("T")[0]
                )
                last_release = release_date.strftime("%b %d, %Y")
                break

        # Use the canonical name from the simple-index link. Some projects have
        # temporarily published metadata with a different name, e.g. pytask_stata.
        name = f"[{project_name}](https://pypi.org/project/{project_name}/)"
        summary = ""
        if info["summary"]:
            summary = _escape_markdown(info["summary"].replace("\n", ""))

        yield {
            "name": name,
            "summary": summary.strip(),
            "last release": last_release,
            "status": status,
            "requires": requires,
        }


def main() -> None:
    plugins = list(_iter_plugins())

    reference_dir = pathlib.Path("docs", "source")

    plugin_list = reference_dir / "plugin_list.md"
    with plugin_list.open("w") as f:
        f.write(_FILE_HEAD)
        f.write(f"This list contains {len(plugins)} plugins.\n\n")
        f.write(_create_table(plugins))
        f.write("\n")


if __name__ == "__main__":
    main()
