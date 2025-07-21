# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))  # Путь к C:\Users\Lenovo\CurvativeParameter
os.environ['DJANGO_SETTINGS_MODULE'] = 'website.settings'
import django
django.setup()

# -- Project information -----------------------------------------------------

project = 'CurvativeParameter'
copyright = '2025, Alle'
author = 'Alle'
release = '0.2'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',  # Автодокументация
    'sphinx.ext.viewcode',  # Ссылки на исходный код
    'sphinx.ext.napoleon',  # Поддержка Google/Numpy docstrings
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_static_path = ['_static']
language = 'en'