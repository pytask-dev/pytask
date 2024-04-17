"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full list see the
documentation: https://www.sphinx-doc.org/en/master/usage/configuration.html

"""

from __future__ import annotations

import inspect
import os
import sys
import warnings
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import pytask

if TYPE_CHECKING:
    import sphinx


# -- Project information ---------------------------------------------------------------

project = "pytask"
author = "Tobias Raabe"
copyright = f"2020, {author}"  # noqa: A001

# The version, including alpha/beta/rc tags, but not commit hash and datestamps
release = version("pytask")
# The short X.Y version.
version = ".".join(release.split(".")[:2])

# -- General configuration -------------------------------------------------------------

master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be extensions coming
# with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "IPython.sphinxext.ipython_console_highlighting",
    "IPython.sphinxext.ipython_directive",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    "sphinxext.opengraph",
    "sphinx_copybutton",
    "sphinx_click",
    "sphinx_toolbox.more_autodoc.autoprotocol",
    "nbsphinx",
    "myst_parser",
    "sphinx_design",
]

# List of patterns, relative to source directory, that match files and directories to
# ignore when looking for source files. This pattern also affects html_static_path and
# html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]


pygments_style = "sphinx"
pygments_dark_style = "monokai"

# -- Extensions configuration ----------------------------------------------------------

# Configuration for autodoc.
add_module_names = True

# Remove prefixed $ for bash, >>> for Python prompts, and In [1]: for IPython prompts.
copybutton_prompt_text = r"\$ |>>> |In \[\d\]: "
copybutton_prompt_is_regexp = True

_repo = "https://github.com/pytask-dev/pytask"
extlinks = {
    "pypi": ("https://pypi.org/project/%s/", "%s"),
    "issue": (f"{_repo}/issues/%s", "#%s"),
    "pull": (f"{_repo}/pull/%s", "#%s"),
    "user": ("https://github.com/%s", "@%s"),
}

intersphinx_mapping = {
    "click": ("https://click.palletsprojects.com/en/8.0.x/", None),
    "deepdiff": ("https://zepworks.com/deepdiff/current/", None),
    "networkx": ("https://networkx.org/documentation/stable", None),
    "nx": ("https://networkx.org/documentation/stable", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "pd": ("https://pandas.pydata.org/docs", None),
    "pluggy": ("https://pluggy.readthedocs.io/en/latest", None),
    "pygraphviz": ("https://pygraphviz.github.io/documentation/stable/", None),
    "python": ("https://docs.python.org/3.10", None),
}

# MyST
myst_enable_extensions = ["deflist", "dollarmath"]
myst_footnote_transition = False

# Open Graph
ogp_social_cards = {"image": "_static/images/pytask_w_text.png"}


# Linkcode, based on numpy doc/source/conf.py
def linkcode_resolve(domain: str, info: dict[str, str]) -> str:  # noqa: C901, PLR0912
    """Determine the URL corresponding to Python object."""
    if domain != "py":
        return None

    modname = info["module"]
    fullname = info["fullname"]

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split("."):
        try:
            with warnings.catch_warnings():
                # Accessing deprecated objects will generate noisy warnings
                warnings.simplefilter("ignore", FutureWarning)
                obj = getattr(obj, part)
        except AttributeError:  # noqa: PERF203
            return None

    try:
        fn = inspect.getsourcefile(inspect.unwrap(obj))
    except TypeError:
        try:  # property
            fn = inspect.getsourcefile(inspect.unwrap(obj.fget))
        except (AttributeError, TypeError):
            fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except TypeError:
        try:  # property
            source, lineno = inspect.getsourcelines(obj.fget)
        except (AttributeError, TypeError):
            lineno = None
    except OSError:
        lineno = None

    linespec = f"#L{lineno}-L{lineno + len(source) - 1}" if lineno else ""

    fn = os.path.relpath(fn, start=Path(pytask.__file__).parent)

    if "+" in pytask.__version__:
        return (
            f"https://github.com/pytask-dev/pytask/blob/main/src/pytask/{fn}{linespec}"
        )
    return (
        f"https://github.com/pytask-dev/pytask/blob/"
        f"v{pytask.__version__}/src/pytask/{fn}{linespec}"
    )


# -- Options for HTML output -----------------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for a list of
# built-in themes.
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here, relative
# to this directory. They are copied after the built-in static files, so a file named
# "default.css" will overwrite the built-in "default.css".
html_css_files = ["css/termynal.css", "css/termynal_custom.css", "css/custom.css"]

html_js_files = ["js/termynal.js", "js/custom.js"]

# The name of an image file (within the static path) to use as favicon of the docs.
# This file should be a Windows icon file (.ico) being 16x16 or 32x32 pixels large.
html_favicon = "_static/images/pytask.ico"

# Add any paths that contain custom static files (such as style sheets) here, relative
# to this directory. They are copied after the builtin static files, so a file named
# "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If false, no module index is generated.
html_domain_indices = True

# If false, no index is generated.
html_use_index = True

# If true, the index is split into individual pages for each letter.
html_split_index = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True

html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    "light_logo": "images/pytask_w_text_light.svg",
    "dark_logo": "images/pytask_w_text_dark.svg",
}


def setup(app: sphinx.application.Sphinx) -> None:
    """Configure sphinx."""
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )
