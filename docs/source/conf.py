"""
Sphinx configuration for the Smart Meeting Room backend documentation.

This file configures Sphinx so that it can build HTML documentation
from the docstrings and ``.rst`` files in the project.

The configuration is intentionally lightweight in Commit 2. Later
commits may extend it with additional extensions or HTML themes.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

# Add the project root (two levels up from this file) to sys.path so that
# modules like ``common`` and ``db`` can be imported by autodoc.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Project information
# ---------------------------------------------------------------------------

project = "Smart Meeting Room Backend"
author = "Mayssa Hajj Hassan & Ahmad Abbas"
current_year = datetime.now().year
copyright = f"{current_year}, {author}"

# ---------------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc.typehints",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = ["_build", "Thumbs.db", ".DS_Store"]

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

html_theme = "alabaster"
html_static_path = ["_static"]
html_title = "Smart Meeting Room Backend Documentation"
