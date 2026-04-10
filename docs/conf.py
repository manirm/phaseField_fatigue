# Configuration file for the Sphinx documentation builder.
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Phase-Field Fatigue Suite'
copyright = '2026, Mohammed Maniruzzaman'
author = 'Mohammed Maniruzzaman'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster' # We'll use Alabaster as default, compatible with RTD
html_static_path = ['_static']

html_theme_options = {
    'description': 'Professional 3D Phase-Field Fracture Mechanics Suite',
    'fixed_sidebar': True,
    'badge_branch': 'main',
    'github_user': 'manirm',
    'github_repo': 'phaseField_fatigue',
}
