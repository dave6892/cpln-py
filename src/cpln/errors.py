"""
Specific error classes for the CPLN Python client.

This module contains error classes that represent actual problems, failures,
and mistakes that occur during CPLN operations. These are situations that
typically need to be handled or corrected.

Naming Convention:
- Classes ending in "Error" represent specific problems, failures, or mistakes
- These indicate something went wrong and typically require corrective action
"""

from typing import Any, Optional

from .exceptions import CPLNException, WebSocketException


class CPLNError(Exception):
    """
    Modern base error class for CPLN client errors.

    This error provides sophisticated error formatting with optional metadata.
    All modern CPLN errors should inherit from this base class.

    This represents actual problems or failures that occur during CPLN operations,
    as opposed to exceptional situations that may be part of normal flow.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Initialize a new CPLNError.

        Args:
            message: A human-readable error message
            status_code: HTTP status code if the error came from an API call
            response: The response body if the error came from an API call
            request_id: The request ID if available from the API
        """
        self.message = message
        self.status_code = status_code
        self.response = response
        self.request_id = request_id

        # Construct the full error message
        error_parts = [message]
        if status_code is not None:
            error_parts.append(f"Status code: {status_code}")
        if request_id:
            error_parts.append(f"Request ID: {request_id}")
        if response:
            error_parts.append(f"Response: {response}")

        super().__init__("\n".join(error_parts))


# Authentication and Authorization Errors
class AuthenticationError(CPLNError):
    """
    Raised when authentication fails.

    This error indicates that the provided credentials are invalid,
    expired, or insufficient for the requested operation.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


# Validation and Input Errors
class ValidationError(CPLNError):
    """
    Raised when input validation fails.

    This error indicates that the provided input data does not meet
    the required format, constraints, or business rules.
    """

    def __init__(
        self,
        message: str = "Validation error",
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


# Resource and API Errors
class ResourceNotFoundError(CPLNError):
    """
    Raised when a requested resource cannot be found.

    This error indicates that the system attempted to locate a specific
    resource but was unable to find it.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


# Rate Limiting and Throttling Errors
class RateLimitError(CPLNError):
    """
    Raised when API rate limits are exceeded.

    This error indicates that the client has made too many requests
    in a given time period and must wait before making additional requests.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


# API Communication Errors
class APIError(CPLNError):
    """
    Raised when API communication fails.

    This error represents failures in HTTP communication with the CPLN API,
    including network issues, server errors, and malformed responses.
    """

    def __init__(
        self,
        message: str,
        response=None,
        explanation: Optional[str] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        # Include explanation in the message if provided
        full_message = f"{message} ({explanation})" if explanation else message

        # Handle legacy response parameter for backward compatibility
        if response is not None and hasattr(response, "status_code"):
            status_code = status_code or getattr(response, "status_code", None)

        super().__init__(full_message, status_code, None, request_id)
        self.response = response  # Keep original response object
        self.explanation = explanation

    def __str__(self):
        """Format error message with HTTP details when available."""
        message = super().__str__()

        if self.response and hasattr(self.response, "status_code"):
            status = self.get_status_code()
            if self.is_client_error():
                message = (
                    f"{status} Client Error for "
                    f"{getattr(self.response, 'url', 'unknown')}: "
                    f"{getattr(self.response, 'reason', 'unknown')}"
                )
            elif self.is_server_error():
                message = (
                    f"{status} Server Error for "
                    f"{getattr(self.response, 'url', 'unknown')}: "
                    f"{getattr(self.response, 'reason', 'unknown')}"
                )

        if self.explanation:
            message = f'{message} ("{self.explanation}")'

        return message

    def get_status_code(self):
        """Get status code from response or stored value."""
        if self.response and hasattr(self.response, "status_code"):
            return getattr(self.response, "status_code", None)
        return getattr(self, "status_code", None)

    def is_error(self) -> bool:
        """Check if this represents an HTTP error status."""
        return self.is_client_error() or self.is_server_error()

    def is_client_error(self) -> bool:
        """Check if this represents a 4xx client error."""
        status = self.get_status_code()
        if status is None:
            return False
        return 400 <= status < 500

    def is_server_error(self) -> bool:
        """Check if this represents a 5xx server error."""
        status = self.get_status_code()
        if status is None:
            return False
        return 500 <= status < 600


# Build and Deployment Errors
class BuildError(CPLNException):
    """
    Raised when build processes fail.

    This error indicates that a build operation (such as container image
    building) has failed and cannot be completed.
    """

    def __init__(self, reason, build_log):
        super().__init__(reason)
        self.msg = reason  # Legacy compatibility
        self.build_log = build_log


# WebSocket Communication Errors
class WebSocketError(WebSocketException):
    """
    Base class for WebSocket communication errors.

    This error represents actual problems that occur during WebSocket
    communication, as opposed to expected WebSocket states.
    """


class WebSocketConnectionError(WebSocketError):
    """
    Raised when WebSocket connection fails.

    This error indicates that the client was unable to establish
    or maintain a WebSocket connection to the server.
    """


class WebSocketMessageError(WebSocketError):
    """
    Raised when WebSocket message processing fails.

    This error indicates that there was a problem processing
    a WebSocket message (parsing, format, content, etc.).
    """


class WebSocketExitCodeError(WebSocketMessageError):
    """
    Raised when a WebSocket process exits with a non-zero code.

    This error indicates that a command or process executed via
    WebSocket has failed with a non-zero exit code.
    """


class WebSocketOperationError(WebSocketMessageError):
    """
    Raised when a WebSocket operation fails to complete.

    This error indicates that a WebSocket-based operation
    could not be completed successfully.
    """
