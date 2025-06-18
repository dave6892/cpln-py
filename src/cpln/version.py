"""Version management for the CPLN Python SDK.

This module attempts to determine the package version by first trying to import
from a generated _version.py file, and falling back to using importlib.metadata
if that fails.
"""

try:
    from ._version import __version__
except ImportError:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("cpln")
    except PackageNotFoundError:
        __version__ = "0.0.0"
