"""
Custom exceptions for the CPLN Python client.
"""

from typing import Any, Dict, Optional


class CPLNError(Exception):
    """
    Base exception class for CPLN client errors.

    This exception is raised when there's an error interacting with the CPLN API
    or when there's an error in the client itself.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
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
        if status_code:
            error_parts.append(f"Status code: {status_code}")
        if request_id:
            error_parts.append(f"Request ID: {request_id}")
        if response:
            error_parts.append(f"Response: {response}")

        super().__init__("\n".join(error_parts))


class AuthenticationError(CPLNError):
    """Raised when there's an authentication error with the CPLN API."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


class ValidationError(CPLNError):
    """Raised when there's a validation error in the request parameters."""

    def __init__(
        self,
        message: str = "Validation error",
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


class ResourceNotFoundError(CPLNError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)


class RateLimitError(CPLNError):
    """Raised when the API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code, response, request_id)
