"""
Report generation module. Creates from templates using jinja.
"""

__all__ = (
    'IFileGenerator',
    'HTMLGenerator',
)

from .base_generator import IFileGenerator
from .html_generator import HTMLGenerator
