"""Exit code definitions for various command-line tools.

This module provides enumerations and utilities for interpreting exit codes
from various command-line tools that may be executed via the WebSocket API.
"""

from .aws import AwsExitCode
from .generic import GenericExitCode
from .postgres import PostgresExitCode

__all__ = ["AwsExitCode", "GenericExitCode", "PostgresExitCode"]
