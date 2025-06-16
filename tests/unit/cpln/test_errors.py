"""Tests for errors module."""

import unittest.mock as mock

from cpln.errors import (
    APIError,
    BuildError,
    ContextException,
    ContextNotFound,
    CPLNException,
    DeprecatedMethod,
    ImageLoadError,
    ImageNotFound,
    InvalidArgument,
    InvalidConfigFile,
    InvalidRepository,
    InvalidVersion,
    MissingContextParameter,
    NotFound,
    NullResource,
    WebSocketConnectionError,
    WebSocketError,
    WebSocketExitCodeError,
    WebSocketMessageError,
    WebSocketOperationError,
)


class TestAPIError:
    def test_api_error_with_client_error(self):
        """Test APIError formatting for client errors."""
        response = mock.Mock()
        response.status_code = 404
        response.url = "http://test.com/api"
        response.reason = "Not Found"

        error = APIError("Test error", response=response)
        error_str = str(error)

        assert "404 Client Error" in error_str
        assert "http://test.com/api" in error_str
        assert "Not Found" in error_str

    def test_api_error_with_server_error(self):
        """Test APIError formatting for server errors."""
        response = mock.Mock()
        response.status_code = 500
        response.url = "http://test.com/api"
        response.reason = "Internal Server Error"

        error = APIError("Test error", response=response)
        error_str = str(error)

        assert "500 Server Error" in error_str

    def test_api_error_with_explanation(self):
        """Test APIError with explanation."""
        response = mock.Mock()
        response.status_code = 400
        response.url = "http://test.com/api"
        response.reason = "Bad Request"

        error = APIError(
            "Test error", response=response, explanation="Invalid parameters"
        )
        error_str = str(error)

        assert "Invalid parameters" in error_str

    def test_api_error_status_code_property(self):
        """Test status_code property."""
        response = mock.Mock()
        response.status_code = 404

        error = APIError("Test error", response=response)
        assert error.status_code == 404

        error_no_response = APIError("Test error")
        assert error_no_response.status_code is None

    def test_api_error_is_client_error(self):
        """Test is_client_error method."""
        response = mock.Mock()
        response.status_code = 404

        error = APIError("Test error", response=response)
        assert error.is_client_error() is True

        response.status_code = 500
        assert error.is_client_error() is False

        error_no_response = APIError("Test error")
        assert error_no_response.is_client_error() is False

    def test_api_error_is_server_error(self):
        """Test is_server_error method."""
        response = mock.Mock()
        response.status_code = 500

        error = APIError("Test error", response=response)
        assert error.is_server_error() is True

        response.status_code = 404
        assert error.is_server_error() is False

        error_no_response = APIError("Test error")
        assert error_no_response.is_server_error() is False

    def test_api_error_is_error(self):
        """Test is_error method."""
        response = mock.Mock()
        response.status_code = 404

        error = APIError("Test error", response=response)
        assert error.is_error() is True

        response.status_code = 500
        assert error.is_error() is True

        response.status_code = 200
        assert error.is_error() is False


def test_build_error():
    """Test BuildError with build log."""
    error = BuildError("Build failed", "detailed build log")
    assert error.msg == "Build failed"
    assert error.build_log == "detailed build log"
    assert str(error) == "Build failed"


def test_missing_context_parameter():
    """Test MissingContextParameter error."""
    error = MissingContextParameter("test_param")
    assert error.param == "test_param"
    assert str(error) == "missing parameter: test_param"


def test_context_exception():
    """Test ContextException error."""
    error = ContextException("Context error message")
    assert error.msg == "Context error message"
    assert str(error) == "Context error message"


def test_context_not_found():
    """Test ContextNotFound error."""
    error = ContextNotFound("test_context")
    assert error.name == "test_context"
    assert str(error) == "context 'test_context' not found"


def test_all_simple_exceptions():
    """Test instantiation of simple exception classes."""
    exceptions = [
        CPLNException,
        NotFound,
        ImageNotFound,
        InvalidVersion,
        InvalidRepository,
        InvalidConfigFile,
        InvalidArgument,
        DeprecatedMethod,
        NullResource,
        ImageLoadError,
        WebSocketError,
        WebSocketConnectionError,
        WebSocketMessageError,
        WebSocketExitCodeError,
        WebSocketOperationError,
    ]

    for exc_class in exceptions:
        error = exc_class("Test message")
        assert isinstance(error, Exception)
        assert "Test message" in str(error)
