"""
confuse-jsonschema: Convert JSON Schema to Confuse templates.

A Python module for converting JSON Schema definitions into Confuse
configuration templates.
"""

from .to_template import to_template

__version__ = "0.1.0"
__author__ = "Christophe-Marie Duquesne"
__email__ = "chmd@chmd.fr"

__all__ = ["to_template"]
