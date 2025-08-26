"""Tests for custom CPLN exceptions following unit testing best practices."""

import unittest

from cpln.errors import (
    AuthenticationError,
    CPLNError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
)


class TestCPLNError(unittest.TestCase):
    """Test CPLNError base exception class functionality"""

    def setUp(self) -> None:
        """Set up common test data for CPLNError tests"""
        self.test_message = "Test error occurred"
        self.test_status_code = 404
        self.test_request_id = "req-12345"
        self.test_response = {"error": "Resource not found", "code": "NOT_FOUND"}

    def test_cpln_error_with_message_only_stores_basic_info(self) -> None:
        """Test that CPLNError with only message parameter stores and displays correctly"""
        # Act
        error = CPLNError(self.test_message)

        # Assert
        self.assertEqual(error.message, self.test_message)
        self.assertIsNone(error.status_code)
        self.assertIsNone(error.response)
        self.assertIsNone(error.request_id)
        self.assertEqual(str(error), self.test_message)

    def test_cpln_error_with_all_parameters_stores_complete_info(self) -> None:
        """Test that CPLNError stores all provided parameters correctly"""
        # Act
        error = CPLNError(
            message=self.test_message,
            status_code=self.test_status_code,
            response=self.test_response,
            request_id=self.test_request_id,
        )

        # Assert
        self.assertEqual(error.message, self.test_message)
        self.assertEqual(error.status_code, self.test_status_code)
        self.assertEqual(error.response, self.test_response)
        self.assertEqual(error.request_id, self.test_request_id)

    def test_cpln_error_formats_message_with_all_details(self) -> None:
        """Test that CPLNError formats multi-line error message with all details"""
        # Act
        error = CPLNError(
            message=self.test_message,
            status_code=self.test_status_code,
            response=self.test_response,
            request_id=self.test_request_id,
        )
        error_str = str(error)

        # Assert
        self.assertIn(self.test_message, error_str)
        self.assertIn(f"Status code: {self.test_status_code}", error_str)
        self.assertIn(f"Request ID: {self.test_request_id}", error_str)
        self.assertIn(f"Response: {self.test_response}", error_str)

    def test_cpln_error_with_status_code_only_includes_status_in_message(self) -> None:
        """Test that CPLNError includes status code in message when only status is provided"""
        # Act
        error = CPLNError(self.test_message, status_code=self.test_status_code)
        error_str = str(error)

        # Assert
        self.assertIn(self.test_message, error_str)
        self.assertIn(f"Status code: {self.test_status_code}", error_str)
        self.assertNotIn("Request ID:", error_str)
        self.assertNotIn("Response:", error_str)

    def test_cpln_error_with_request_id_only_includes_request_id_in_message(
        self,
    ) -> None:
        """Test that CPLNError includes request ID in message when only request ID is provided"""
        # Act
        error = CPLNError(self.test_message, request_id=self.test_request_id)
        error_str = str(error)

        # Assert
        self.assertIn(self.test_message, error_str)
        self.assertIn(f"Request ID: {self.test_request_id}", error_str)
        self.assertNotIn("Status code:", error_str)
        self.assertNotIn("Response:", error_str)

    def test_cpln_error_with_response_only_includes_response_in_message(self) -> None:
        """Test that CPLNError includes response in message when only response is provided"""
        # Act
        error = CPLNError(self.test_message, response=self.test_response)
        error_str = str(error)

        # Assert
        self.assertIn(self.test_message, error_str)
        self.assertIn(f"Response: {self.test_response}", error_str)
        self.assertNotIn("Status code:", error_str)
        self.assertNotIn("Request ID:", error_str)

    def test_cpln_error_with_empty_message_handles_gracefully(self) -> None:
        """Test that CPLNError handles empty message gracefully"""
        # Act
        error = CPLNError("", status_code=self.test_status_code)
        error_str = str(error)

        # Assert
        self.assertEqual(error.message, "")
        self.assertIn(f"Status code: {self.test_status_code}", error_str)

    def test_cpln_error_with_zero_status_code_includes_status(self) -> None:
        """Test that CPLNError includes status code even when it's 0"""
        # Act
        error = CPLNError(self.test_message, status_code=0)
        error_str = str(error)

        # Assert
        self.assertEqual(error.status_code, 0)
        self.assertIn("Status code: 0", error_str)

    def test_cpln_error_inherits_from_exception(self) -> None:
        """Test that CPLNError properly inherits from Exception"""
        # Act
        error = CPLNError(self.test_message)

        # Assert
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, CPLNError)

    def test_cpln_error_with_complex_response_object_formats_correctly(self) -> None:
        """Test that CPLNError handles complex response objects in formatting"""
        # Arrange
        complex_response = {
            "errors": ["Field is required", "Invalid format"],
            "metadata": {"timestamp": "2023-01-01T00:00:00Z"},
            "nested": {"data": {"values": [1, 2, 3]}},
        }

        # Act
        error = CPLNError(self.test_message, response=complex_response)
        error_str = str(error)

        # Assert
        self.assertIn(str(complex_response), error_str)


