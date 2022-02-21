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
from textwrap import dedent
from textwrap import indent

import packaging.version
import requests
import tabulate
import wcwidth
from tqdm import tqdm


_FILE_HEAD = r"""
.. _plugin-list:

Plugin List
===========

PyPI projects that match "pytask-\*" are considered plugins and are listed
automatically. Packages classified as inactive are excluded.

.. The following conditional uses a different format for this list when
   creating a PDF, because otherwise the table gets far too wide for the
   page.

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


_EXCLUDED_PACKAGES = ["pytask-io"]


def _escape_rst(text: str) -> str:
    """Rudimentary attempt to escape special RST characters to appear as plain text."""
    text = (
        text.replace("*", "\\*")
        .replace("<", "\\<")
        .replace(">", "\\>")
        .replace("`", "\\`")
    )
    text = re.sub(r"_\b", "", text)
    return text


def _iter_plugins():
    """Iterate over all plugins and format entries."""
    regex = r">([\d\w-]*)</a>"
    response = requests.get("https://pypi.org/simple")

    matches = [
        match
        for match in re.finditer(regex, response.text)
        if match.groups()[0].startswith("pytask-")
        and match.groups()[0] not in _EXCLUDED_PACKAGES
    ]

    for match in tqdm(matches, smoothing=0):
        name = match.groups()[0]
        response = requests.get(f"https://pypi.org/pypi/{name}/json")
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
                if requirement == "pytask" or "pytask " in requirement:
                    requires = requirement
                    break
        releases = response.json()["releases"]

        for release in sorted(releases, key=packaging.version.parse, reverse=True):
            if releases[release]:
                release_date = datetime.date.fromisoformat(
                    releases[release][-1]["upload_time_iso_8601"].split("T")[0]
                )
                last_release = release_date.strftime("%b %d, %Y")
                break

        name = f':pypi:`{info["name"]}`'
        summary = _escape_rst(info["summary"].replace("\n", ""))

        yield {
            "name": name,
            "summary": summary.strip(),
            "last release": last_release,
            "status": status,
            "requires": requires,
        }


def _plugin_definitions(plugins):
    """Return RST for the plugin list that fits better on a vertical page."""

    for plugin in plugins:
        yield dedent(
            f"""
            {plugin['name']}
               *last release*: {plugin["last release"]},
               *status*: {plugin["status"]},
               *requires*: {plugin["requires"]}

               {plugin["summary"]}
            """
        )


def main():
    plugins = list(_iter_plugins())

    reference_dir = pathlib.Path("docs", "source")

    plugin_list = reference_dir / "plugin_list.rst"
    with plugin_list.open("w") as f:
        f.write(_FILE_HEAD)
        f.write(f"This list contains {len(plugins)} plugins.\n\n")
        f.write(".. only:: not latex\n\n")

        wcwidth  # reference library that must exist for tabulate to work
        plugin_table = tabulate.tabulate(plugins, headers="keys", tablefmt="rst")
        f.write(indent(plugin_table, "   "))
        f.write("\n\n")

        f.write(".. only:: latex\n\n")
        f.write(indent("".join(_plugin_definitions(plugins)), "  "))


if __name__ == "__main__":
    main()
