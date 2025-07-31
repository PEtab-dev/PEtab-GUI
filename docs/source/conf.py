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
    'myst_parser'               # For Markdown support
    'sphinx.ext.mathjax',       # For LaTeX math rendering
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
