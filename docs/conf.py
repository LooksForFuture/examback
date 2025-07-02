import sphinx_rtd_theme


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'competition'
copyright = '2024, Tapsi Security Team'
author = 'Tapsi Security Team'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon', # برای پشتیبانی از سبک Google و NumPy docstring
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']


html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


html_css_files = [
    'tapsi_sphinx_rtd_theme_custom_style/css/style.css',
]