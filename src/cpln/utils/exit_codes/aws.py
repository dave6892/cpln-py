from enum import Enum
from typing import Dict, Optional


class AwsExitCode(Enum):
    """Enumeration of common exit codes and their meanings."""

    SUCCESS = 0
    CONFIG_ERROR = 1
    PARSE_ERROR = 2
    SIGINT = 130
    INVALID_SYNTAX = 252
    INVALID_ENV = 253
    SERVICE_ERROR = 254
    GENERAL_ERROR = 255

    @classmethod
    def get_message(cls, code: int) -> str:
        """Get the human-readable message for an exit code."""
        messages: Dict[int, str] = {
            cls.SUCCESS.value: "The command was successful. There were no errors thrown by either the CLI or by the service that the request was made to.",
            cls.CONFIG_ERROR.value: "The configuration file parsed to the CLI was not found or might be corrupt.",
            cls.PARSE_ERROR.value: "The command entered on the command line failed to be parsed. Parsing failures can be caused by, but are not limited to, missing any required subcommands or arguments or using any unknown commands or arguments.",
            cls.SIGINT.value: "The process received a SIGINT (Ctrl-C).",
            cls.INVALID_SYNTAX.value: "Command syntax was invalid, an unknown parameter was provided, or a parameter value was incorrect and prevented the command from running.",
            cls.INVALID_ENV.value: "The system environment or configuration was invalid. While the command provided may be syntactically valid, missing configuration or credentials prevented the command from running.",
            cls.SERVICE_ERROR.value: "The command was successfully parsed and a request was made to the specified service but the service returned an error. This will generally indicate incorrect API usage or other service specific issues.",
            cls.GENERAL_ERROR.value: "General catch-all error. The command may have parsed correctly but an unspecified runtime error occurred when running the command.",
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
            cls.CONFIG_ERROR.value: "Configuration Error",
            cls.PARSE_ERROR.value: "Parse Error",
            cls.SIGINT.value: "Interrupted",
            cls.INVALID_SYNTAX.value: "Syntax Error",
            cls.INVALID_ENV.value: "Environment Error",
            cls.SERVICE_ERROR.value: "Service Error",
            cls.GENERAL_ERROR.value: "General Error",
        }
        return error_types.get(code)
