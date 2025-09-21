"""
Setup script for confuse-jsonschema package.
This is a fallback for older build systems that don't support pyproject.toml.
"""

from setuptools import setup, find_packages

setup(
    name="confuse-jsonschema",
    use_scm_version=False,
    packages=find_packages(),
)
