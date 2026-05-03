"""Sphinx configuration for Matchstick Man documentation.

See the Sphinx documentation for the full reference:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

# Expose the (eventual) source package to autodoc.
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
project = "Matchstick Man"
author = "Erik S. Bailey"
copyright = f"{datetime.now():%Y}, {author}"  # noqa: A001 - sphinx convention
release = "0.0.1"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "numpydoc",
    "sphinxcontrib.plantuml",
]

# Absolute path to the MacPorts-installed plantuml wrapper.
plantuml = "/opt/local/bin/plantuml"
plantuml_output_format = "svg"

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# numpydoc handles NumPy-style docstring parsing. Disable its class-member
# auto-listing since autodoc already covers that and would otherwise duplicate.
numpydoc_show_class_members = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- HTML output -------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
