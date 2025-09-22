"""
confuse-jsonschema: Convert JSON Schema to Confuse templates.

A Python module for converting JSON Schema definitions into Confuse
configuration templates.
"""

from .to_template import to_template
from importlib.metadata import distribution


__version__ = ""
try:
    __version__ = distribution("confuse_jsonschema").version
except importlib.metadata.PackageNotFoundError:
    pass

__author__ = "Christophe-Marie Duquesne"
__email__ = "chmd@chmd.fr"

__all__ = ["to_template"]
