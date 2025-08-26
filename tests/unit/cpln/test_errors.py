"""Tests for errors module following unit testing best practices."""

import unittest
from unittest.mock import Mock

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


class TestAPIError(unittest.TestCase):
    """Test APIError exception class for HTTP response error handling"""

    def setUp(self) -> None:
        """Set up common test data for APIError tests"""
        self.test_message = "Test API error"
        self.test_url = "http://test.com/api"
        self.test_explanation = "Invalid parameters provided"

    def _create_mock_response(
        self, status_code: int, reason: str = "Test Reason"
    ) -> Mock:
        """Helper method to create mock HTTP response objects"""
        response = Mock()
        response.status_code = status_code
        response.url = self.test_url
        response.reason = reason
        return response

    # =======================================
    #  Message Formatting Tests
    # =======================================
    def test_api_error_with_client_error_formats_message_correctly(self) -> None:
        """Test that APIError properly formats client error messages (4xx status codes)"""
        response = self._create_mock_response(404, "Not Found")

        error = APIError(self.test_message, response=response)
        error_str = str(error)

        self.assertIn("404 Client Error", error_str)
        self.assertIn(self.test_url, error_str)
        self.assertIn("Not Found", error_str)

    def test_api_error_with_server_error_formats_message_correctly(self) -> None:
        """Test that APIError properly formats server error messages (5xx status codes)"""
        response = self._create_mock_response(500, "Internal Server Error")

        error = APIError(self.test_message, response=response)
        error_str = str(error)

        self.assertIn("500 Server Error", error_str)
        self.assertIn(self.test_url, error_str)
        self.assertIn("Internal Server Error", error_str)

    def test_api_error_includes_explanation_when_provided(self) -> None:
        """Test that APIError includes explanation text in error message when provided"""
        response = self._create_mock_response(400, "Bad Request")

        error = APIError(
            self.test_message, response=response, explanation=self.test_explanation
        )
        error_str = str(error)

        self.assertIn(self.test_explanation, error_str)
        self.assertIn("400 Client Error", error_str)

    def test_api_error_without_response_creates_basic_error(self) -> None:
        """Test that APIError can be created without response object for basic error handling"""
        error = APIError(self.test_message)

        self.assertEqual(str(error), self.test_message)
        self.assertIsNone(error.status_code)

    # =======================================
    #  Status Code Property Tests
    # =======================================
    def test_status_code_property_returns_response_status_code(self) -> None:
        """Test that status_code property correctly returns the HTTP status code from response"""
        response = self._create_mock_response(404)

        error = APIError(self.test_message, response=response)

        self.assertEqual(error.status_code, 404)

    def test_status_code_property_returns_none_without_response(self) -> None:
        """Test that status_code property returns None when no response object is provided"""
        error = APIError(self.test_message)

        self.assertIsNone(error.status_code)

    # =======================================
    #  Client Error Detection Tests
    # =======================================
    def test_is_client_error_returns_true_for_4xx_status_codes(self) -> None:
        """Test that is_client_error correctly identifies 4xx status codes as client errors"""
        test_cases = [400, 401, 403, 404, 422, 429]

        for status_code in test_cases:
            with self.subTest(status_code=status_code):
                response = self._create_mock_response(status_code)
                error = APIError(self.test_message, response=response)

                self.assertTrue(error.is_client_error())

    def test_is_client_error_returns_false_for_non_4xx_status_codes(self) -> None:
        """Test that is_client_error returns false for non-4xx status codes"""
        test_cases = [200, 201, 301, 500, 502, 503]

        for status_code in test_cases:
            with self.subTest(status_code=status_code):
                response = self._create_mock_response(status_code)
                error = APIError(self.test_message, response=response)

                self.assertFalse(error.is_client_error())

    def test_is_client_error_returns_false_without_response(self) -> None:
        """Test that is_client_error returns false when no response object is available"""
        error = APIError(self.test_message)

        self.assertFalse(error.is_client_error())

    # =======================================
    #  Server Error Detection Tests
    # =======================================
    def test_is_server_error_returns_true_for_5xx_status_codes(self) -> None:
        """Test that is_server_error correctly identifies 5xx status codes as server errors"""
        test_cases = [500, 501, 502, 503, 504, 505]

        for status_code in test_cases:
            with self.subTest(status_code=status_code):
                response = self._create_mock_response(status_code)
                error = APIError(self.test_message, response=response)

                self.assertTrue(error.is_server_error())

    def test_is_server_error_returns_false_for_non_5xx_status_codes(self) -> None:
        """Test that is_server_error returns false for non-5xx status codes"""
        test_cases = [200, 201, 301, 400, 404, 422]

        for status_code in test_cases:
            with self.subTest(status_code=status_code):
                response = self._create_mock_response(status_code)
                error = APIError(self.test_message, response=response)

                self.assertFalse(error.is_server_error())

    def test_is_server_error_returns_false_without_response(self) -> None:
        """Test that is_server_error returns false when no response object is available"""
        error = APIError(self.test_message)

        self.assertFalse(error.is_server_error())

    # =======================================
    #  Error Detection Tests
    # =======================================
    def test_is_error_returns_true_for_error_status_codes(self) -> None:
        """Test that is_error correctly identifies 4xx and 5xx status codes as errors"""
        error_status_codes = [400, 401, 404, 422, 500, 502, 503]

        for status_code in error_status_codes:
            with self.subTest(status_code=status_code):
                response = self._create_mock_response(status_code)
                error = APIError(self.test_message, response=response)

                self.assertTrue(error.is_error())

    def test_is_error_returns_false_for_success_status_codes(self) -> None:
        """Test that is_error returns false for successful 2xx and 3xx status codes"""
        success_status_codes = [200, 201, 202, 204, 301, 302, 304]

        for status_code in success_status_codes:
            with self.subTest(status_code=status_code):
                response = self._create_mock_response(status_code)
                error = APIError(self.test_message, response=response)

                self.assertFalse(error.is_error())

    def test_api_error_with_edge_case_status_codes(self) -> None:
        """Test APIError behavior with edge case status codes like 1xx"""
        response = self._create_mock_response(100, "Continue")

        error = APIError(self.test_message, response=response)

        self.assertEqual(error.status_code, 100)
        self.assertFalse(error.is_client_error())
        self.assertFalse(error.is_server_error())
        self.assertFalse(error.is_error())


