# Configuration file for the Sphinx documentation builder.
# This file only contains a selection of the most common options. For a full list see
# the documentation: https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup ------------------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory, add
# these directories to sys.path here. If the directory is relative to the documentation
# root, use os.path.abspath to make it absolute, like shown here.
import os
import sys


sys.path.insert(0, os.path.abspath(".."))


# -- Project information ---------------------------------------------------------------

project = "pytask"
copyright = "2020, Tobias Raabe"  # noqa: A001
author = "Tobias Raabe"

# The full version, including alpha/beta/rc tags
release = "0.0.1"


# -- General configuration -------------------------------------------------------------

master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be extensions coming
# with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "numpydoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
]

# Add any paths that contain templates here, relative to this directory.

# templates_path = ["_templates"]  # noqa: E800

# List of patterns, relative to source directory, that match files and directories to
# ignore when looking for source files. This pattern also affects html_static_path and
# html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Extensions configuration ----------------------------------------------------------

# Configuration for autodoc
autosummary_generate = True

copybutton_prompt_text = r"\\$ |>>> "
copybutton_prompt_is_regexp = True

extlinks = {
    "ghuser": ("https://github.com/%s", "@"),
    "gh": ("https://github.com/pytask/pytask/pull/%s", "#"),
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.7", None),
}

# Configuration for numpydoc
numpydoc_xref_param_type = True
numpydoc_xref_ignore = {"type", "optional", "default"}


# -- Options for HTML output -----------------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for a list of
# built-in themes.

html_theme = "pydata_sphinx_theme"

# Add any paths that contain custom static files (such as style sheets) here, relative
# to this directory. They are copied after the built-in static files, so a file named
# "default.css" will overwrite the built-in "default.css".
html_css_files = ["css/custom.css"]

html_static_path = ["_static"]

html_theme_options = {
    "github_url": "https://github.com/pytask/pytask",
}