class TestAuthenticationError(unittest.TestCase):
    """Test AuthenticationError exception class"""

    def test_authentication_error_with_default_message_uses_standard_text(self) -> None:
        """Test that AuthenticationError uses default message when none provided"""
        # Act
        error = AuthenticationError()

        # Assert
        self.assertEqual(error.message, "Authentication failed")
        self.assertIn("Authentication failed", str(error))

    def test_authentication_error_with_custom_message_uses_provided_text(self) -> None:
        """Test that AuthenticationError uses custom message when provided"""
        # Arrange
        custom_message = "Invalid API token provided"

        # Act
        error = AuthenticationError(message=custom_message)

        # Assert
        self.assertEqual(error.message, custom_message)
        self.assertIn(custom_message, str(error))

    def test_authentication_error_with_all_parameters_stores_complete_info(
        self,
    ) -> None:
        """Test that AuthenticationError accepts and stores all CPLNError parameters"""
        # Arrange
        message = "Token expired"
        status_code = 401
        response = {"error": "token_expired"}
        request_id = "auth-req-123"

        # Act
        error = AuthenticationError(
            message=message,
            status_code=status_code,
            response=response,
            request_id=request_id,
        )

        # Assert
        self.assertEqual(error.message, message)
        self.assertEqual(error.status_code, status_code)
        self.assertEqual(error.response, response)
        self.assertEqual(error.request_id, request_id)

    def test_authentication_error_inherits_from_cpln_error(self) -> None:
        """Test that AuthenticationError properly inherits from CPLNError"""
        # Act
        error = AuthenticationError()

        # Assert
        self.assertIsInstance(error, CPLNError)
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, AuthenticationError)


class TestValidationError(unittest.TestCase):
    """Test ValidationError exception class"""

    def test_validation_error_with_default_message_uses_standard_text(self) -> None:
        """Test that ValidationError uses default message when none provided"""
        # Act
        error = ValidationError()

        # Assert
        self.assertEqual(error.message, "Validation error")
        self.assertIn("Validation error", str(error))

    def test_validation_error_with_custom_message_uses_provided_text(self) -> None:
        """Test that ValidationError uses custom message when provided"""
        # Arrange
        custom_message = "Required field 'name' is missing"

        # Act
        error = ValidationError(message=custom_message)

        # Assert
        self.assertEqual(error.message, custom_message)
        self.assertIn(custom_message, str(error))

    def test_validation_error_with_response_details_includes_validation_info(
        self,
    ) -> None:
        """Test that ValidationError includes validation details from response"""
        # Arrange
        message = "Invalid input data"
        response = {"errors": {"name": ["is required"], "email": ["invalid format"]}}

        # Act
        error = ValidationError(message=message, status_code=400, response=response)
        error_str = str(error)

        # Assert
        self.assertIn(message, error_str)
        self.assertIn("Status code: 400", error_str)
        self.assertIn(str(response), error_str)

    def test_validation_error_inherits_from_cpln_error(self) -> None:
        """Test that ValidationError properly inherits from CPLNError"""
        # Act
        error = ValidationError()

        # Assert
        self.assertIsInstance(error, CPLNError)
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, ValidationError)