class TestBuildError(unittest.TestCase):
    """Test BuildError exception class for build failure handling"""

    def test_build_error_stores_message_and_build_log(self) -> None:
        """Test that BuildError properly stores error message and build log"""
        # Arrange
        message = "Build failed"
        build_log = "detailed build log content"

        # Act
        error = BuildError(message, build_log)

        # Assert
        self.assertEqual(error.msg, message)
        self.assertEqual(error.build_log, build_log)
        self.assertEqual(str(error), message)

    def test_build_error_with_empty_build_log(self) -> None:
        """Test BuildError behavior when build log is empty"""
        message = "Build failed"
        build_log = ""

        error = BuildError(message, build_log)

        self.assertEqual(error.build_log, "")
        self.assertEqual(str(error), message)

    def test_build_error_with_none_build_log(self) -> None:
        """Test BuildError behavior when build log is None"""
        message = "Build failed"

        error = BuildError(message, None)

        self.assertIsNone(error.build_log)
        self.assertEqual(str(error), message)


class TestContextErrors(unittest.TestCase):
    """Test context-related exception classes"""

    def test_missing_context_parameter_stores_parameter_name(self) -> None:
        """Test that MissingContextParameter stores and formats parameter name correctly"""
        param_name = "test_param"

        error = MissingContextParameter(param_name)

        self.assertEqual(error.param, param_name)
        self.assertEqual(str(error), f"missing parameter: {param_name}")

    def test_context_exception_stores_and_displays_message(self) -> None:
        """Test that ContextException properly stores and displays error message"""
        message = "Context error message"

        error = ContextException(message)

        self.assertEqual(error.msg, message)
        self.assertEqual(str(error), message)

    def test_context_not_found_formats_context_name_correctly(self) -> None:
        """Test that ContextNotFound formats context name in error message"""
        context_name = "test_context"

        error = ContextNotFound(context_name)

        self.assertEqual(error.name, context_name)
        self.assertEqual(str(error), f"context '{context_name}' not found")

    def test_context_not_found_with_empty_context_name(self) -> None:
        """Test ContextNotFound behavior with empty context name"""
        context_name = ""

        error = ContextNotFound(context_name)

        self.assertEqual(error.name, "")
        self.assertEqual(str(error), "context '' not found")


