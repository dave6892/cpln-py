from enum import Enum
from typing import Dict, Optional


class GenericExitCode(Enum):
    """Enumeration of generic exit codes and their meanings."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    PERMISSION_DENIED = 3
    FILE_NOT_FOUND = 4
    PROCESS_INTERRUPTED = 130
    UNKNOWN_ERROR = 255

    @classmethod
    def get_message(cls, code: int) -> str:
        """Get the human-readable message for an exit code."""
        messages: Dict[int, str] = {
            cls.SUCCESS.value: "The command completed successfully.",
            cls.GENERAL_ERROR.value: "An error occurred while executing the command.",
            cls.INVALID_ARGUMENTS.value: "Invalid arguments were provided to the command.",
            cls.PERMISSION_DENIED.value: "Permission denied while executing the command.",
            cls.FILE_NOT_FOUND.value: "A required file or directory was not found.",
            cls.PROCESS_INTERRUPTED.value: "The process was interrupted by a signal.",
            cls.UNKNOWN_ERROR.value: "An unknown error occurred while executing the command.",
        }
        return messages.get(code, f"Unknown exit code: {code}")

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
            cls.PERMISSION_DENIED.value: "Permission Denied",
            cls.FILE_NOT_FOUND.value: "File Not Found",
            cls.PROCESS_INTERRUPTED.value: "Process Interrupted",
            cls.UNKNOWN_ERROR.value: "Unknown Error",
        }
        return error_types.get(code)
