"""
Modern exception system for the CPLN Python client.

This module contains all custom exceptions for the CPLN client, providing
comprehensive error handling with detailed formatting and metadata support.

Naming Convention:
- "Exception" suffix: Base classes or generic exceptional situations
- "Error" suffix: Specific problems, failures, or mistakes that need handling
"""

from typing import Any, Optional


class CPLNError(Exception):
    """
    Modern base exception class for CPLN client errors.

    This exception provides sophisticated error formatting with optional metadata.
    All other CPLN exceptions inherit from this base class.
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


# Legacy base class for backward compatibility
class CPLNException(Exception):
    """
    Legacy base exception class for backward compatibility.

    New code should use CPLNError instead, but this is maintained
    for compatibility with existing code that expects this name.
    """


# Authentication and Authorization Errors
class AuthenticationError(CPLNError):
    """Raised when there's an authentication failure."""

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
    """Raised when there's a validation error in request parameters."""

    def __init__(
        self,
        message: str = "Validation error",
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


class InvalidArgument(CPLNException):
    """Raised when an invalid argument is provided."""


class InvalidVersion(CPLNException):
    """Raised when an invalid version is specified."""


class InvalidRepository(CPLNException):
    """Raised when an invalid repository is specified."""


class InvalidConfigFile(CPLNException):
    """Raised when a configuration file is invalid."""


# Resource and API Errors
class ResourceNotFoundError(CPLNError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


class NotFound(CPLNException):
    """Legacy: Raised when a resource is not found (404 errors)."""


class ImageNotFound(NotFound):
    """Legacy: Raised when a Docker image is not found."""


class NullResource(CPLNException, ValueError):
    """Raised when a resource is unexpectedly null."""


# Rate Limiting and Throttling Errors
class RateLimitError(CPLNError):
    """Raised when the API rate limit is exceeded."""

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
    """Raised when there's a general API communication error."""

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
    """Raised when there's an error during a build process."""

    def __init__(self, reason, build_log):
        super().__init__(reason)
        self.msg = reason  # Legacy compatibility
        self.build_log = build_log


class ImageLoadError(CPLNException):
    """Raised when there's an error loading an image."""


class DeprecatedMethod(CPLNException):
    """Raised when a deprecated method is called."""


# Context and Parameter Errors
class MissingContextParameter(CPLNException):
    """Raised when a required context parameter is missing."""

    def __init__(self, param):
        self.param = param

    def __str__(self):
        return f"missing parameter: {self.param}"


class ContextException(CPLNException):
    """Raised when there's a context-related error."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ContextNotFound(CPLNException):
    """Raised when a specified context is not found."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"context '{self.name}' not found"


# WebSocket Communication Exceptions (base class uses Exception for generic situations)
class WebSocketException(Exception):
    """
    Base exception class for WebSocket-related exceptional situations.

    Uses 'Exception' suffix as it represents a category of exceptional
    situations that may not all be "errors" (some might be expected states).
    """


class WebSocketError(WebSocketException):
    """Base class for WebSocket communication errors."""


class WebSocketConnectionError(WebSocketError):
    """Raised when there are WebSocket connection failures."""


class WebSocketMessageError(WebSocketError):
    """Raised when there are WebSocket message processing errors."""


class WebSocketExitCodeError(WebSocketMessageError):
    """Raised when a WebSocket process exits with a non-zero code."""


class WebSocketOperationError(WebSocketMessageError):
    """Raised when a WebSocket operation fails to complete."""
