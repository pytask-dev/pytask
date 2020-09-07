# Configuration file for the Sphinx documentation builder.
# This file only contains a selection of the most common options. For a full list see
# the documentation: https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup ------------------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory, add
# these directories to sys.path here. If the directory is relative to the documentation
# root, use os.path.abspath to make it absolute, like shown here.
import os
import sys

import sphinx


sys.path.insert(0, os.path.abspath("../src"))


# -- Project information ---------------------------------------------------------------

project = "pytask"
copyright = "2020, Tobias Raabe"  # noqa: A001
author = "Tobias Raabe"

# The full version, including alpha/beta/rc tags
release = "0.0.5"


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
    "autoapi.extension",
    "sphinx_autodoc_typehints",
]

# List of patterns, relative to source directory, that match files and directories to
# ignore when looking for source files. This pattern also affects html_static_path and
# html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

suppress_warnings = ["ref.python"]

# -- Extensions configuration ----------------------------------------------------------

# Configuration for autodoc.
autosummary_generate = True
add_module_names = False
autodoc_mock_imports = ["attr", "click", "networkx", "pluggy", "pony"]

# Remove prefixed $ for bash, >>> for Python prompts, and In [1]: for IPython prompts.
copybutton_prompt_text = r"\$ |>>> |In \[\d\]: "
copybutton_prompt_is_regexp = True

extlinks = {
    "ghuser": ("https://github.com/%s", "@"),
    "gh": ("https://github.com/pytask-dev/pytask/pull/%s", "#"),
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.8", None),
    "click": ("https://click.palletsprojects.com/en/7.x", None),
    "pluggy": ("https://pluggy.readthedocs.io/en/latest", None),
}

# Configuration for autoapi
autoapi_type = "python"
autoapi_dirs = ["../src"]
autoapi_keep_files = False
autoapi_add_toctree_entry = False


# -- Options for HTML output -----------------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for a list of
# built-in themes.

html_theme = "alabaster"

# Add any paths that contain custom static files (such as style sheets) here, relative
# to this directory. They are copied after the built-in static files, so a file named
# "default.css" will overwrite the built-in "default.css".
html_css_files = ["css/custom.css"]

# The name of an image file (within the static path) to use as favicon of the docs.
# This file should be a Windows icon file (.ico) being 16x16 or 32x32 pixels large.
html_favicon = "_static/images/pytask.ico"  # noqa: E800

html_static_path = ["_static"]

html_theme_options = {
    "extra_nav_links": {"On Github": "https://github.com/pytask-dev/pytask"},
    "logo": "images/pytask_w_text.svg",
    "logo_name": False,
    "github_button": False,
    "github_user": "pytask-dev",
    "github_repo": "pytask",
    "font_family": '"Avenir Next", Calibri, "PT Sans", sans-serif',
    "head_font_family": '"Avenir Next", Calibri, "PT Sans", sans-serif',
}


def setup(app: "sphinx.application.Sphinx") -> None:
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )
