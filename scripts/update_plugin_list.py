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

from __future__ import annotations

import datetime
import pathlib
import re
from textwrap import indent
from typing import TYPE_CHECKING

import httpx
import packaging.version
import tabulate
import wcwidth
from tqdm import tqdm

if TYPE_CHECKING:
    from collections.abc import Generator

_FILE_HEAD = r"""
.. _plugin-list:

Plugin List
===========

PyPI projects that match "pytask-\*" are considered plugins and are listed
automatically. Packages classified as inactive are excluded.

.. warning::

   Please be aware that this list is not a curated collection of projects and does not
   undergo a systematic review process. It serves purely as an informational resource to
   aid in the discovery of ``pytask`` plugins.

   Do not presume any endorsement from the ``pytask`` project or its developers, and
   always conduct your own quality assessment before incorporating any of these plugins
   into your own projects.

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


_EXCLUDED_PACKAGES = ["pytask-io", "pytask-list"]


def _escape_rst(text: str) -> str:
    """Rudimentary attempt to escape special RST characters to appear as plain text."""
    text = (
        text.replace("*", "\\*")
        .replace("<", "\\<")
        .replace(">", "\\>")
        .replace("`", "\\`")
    )
    return re.sub(r"_\b", "", text)


def _iter_plugins() -> Generator[dict[str, str], None, None]:  # noqa: C901
    """Iterate over all plugins and format entries."""
    regex = r">([\d\w-]*)</a>"
    response = httpx.get("https://pypi.org/simple/", timeout=20)

    matches = [
        match
        for match in re.finditer(regex, response.text)
        if match.groups()[0].startswith("pytask-")
        and match.groups()[0] not in _EXCLUDED_PACKAGES
    ]

    for match in tqdm(matches, smoothing=0):
        name = match.groups()[0]
        response = httpx.get(f"https://pypi.org/pypi/{name}/json", timeout=20)
        if response.status_code == 404:  # noqa: PLR2004
            # Some packages might return a 404.
            continue

        response.raise_for_status()
        info = response.json()["info"]

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

        releases = response.json()["releases"]

        for release in sorted(releases, key=_version_sort_key, reverse=True):
            if releases[release]:
                release_date = datetime.date.fromisoformat(
                    releases[release][-1]["upload_time_iso_8601"].split("T")[0]
                )
                last_release = release_date.strftime("%b %d, %Y")
                break

        name = f':pypi:`{info["name"]}`'
        summary = ""
        if info["summary"]:
            summary = _escape_rst(info["summary"].replace("\n", ""))

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

    plugin_list = reference_dir / "plugin_list.rst"
    with plugin_list.open("w") as f:
        f.write(_FILE_HEAD)
        f.write(f"This list contains {len(plugins)} plugins.\n\n")

        assert wcwidth  # reference library that must exist for tabulate to work
        plugin_table = tabulate.tabulate(plugins, headers="keys", tablefmt="rst")
        f.write(indent(plugin_table, "   "))
        f.write("\n")


if __name__ == "__main__":
    main()