class TestResourceNotFoundError(unittest.TestCase):
    """Test ResourceNotFoundError exception class"""

    def test_resource_not_found_error_with_default_message_uses_standard_text(
        self,
    ) -> None:
        """Test that ResourceNotFoundError uses default message when none provided"""
        # Act
        error = ResourceNotFoundError()

        # Assert
        self.assertEqual(error.message, "Resource not found")
        self.assertIn("Resource not found", str(error))

    def test_resource_not_found_error_with_custom_message_uses_provided_text(
        self,
    ) -> None:
        """Test that ResourceNotFoundError uses custom message when provided"""
        # Arrange
        custom_message = "Workload 'my-app' not found in organization 'my-org'"

        # Act
        error = ResourceNotFoundError(message=custom_message)

        # Assert
        self.assertEqual(error.message, custom_message)
        self.assertIn(custom_message, str(error))

    def test_resource_not_found_error_with_404_status_code_formats_correctly(
        self,
    ) -> None:
        """Test that ResourceNotFoundError formats correctly with 404 status code"""
        # Arrange
        message = "GVC 'prod' not found"
        status_code = 404
        request_id = "find-req-456"

        # Act
        error = ResourceNotFoundError(
            message=message, status_code=status_code, request_id=request_id
        )
        error_str = str(error)

        # Assert
        self.assertIn(message, error_str)
        self.assertIn("Status code: 404", error_str)
        self.assertIn(f"Request ID: {request_id}", error_str)

    def test_resource_not_found_error_inherits_from_cpln_error(self) -> None:
        """Test that ResourceNotFoundError properly inherits from CPLNError"""
        # Act
        error = ResourceNotFoundError()

        # Assert
        self.assertIsInstance(error, CPLNError)
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, ResourceNotFoundError)


class TestRateLimitError(unittest.TestCase):
    """Test RateLimitError exception class"""

    def test_rate_limit_error_with_default_message_uses_standard_text(self) -> None:
        """Test that RateLimitError uses default message when none provided"""
        # Act
        error = RateLimitError()

        # Assert
        self.assertEqual(error.message, "Rate limit exceeded")
        self.assertIn("Rate limit exceeded", str(error))

    def test_rate_limit_error_with_custom_message_uses_provided_text(self) -> None:
        """Test that RateLimitError uses custom message when provided"""
        # Arrange
        custom_message = "API rate limit exceeded. Retry after 60 seconds"

        # Act
        error = RateLimitError(message=custom_message)

        # Assert
        self.assertEqual(error.message, custom_message)
        self.assertIn(custom_message, str(error))

    def test_rate_limit_error_with_429_status_code_formats_correctly(self) -> None:
        """Test that RateLimitError formats correctly with 429 status code"""
        # Arrange
        message = "Too many requests"
        status_code = 429
        response = {"retry_after": 60, "limit": 100, "remaining": 0}

        # Act
        error = RateLimitError(
            message=message, status_code=status_code, response=response
        )
        error_str = str(error)

        # Assert
        self.assertIn(message, error_str)
        self.assertIn("Status code: 429", error_str)
        self.assertIn(str(response), error_str)

    def test_rate_limit_error_inherits_from_cpln_error(self) -> None:
        """Test that RateLimitError properly inherits from CPLNError"""
        # Act
        error = RateLimitError()

        # Assert
        self.assertIsInstance(error, CPLNError)
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, RateLimitError)


