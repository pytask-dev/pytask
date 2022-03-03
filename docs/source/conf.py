# Configuration file for the Sphinx documentation builder.
# This file only contains a selection of the most common options. For a full list see
# the documentation: https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup ------------------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory, add
# these directories to sys.path here. If the directory is relative to the documentation
# root, use os.path.abspath to make it absolute, like shown here.
from __future__ import annotations

from importlib.metadata import version

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
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_click",
    "sphinx_panels",
    "autoapi.extension",
    "myst_parser",
]

# List of patterns, relative to source directory, that match files and directories to
# ignore when looking for source files. This pattern also affects html_static_path and
# html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

suppress_warnings = ["ref.python"]

pygments_style = "sphinx"
pygments_dark_style = "monokai"

# -- Extensions configuration ----------------------------------------------------------

# Configuration for autodoc.
autosummary_generate = True
add_module_names = False
# Actually irrelevant since sphinx-click needs to import everything to build the cli.
autodoc_mock_imports = [
    "attr",
    "click",
    "click_default_group",
    "networkx",
    "pluggy",
    "pony",
]

# Remove prefixed $ for bash, >>> for Python prompts, and In [1]: for IPython prompts.
copybutton_prompt_text = r"\$ |>>> |In \[\d\]: "
copybutton_prompt_is_regexp = True

_repo = "https://github.com/pytest-dev/pytest"
extlinks = {
    "pypi": ("https://pypi.org/project/%s/", ""),
    "issue": (f"{_repo}/issues/%s", "issue #"),
    "pull": (f"{_repo}/pull/%s", "pull request #"),
    "user": ("https://github.com/%s", "@"),
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.9", None),
    "click": ("https://click.palletsprojects.com/en/8.0.x/", None),
    "pluggy": ("https://pluggy.readthedocs.io/en/latest", None),
}

# Configuration for autoapi
autoapi_type = "python"
autoapi_dirs = ["../../src"]
autoapi_keep_files = False
autoapi_add_toctree_entry = False


# MyST
myst_enable_extensions = ["colon_fence", "deflist", "dollarmath"]


# -- Options for HTML output -----------------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for a list of
# built-in themes.
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here, relative
# to this directory. They are copied after the built-in static files, so a file named
# "default.css" will overwrite the built-in "default.css".
html_css_files = ["css/custom.css"]

# The name of an image file (within the static path) to use as favicon of the docs.
# This file should be a Windows icon file (.ico) being 16x16 or 32x32 pixels large.
html_logo = "_static/images/pytask_w_text.svg"

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
}


def setup(app: sphinx.application.Sphinx) -> None:
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )
