# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PEtab GUI'
copyright = '2025, Paul Jonas Jost, Frank T. Bergmann'
author = 'Paul Jonas Jost, Frank T. Bergmann'
release = '0.1.3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon',      # For Google/Numpy style docstrings
    'sphinx.ext.viewcode',      # Add links to highlighted source code
    'sphinx.ext.githubpages',   # For publishing on GitHub Pages
    'sphinx.ext.todo',          # Support todo items
    'sphinx.ext.mathjax',       # For LaTeX math rendering
    'myst_parser'               # For Markdown support
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": -1,
    "logo_only": True,
}

# Title
html_title = "PEtab GUI documentation"
# Navigation bar title
html_short_title = "PEtab GUI"

html_static_path = []