class TestExceptionHierarchy(unittest.TestCase):
    """Test the exception inheritance hierarchy and relationships"""

    def test_all_specific_exceptions_inherit_from_cpln_error(self) -> None:
        """Test that all specific exception classes properly inherit from CPLNError"""
        # Arrange
        exception_classes = [
            AuthenticationError,
            ValidationError,
            ResourceNotFoundError,
            RateLimitError,
        ]

        for exc_class in exception_classes:
            with self.subTest(exception_class=exc_class.__name__):
                # Act
                error = exc_class()

                # Assert
                self.assertIsInstance(error, CPLNError)
                self.assertIsInstance(error, Exception)

    def test_all_exceptions_can_be_instantiated_with_full_parameters(self) -> None:
        """Test that all exception classes accept the full parameter set"""
        # Arrange
        exception_classes = [
            CPLNError,
            AuthenticationError,
            ValidationError,
            ResourceNotFoundError,
            RateLimitError,
        ]
        test_message = "Test error"
        test_status_code = 400
        test_response = {"error": "test"}
        test_request_id = "test-123"

        for exc_class in exception_classes:
            with self.subTest(exception_class=exc_class.__name__):
                # Act
                error = exc_class(
                    message=test_message,
                    status_code=test_status_code,
                    response=test_response,
                    request_id=test_request_id,
                )

                # Assert
                self.assertEqual(error.message, test_message)
                self.assertEqual(error.status_code, test_status_code)
                self.assertEqual(error.response, test_response)
                self.assertEqual(error.request_id, test_request_id)

    def test_exception_default_messages_are_unique(self) -> None:
        """Test that each specific exception class has its own default message"""
        # Act & Assert
        auth_error = AuthenticationError()
        validation_error = ValidationError()
        not_found_error = ResourceNotFoundError()
        rate_limit_error = RateLimitError()

        # Assert all messages are different
        messages = [
            auth_error.message,
            validation_error.message,
            not_found_error.message,
            rate_limit_error.message,
        ]

        self.assertEqual(len(messages), len(set(messages)))  # All unique
        self.assertEqual(auth_error.message, "Authentication failed")
        self.assertEqual(validation_error.message, "Validation error")
        self.assertEqual(not_found_error.message, "Resource not found")
        self.assertEqual(rate_limit_error.message, "Rate limit exceeded")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for exception handling"""

    def test_exceptions_with_none_parameters_handle_gracefully(self) -> None:
        """Test that exceptions handle None values gracefully"""
        # Act
        error = CPLNError(
            message="Test", status_code=None, response=None, request_id=None
        )

        # Assert
        self.assertIsNone(error.status_code)
        self.assertIsNone(error.response)
        self.assertIsNone(error.request_id)
        self.assertEqual(str(error), "Test")  # Only message in output

    def test_exceptions_with_empty_string_parameters_handle_gracefully(self) -> None:
        """Test that exceptions handle empty string values gracefully"""
        # Act
        error = CPLNError(message="Test", request_id="")

        # Assert
        self.assertEqual(error.request_id, "")
        # Empty request_id should not appear in formatted message
        self.assertEqual(str(error), "Test")

    def test_exceptions_with_very_long_messages_handle_gracefully(self) -> None:
        """Test that exceptions handle very long error messages"""
        # Arrange
        long_message = "A" * 1000  # 1000 character message

        # Act
        error = CPLNError(long_message)

        # Assert
        self.assertEqual(error.message, long_message)
        self.assertEqual(str(error), long_message)

    def test_exceptions_with_special_characters_in_message_handle_gracefully(
        self,
    ) -> None:
        """Test that exceptions handle special characters in messages"""
        # Arrange
        special_message = "Error with unicode: àáâã and symbols: !@#$%^&*()"

        # Act
        error = CPLNError(special_message)

        # Assert
        self.assertEqual(error.message, special_message)
        self.assertIn(special_message, str(error))


if __name__ == "__main__":
    unittest.main()  # type: ignore