class TestWebSocketErrors(unittest.TestCase):
    """Test WebSocket-related exception classes"""

    def test_websocket_error_inheritance_and_basic_functionality(self) -> None:
        """Test that WebSocketError is properly instantiated and displays message"""
        message = "WebSocket connection failed"

        error = WebSocketError(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_websocket_connection_error_inheritance(self) -> None:
        """Test that WebSocketConnectionError is a proper WebSocket error"""
        message = "Connection refused"

        error = WebSocketConnectionError(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_websocket_message_error_inheritance(self) -> None:
        """Test that WebSocketMessageError properly handles message errors"""
        message = "Invalid message format"

        error = WebSocketMessageError(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_websocket_exit_code_error_inheritance(self) -> None:
        """Test that WebSocketExitCodeError handles exit code errors"""
        message = "Process exited with non-zero code"

        error = WebSocketExitCodeError(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_websocket_operation_error_inheritance(self) -> None:
        """Test that WebSocketOperationError handles operation errors"""
        message = "Operation failed"

        error = WebSocketOperationError(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))


class TestValidationErrors(unittest.TestCase):
    """Test validation-related exception classes"""

    def test_invalid_argument_displays_message(self) -> None:
        """Test that InvalidArgument properly displays error message"""
        message = "Invalid argument provided"

        error = InvalidArgument(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_invalid_version_displays_message(self) -> None:
        """Test that InvalidVersion properly displays version error message"""
        message = "Version 1.0.0 is not supported"

        error = InvalidVersion(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_invalid_repository_displays_message(self) -> None:
        """Test that InvalidRepository properly displays repository error message"""
        message = "Repository URL is malformed"

        error = InvalidRepository(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_invalid_config_file_displays_message(self) -> None:
        """Test that InvalidConfigFile properly displays config error message"""
        message = "Configuration file is invalid"

        error = InvalidConfigFile(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))


class TestResourceErrors(unittest.TestCase):
    """Test resource-related exception classes"""

    def test_not_found_displays_message(self) -> None:
        """Test that NotFound exception properly displays error message"""
        message = "Resource not found"

        error = NotFound(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_null_resource_displays_message(self) -> None:
        """Test that NullResource exception properly displays error message"""
        message = "Resource is null"

        error = NullResource(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_image_not_found_displays_message(self) -> None:
        """Test that ImageNotFound exception properly displays error message"""
        message = "Docker image not found"

        error = ImageNotFound(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_image_load_error_displays_message(self) -> None:
        """Test that ImageLoadError exception properly displays error message"""
        message = "Failed to load image"

        error = ImageLoadError(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))


class TestGeneralErrors(unittest.TestCase):
    """Test general exception classes"""

    def test_cpln_exception_base_functionality(self) -> None:
        """Test that CPLNException serves as base exception with proper message handling"""
        message = "General CPLN error"

        error = CPLNException(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))

    def test_deprecated_method_displays_message(self) -> None:
        """Test that DeprecatedMethod exception properly displays deprecation message"""
        message = "This method is deprecated"

        error = DeprecatedMethod(message)

        self.assertIsInstance(error, Exception)
        self.assertIn(message, str(error))


class TestExceptionInstantiation(unittest.TestCase):
    """Test that all exception classes can be properly instantiated and inherit from Exception"""

    def test_all_exceptions_inherit_from_exception_and_display_messages(self) -> None:
        """Test that all exception classes properly inherit from Exception and display messages"""
        exception_classes = [
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
        test_message = "Test error message"

        for exc_class in exception_classes:
            with self.subTest(exception_class=exc_class.__name__):
                error = exc_class(test_message)

                self.assertIsInstance(error, Exception)
                self.assertIn(test_message, str(error))

    def test_exception_classes_with_empty_messages(self) -> None:
        """Test exception behavior with empty error messages"""
        exception_classes = [CPLNException, NotFound, InvalidArgument]

        for exc_class in exception_classes:
            with self.subTest(exception_class=exc_class.__name__):
                error = exc_class("")

                self.assertIsInstance(error, Exception)
                # Empty string should still be handleable
                self.assertEqual(str(error), "")


if __name__ == "__main__":
    unittest.main()  # type: ignore
