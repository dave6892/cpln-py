"""Tests for environment utility functions following unit testing best practices."""

import os
import unittest
from unittest.mock import patch

from cpln.constants import DEFAULT_CPLN_API_URL
from cpln.utils import kwargs_from_env


class TestKwargsFromEnvBasicFunctionality(unittest.TestCase):
    """Test kwargs_from_env basic functionality and happy path scenarios"""

    def test_kwargs_from_env_with_minimal_required_variables_returns_basic_config(self):
        """Test that kwargs_from_env works with minimal required environment variables"""
        # Arrange
        test_token = "test-minimal-token"
        test_org = "test-minimal-org"

        # Act
        with patch.dict(
            os.environ, {"CPLN_TOKEN": test_token, "CPLN_ORG": test_org}, clear=True
        ):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], test_token)
        self.assertEqual(result["org"], test_org)
        self.assertIn("base_url", result)
        # Optional fields should not be present
        self.assertNotIn("version", result)
        self.assertNotIn("timeout", result)

    def test_kwargs_from_env_with_all_variables_returns_complete_config(self):
        """Test that kwargs_from_env includes all environment variables when present"""
        # Arrange
        test_env = {
            "CPLN_TOKEN": "complete-token",
            "CPLN_ORG": "complete-org",
            "CPLN_BASE_URL": "https://complete-api.cpln.io",
            "CPLN_VERSION": "2.5.0",
            "CPLN_TIMEOUT": "45",
        }

        # Act
        with patch.dict(os.environ, test_env, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], "complete-token")
        self.assertEqual(result["org"], "complete-org")
        self.assertEqual(result["base_url"], "https://complete-api.cpln.io")
        self.assertEqual(result["version"], "2.5.0")
        self.assertEqual(result["timeout"], "45")

    def test_kwargs_from_env_uses_default_base_url_when_not_provided(self):
        """Test that kwargs_from_env uses DEFAULT_CPLN_API_URL when CPLN_BASE_URL is not set"""
        # Arrange
        test_token = "default-url-token"
        test_org = "default-url-org"

        # Act
        with patch.dict(
            os.environ, {"CPLN_TOKEN": test_token, "CPLN_ORG": test_org}, clear=True
        ):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], test_token)
        self.assertEqual(result["org"], test_org)
        self.assertEqual(result["base_url"], DEFAULT_CPLN_API_URL)

    def test_kwargs_from_env_includes_explicit_base_url_when_provided(self):
        """Test that kwargs_from_env uses explicit CPLN_BASE_URL when provided"""
        # Arrange
        custom_base_url = "https://custom-api.example.com"
        test_token = "custom-url-token"
        test_org = "custom-url-org"

        # Act
        with patch.dict(
            os.environ,
            {
                "CPLN_TOKEN": test_token,
                "CPLN_ORG": test_org,
                "CPLN_BASE_URL": custom_base_url,
            },
            clear=True,
        ):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["base_url"], custom_base_url)
        self.assertEqual(result["token"], test_token)
        self.assertEqual(result["org"], test_org)


