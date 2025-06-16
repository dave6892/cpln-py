"""Tests for custom CPLN exceptions."""

from cpln.exceptions import (
    AuthenticationError,
    CPLNError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
)


def test_cpln_error_initialization():
    error = CPLNError("Test error", status_code=404, request_id="req-1234")
    assert error.message == "Test error"
    assert error.status_code == 404
    assert error.request_id == "req-1234"
    assert "Test error" in str(error)
    assert "404" in str(error)
    assert "req-1234" in str(error)


def test_authentication_error_default_msg():
    error = AuthenticationError()
    assert "Authentication failed" in str(error)


def test_validation_error_default_msg():
    error = ValidationError()
    assert "Validation error" in str(error)


def test_resource_not_found_error_default_msg():
    error = ResourceNotFoundError()
    assert "Resource not found" in str(error)


def test_rate_limit_error_default_msg():
    error = RateLimitError()
    assert "Rate limit exceeded" in str(error)
