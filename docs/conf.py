import os
import sys

sys.path.insert(0, os.path.abspath(".."))  # Point to the project root

project = "KolmogorovComplexityEstimatorPythonPackage"
copyright = "2024, Your Name"  # Replace with actual author/year
author = "Your Name"  # Replace with actual author
release = "1.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # For Google and NumPy style docstrings
    "sphinx.ext.viewcode",  # To add links to source code
    "sphinx.ext.intersphinx",  # For linking to other projects' docs
    # Add other extensions here if needed, e.g., 'sphinx_rtd_theme'
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"  # or 'sphinx_rtd_theme' if installed
# html_theme_options = {} # Theme-specific options
# html_static_path = ['_static'] # For custom CSS or JS

# Autodoc options
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# Napoleon settings (for Google/NumPy docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Intersphinx mapping
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
