from enum import Enum
from typing import Dict, Optional


class PostgresExitCode(Enum):
    """Enumeration of PostgreSQL command exit codes and their meanings.
    This class handles exit codes for both pg_dump and pg_restore commands."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    CONNECTION_ERROR = 3
    PERMISSION_DENIED = 4
    FILE_ERROR = 5
    PROCESS_INTERRUPTED = 130
    UNKNOWN_ERROR = 255

    @classmethod
    def get_message(cls, code: int, command: str = "PostgreSQL command") -> str:
        """Get the human-readable message for an exit code.

        Args:
            code (int): The exit code to get the message for
            command (str): The name of the PostgreSQL command (e.g., 'pg_dump', 'pg_restore')
        """
        messages: Dict[int, str] = {
            cls.SUCCESS.value: f"The {command} completed successfully.",
            cls.GENERAL_ERROR.value: f"An error occurred while executing {command}. This could be due to invalid command-line arguments, internal errors, or other issues.",
            cls.INVALID_ARGUMENTS.value: f"Invalid command-line arguments were provided to {command}.",
            cls.CONNECTION_ERROR.value: "Failed to connect to the database server. Check your connection parameters and ensure the server is running.",
            cls.PERMISSION_DENIED.value: f"Permission denied while accessing the database or {command} files.",
            cls.FILE_ERROR.value: f"Error accessing files for {command}. Check file permissions and available disk space.",
            cls.PROCESS_INTERRUPTED.value: f"The {command} process was interrupted by a signal (e.g., Ctrl+C).",
            cls.UNKNOWN_ERROR.value: f"An unknown error occurred while executing {command}.",
        }
        return messages.get(code, f"Unknown {command} exit code: {code}")

    @classmethod
    def is_error(cls, code: int) -> bool:
        """Check if an exit code indicates an error."""
        return code != cls.SUCCESS.value

    @classmethod
    def get_error_type(cls, code: int) -> Optional[str]:
        """Get the type of error for an exit code."""
        error_types: Dict[int, str] = {
            cls.GENERAL_ERROR.value: "General Error",
            cls.INVALID_ARGUMENTS.value: "Invalid Arguments",
            cls.CONNECTION_ERROR.value: "Connection Error",
            cls.PERMISSION_DENIED.value: "Permission Denied",
            cls.FILE_ERROR.value: "File Error",
            cls.PROCESS_INTERRUPTED.value: "Process Interrupted",
            cls.UNKNOWN_ERROR.value: "Unknown Error",
        }
        return error_types.get(code)