class TestKwargsFromEnvOptionalParameters(unittest.TestCase):
    """Test kwargs_from_env optional parameter handling"""

    def setUp(self):
        """Set up common test fixtures"""
        self.base_env = {"CPLN_TOKEN": "base-token", "CPLN_ORG": "base-org"}

    def test_kwargs_from_env_includes_version_when_provided(self):
        """Test that kwargs_from_env includes version when CPLN_VERSION is set"""
        # Arrange
        test_version = "3.1.4"
        env_with_version = {**self.base_env, "CPLN_VERSION": test_version}

        # Act
        with patch.dict(os.environ, env_with_version, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["version"], test_version)
        self.assertIn("token", result)
        self.assertIn("org", result)

    def test_kwargs_from_env_excludes_version_when_not_provided(self):
        """Test that kwargs_from_env excludes version when CPLN_VERSION is not set"""
        # Act
        with patch.dict(os.environ, self.base_env, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertNotIn("version", result)
        self.assertIn("token", result)
        self.assertIn("org", result)

    def test_kwargs_from_env_includes_timeout_when_provided(self):
        """Test that kwargs_from_env includes timeout when CPLN_TIMEOUT is set"""
        # Arrange
        test_timeout = "60"
        env_with_timeout = {**self.base_env, "CPLN_TIMEOUT": test_timeout}

        # Act
        with patch.dict(os.environ, env_with_timeout, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["timeout"], test_timeout)
        self.assertIn("token", result)
        self.assertIn("org", result)

    def test_kwargs_from_env_excludes_timeout_when_not_provided(self):
        """Test that kwargs_from_env excludes timeout when CPLN_TIMEOUT is not set"""
        # Act
        with patch.dict(os.environ, self.base_env, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertNotIn("timeout", result)
        self.assertIn("token", result)
        self.assertIn("org", result)

    def test_kwargs_from_env_with_selective_optional_parameters_includes_only_provided(
        self,
    ):
        """Test that kwargs_from_env includes only the optional parameters that are provided"""
        # Arrange - only version, no timeout
        env_with_version_only = {**self.base_env, "CPLN_VERSION": "2.0.0"}

        # Act
        with patch.dict(os.environ, env_with_version_only, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertIn("version", result)
        self.assertEqual(result["version"], "2.0.0")
        self.assertNotIn("timeout", result)
        self.assertIn("token", result)
        self.assertIn("org", result)


class TestKwargsFromEnvErrorHandling(unittest.TestCase):
    """Test kwargs_from_env error handling and validation"""

    def test_kwargs_from_env_with_missing_token_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_TOKEN is missing"""
        # Arrange
        env_missing_token = {"CPLN_ORG": "test-org"}

        # Act & Assert
        with patch.dict(os.environ, env_missing_token, clear=True):
            with self.assertRaises(ValueError) as context:
                kwargs_from_env()

            self.assertIn("CPLN_TOKEN", str(context.exception))

    def test_kwargs_from_env_with_missing_org_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_ORG is missing"""
        # Arrange
        env_missing_org = {"CPLN_TOKEN": "test-token"}

        # Act & Assert
        with patch.dict(os.environ, env_missing_org, clear=True):
            with self.assertRaises(ValueError) as context:
                kwargs_from_env()

            self.assertIn("CPLN_ORG", str(context.exception))

    def test_kwargs_from_env_with_both_required_missing_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when both required vars are missing"""
        # Act & Assert
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            kwargs_from_env()

    def test_kwargs_from_env_with_empty_string_token_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_TOKEN is empty string"""
        # Arrange
        env_empty_token = {"CPLN_TOKEN": "", "CPLN_ORG": "test-org"}

        # Act & Assert
        with patch.dict(os.environ, env_empty_token, clear=True):
            with self.assertRaises(ValueError) as context:
                kwargs_from_env()

            self.assertIn("CPLN_TOKEN", str(context.exception))

    def test_kwargs_from_env_with_empty_string_org_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_ORG is empty string"""
        # Arrange
        env_empty_org = {"CPLN_TOKEN": "test-token", "CPLN_ORG": ""}

        # Act & Assert
        with patch.dict(os.environ, env_empty_org, clear=True):
            with self.assertRaises(ValueError) as context:
                kwargs_from_env()

            self.assertIn("CPLN_ORG", str(context.exception))

    def test_kwargs_from_env_with_whitespace_only_values_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError for whitespace-only values"""
        # Arrange
        test_cases = [
            {"CPLN_TOKEN": "   ", "CPLN_ORG": "test-org"},  # Whitespace token
            {"CPLN_TOKEN": "test-token", "CPLN_ORG": "   "},  # Whitespace org
            {"CPLN_TOKEN": "\t\n", "CPLN_ORG": "\t\n"},  # Tab/newline whitespace
        ]

        for env_vars in test_cases:
            # Act & Assert
            with self.subTest(env_vars=env_vars), patch.dict(
                os.environ, env_vars, clear=True
            ), self.assertRaises(ValueError):
                kwargs_from_env()


class TestKwargsFromEnvSpecialValues(unittest.TestCase):
    """Test kwargs_from_env with special and edge case values"""

    def test_kwargs_from_env_with_special_characters_in_values_preserves_values(self):
        """Test that kwargs_from_env preserves special characters in environment values"""
        # Arrange
        special_values = {
            "CPLN_TOKEN": "token-with-dashes_and_underscores.periods:colons",
            "CPLN_ORG": "org.with.periods-and-dashes_underscores",
            "CPLN_BASE_URL": "https://api-staging.cpln.io:8080/v2",
            "CPLN_VERSION": "v2.1.0-beta+build.123",
            "CPLN_TIMEOUT": "30.5",
        }

        # Act
        with patch.dict(os.environ, special_values, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], special_values["CPLN_TOKEN"])
        self.assertEqual(result["org"], special_values["CPLN_ORG"])
        self.assertEqual(result["base_url"], special_values["CPLN_BASE_URL"])
        self.assertEqual(result["version"], special_values["CPLN_VERSION"])
        self.assertEqual(result["timeout"], special_values["CPLN_TIMEOUT"])

    def test_kwargs_from_env_with_unicode_characters_preserves_unicode(self):
        """Test that kwargs_from_env handles unicode characters correctly"""
        # Arrange
        unicode_values = {
            "CPLN_TOKEN": "tökén-with-ünicödé-123",
            "CPLN_ORG": "örg-with-spéciàl-chars",
            "CPLN_BASE_URL": "https://api-测试.cpln.io",
        }

        # Act
        with patch.dict(os.environ, unicode_values, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], unicode_values["CPLN_TOKEN"])
        self.assertEqual(result["org"], unicode_values["CPLN_ORG"])
        self.assertEqual(result["base_url"], unicode_values["CPLN_BASE_URL"])

    def test_kwargs_from_env_with_very_long_values_handles_correctly(self):
        """Test that kwargs_from_env handles very long environment variable values"""
        # Arrange
        long_token = "x" * 1000  # Very long token
        long_org = "o" * 500  # Very long org name
        long_url = "https://very-long-subdomain-" + "x" * 100 + ".cpln.io"

        long_values = {
            "CPLN_TOKEN": long_token,
            "CPLN_ORG": long_org,
            "CPLN_BASE_URL": long_url,
        }

        # Act
        with patch.dict(os.environ, long_values, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], long_token)
        self.assertEqual(result["org"], long_org)
        self.assertEqual(result["base_url"], long_url)
        self.assertEqual(len(result["token"]), 1000)
        self.assertEqual(len(result["org"]), 500)


class TestKwargsFromEnvIntegrationScenarios(unittest.TestCase):
    """Test kwargs_from_env integration scenarios and real-world usage patterns"""

    def test_kwargs_from_env_development_environment_simulation(self):
        """Test kwargs_from_env with typical development environment values"""
        # Arrange
        dev_env = {
            "CPLN_TOKEN": "dev-local-token-12345",
            "CPLN_ORG": "development-org",
            "CPLN_BASE_URL": "https://dev-api.cpln.io",
            "CPLN_TIMEOUT": "10",  # Shorter timeout for development
        }

        # Act
        with patch.dict(os.environ, dev_env, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], "dev-local-token-12345")
        self.assertEqual(result["org"], "development-org")
        self.assertEqual(result["base_url"], "https://dev-api.cpln.io")
        self.assertEqual(result["timeout"], "10")
        # Version not specified in dev, should be excluded
        self.assertNotIn("version", result)

    def test_kwargs_from_env_production_environment_simulation(self):
        """Test kwargs_from_env with typical production environment values"""
        # Arrange
        prod_env = {
            "CPLN_TOKEN": "prod-secure-token-abcdef123456789",
            "CPLN_ORG": "production-company-org",
            "CPLN_BASE_URL": DEFAULT_CPLN_API_URL,
            "CPLN_VERSION": "1.0.0",
            "CPLN_TIMEOUT": "60",  # Longer timeout for production
        }

        # Act
        with patch.dict(os.environ, prod_env, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], "prod-secure-token-abcdef123456789")
        self.assertEqual(result["org"], "production-company-org")
        self.assertEqual(result["base_url"], DEFAULT_CPLN_API_URL)
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["timeout"], "60")

    def test_kwargs_from_env_ci_environment_simulation(self):
        """Test kwargs_from_env with typical CI/CD environment values"""
        # Arrange
        ci_env = {
            "CPLN_TOKEN": "${CI_CPLN_TOKEN}",  # Placeholder that might be in CI
            "CPLN_ORG": "ci-testing-org",
            "CPLN_BASE_URL": "https://staging-api.cpln.io",
            "CPLN_VERSION": "latest",
        }

        # Act
        with patch.dict(os.environ, ci_env, clear=True):
            result = kwargs_from_env()

        # Assert
        self.assertEqual(result["token"], "${CI_CPLN_TOKEN}")
        self.assertEqual(result["org"], "ci-testing-org")
        self.assertEqual(result["base_url"], "https://staging-api.cpln.io")
        self.assertEqual(result["version"], "latest")
        self.assertNotIn("timeout", result)  # Not specified in CI

    def test_kwargs_from_env_with_mixed_case_environment_variables_case_sensitive(self):
        """Test that kwargs_from_env is case-sensitive for environment variable names"""
        # Arrange - Using wrong case for environment variables
        wrong_case_env = {
            "cpln_token": "lowercase-token",  # Wrong case
            "CPLN_ORG": "correct-org",
            "Cpln_Base_Url": "mixed-case-url",  # Wrong case
        }

        # Act & Assert
        with patch.dict(os.environ, wrong_case_env, clear=True), self.assertRaises(
            ValueError
        ):
            # Should fail because lowercase cpln_token is not recognized
            kwargs_from_env()

    def test_kwargs_from_env_environment_isolation_between_calls(self):
        """Test that kwargs_from_env properly isolates different environment contexts"""
        # Arrange
        env1 = {"CPLN_TOKEN": "token1", "CPLN_ORG": "org1"}
        env2 = {"CPLN_TOKEN": "token2", "CPLN_ORG": "org2", "CPLN_VERSION": "v2"}

        # Act
        with patch.dict(os.environ, env1, clear=True):
            result1 = kwargs_from_env()

        with patch.dict(os.environ, env2, clear=True):
            result2 = kwargs_from_env()

        # Assert
        # Results should be different and not interfere with each other
        self.assertEqual(result1["token"], "token1")
        self.assertEqual(result1["org"], "org1")
        self.assertNotIn("version", result1)

        self.assertEqual(result2["token"], "token2")
        self.assertEqual(result2["org"], "org2")
        self.assertEqual(result2["version"], "v2")

        # Results should be completely independent
        self.assertNotEqual(result1, result2)


if __name__ == "__main__":
    unittest.main()  # type: ignore
