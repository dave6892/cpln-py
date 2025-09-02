"""Tests for API config following unit testing best practices."""

import os
import unittest
from unittest.mock import patch

from cpln.api.config import APIConfig
from cpln.constants import (
    DEFAULT_CPLN_API_URL,
    DEFAULT_CPLN_API_VERSION,
    DEFAULT_TIMEOUT_SECONDS,
)


class TestAPIConfigInitialization(unittest.TestCase):
    """Test APIConfig initialization and default values"""

    def test_api_config_initialization_with_environment_values_uses_defaults(self):
        """Test that APIConfig uses default constants when environment values are None"""
        # Arrange & Act
        with patch.dict(
            os.environ,
            {"CPLN_BASE_URL": "", "CPLN_ORG": "test-org", "CPLN_TOKEN": "test-token"},
            clear=True,
        ):
            config = APIConfig(
                base_url=os.getenv("CPLN_BASE_URL") or DEFAULT_CPLN_API_URL,
                org=os.getenv("CPLN_ORG") or "test-org",  # type: ignore
                token=os.getenv("CPLN_TOKEN") or "test-token",  # type: ignore
            )

        # Assert
        self.assertEqual(config.base_url, DEFAULT_CPLN_API_URL)
        self.assertEqual(config.org, "test-org")
        self.assertEqual(config.token, "test-token")
        self.assertEqual(config.version, DEFAULT_CPLN_API_VERSION)
        self.assertEqual(config.timeout, DEFAULT_TIMEOUT_SECONDS)

    def test_api_config_initialization_with_explicit_values_overrides_defaults(self):
        """Test that APIConfig accepts explicit values and overrides defaults"""
        # Arrange
        custom_base_url = "https://custom-api.cpln.io"
        custom_org = "custom-org"
        custom_token = "custom-token"
        custom_version = "2.0.0"
        custom_timeout = 30

        # Act
        config = APIConfig(
            base_url=custom_base_url,
            org=custom_org,
            token=custom_token,
            version=custom_version,
            timeout=custom_timeout,
        )

        # Assert
        self.assertEqual(config.base_url, custom_base_url)
        self.assertEqual(config.org, custom_org)
        self.assertEqual(config.token, custom_token)
        self.assertEqual(config.version, custom_version)
        self.assertEqual(config.timeout, custom_timeout)

    def test_api_config_initialization_with_minimal_required_fields_uses_defaults(self):
        """Test that APIConfig works with only required fields and uses defaults for optional ones"""
        # Arrange
        required_base_url = "https://required-api.cpln.io"
        required_org = "required-org"
        required_token = "required-token"

        # Act
        config = APIConfig(
            base_url=required_base_url,
            org=required_org,
            token=required_token,
        )

        # Assert
        self.assertEqual(config.base_url, required_base_url)
        self.assertEqual(config.org, required_org)
        self.assertEqual(config.token, required_token)
        self.assertEqual(config.version, DEFAULT_CPLN_API_VERSION)
        self.assertEqual(config.timeout, DEFAULT_TIMEOUT_SECONDS)


class TestAPIConfigProperties(unittest.TestCase):
    """Test APIConfig computed properties and methods"""

    def setUp(self):
        """Set up common test fixtures"""
        self.base_url = "https://test-api.cpln.io"
        self.org = "test-organization"
        self.token = "test-bearer-token"
        self.config = APIConfig(
            base_url=self.base_url,
            org=self.org,
            token=self.token,
        )

    def test_org_url_property_combines_base_url_and_org_correctly(self):
        """Test that org_url property constructs correct URL"""
        # Act
        result = self.config.org_url

        # Assert
        expected_url = f"{self.base_url}/org/{self.org}"
        self.assertEqual(result, expected_url)

    def test_org_url_property_handles_trailing_slashes_correctly(self):
        """Test that org_url handles base URLs with trailing slashes"""
        # Arrange
        config_with_trailing_slash = APIConfig(
            base_url="https://api-with-slash.cpln.io/",
            org="slash-org",
            token="slash-token",
        )

        # Act
        result = config_with_trailing_slash.org_url

        # Assert
        # Should handle trailing slash appropriately
        expected_url = "https://api-with-slash.cpln.io/org/slash-org"
        self.assertEqual(result, expected_url)

    def test_asdict_method_returns_complete_configuration_dictionary(self):
        """Test that asdict() returns all configuration values as dictionary"""
        # Arrange
        custom_config = APIConfig(
            base_url="https://dict-api.cpln.io",
            org="dict-org",
            token="dict-token",
            version="1.5.0",
            timeout=45,
        )

        # Act
        result = custom_config.asdict()

        # Assert
        expected_dict = {
            "base_url": "https://dict-api.cpln.io",
            "org": "dict-org",
            "token": "dict-token",
            "version": "1.5.0",
            "timeout": 45,
            "org_url": "https://dict-api.cpln.io/org/dict-org",
        }
        self.assertEqual(result, expected_dict)

    def test_asdict_method_with_default_values_includes_defaults(self):
        """Test that asdict() includes default values for optional fields"""
        # Arrange
        minimal_config = APIConfig(
            base_url="https://minimal-dict.cpln.io",
            org="minimal-org",
            token="minimal-token",
        )

        # Act
        result = minimal_config.asdict()

        # Assert
        expected_dict = {
            "base_url": "https://minimal-dict.cpln.io",
            "org": "minimal-org",
            "token": "minimal-token",
            "version": DEFAULT_CPLN_API_VERSION,
            "timeout": DEFAULT_TIMEOUT_SECONDS,
            "org_url": "https://minimal-dict.cpln.io/org/minimal-org",
        }
        self.assertEqual(result, expected_dict)


class TestAPIConfigValidation(unittest.TestCase):
    """Test APIConfig input validation and error handling"""

    def test_api_config_creation_without_required_fields_raises_type_error(self):
        """Test that APIConfig raises TypeError when required fields are missing"""
        # Test cases for missing required fields
        test_cases = [
            # Missing all required fields
            {},
            # Missing org and token
            {"base_url": "https://test-api.cpln.io"},
            # Missing token
            {"base_url": "https://test-api.cpln.io", "org": "test-org"},
            # Missing org
            {"base_url": "https://test-api.cpln.io", "token": "test-token"},
            # Missing base_url
            {"org": "test-org", "token": "test-token"},
        ]

        for test_case in test_cases:
            # Act & Assert
            with self.subTest(missing_fields=test_case), self.assertRaises(TypeError):
                APIConfig(**test_case)

    def test_api_config_with_none_values_for_required_fields_creates_config(self):
        """Test that APIConfig accepts None values for required fields (dataclass behavior)"""
        # Arrange & Act
        # Note: dataclasses allow None values even for non-Optional fields
        config = APIConfig(base_url=None, org=None, token=None)  # type: ignore

        # Assert
        self.assertIsNone(config.base_url)
        self.assertIsNone(config.org)
        self.assertIsNone(config.token)
        self.assertEqual(config.version, DEFAULT_CPLN_API_VERSION)
        self.assertEqual(config.timeout, DEFAULT_TIMEOUT_SECONDS)

    def test_api_config_with_empty_string_values_preserves_empty_strings(self):
        """Test that APIConfig preserves empty string values"""
        # Arrange & Act
        config = APIConfig(base_url="", org="", token="")

        # Assert
        self.assertEqual(config.base_url, "")
        self.assertEqual(config.org, "")
        self.assertEqual(config.token, "")

    def test_api_config_with_custom_types_accepts_various_timeout_types(self):
        """Test that APIConfig accepts different timeout value types"""
        # Arrange
        test_cases = [
            (15, int),
            (15.5, float),
            ("30", str),  # Should accept string (though not ideal)
        ]

        for timeout_value, expected_type in test_cases:
            with self.subTest(timeout_value=timeout_value, expected_type=expected_type):
                # Act
                config = APIConfig(
                    base_url="https://test.cpln.io",
                    org="test-org",
                    token="test-token",
                    timeout=timeout_value,  # type: ignore
                )

                # Assert
                self.assertEqual(config.timeout, timeout_value)
                self.assertIsInstance(config.timeout, expected_type)


class TestAPIConfigIntegrationWithEnvironment(unittest.TestCase):
    """Test APIConfig integration with environment variables"""

    def test_api_config_with_environment_variables_integration(self):
        """Test complete integration with environment variables"""
        # Arrange
        test_env = {
            "CPLN_BASE_URL": "https://env-integration.cpln.io",
            "CPLN_ORG": "env-integration-org",
            "CPLN_TOKEN": "env-integration-token",
            "CPLN_VERSION": "3.0.0",
            "CPLN_TIMEOUT": "60",
        }

        # Act
        with patch.dict(os.environ, test_env, clear=True):
            config = APIConfig(
                base_url=os.getenv("CPLN_BASE_URL") or "https://env.cpln.io",  # type: ignore
                org=os.getenv("CPLN_ORG") or "env-org",  # type: ignore
                token=os.getenv("CPLN_TOKEN") or "env-token",  # type: ignore
                version=os.getenv("CPLN_VERSION") or "3.0.0",  # type: ignore
                timeout=int(os.getenv("CPLN_TIMEOUT") or "60"),  # type: ignore
            )

        # Assert
        self.assertEqual(config.base_url, "https://env-integration.cpln.io")
        self.assertEqual(config.org, "env-integration-org")
        self.assertEqual(config.token, "env-integration-token")
        self.assertEqual(config.version, "3.0.0")
        self.assertEqual(config.timeout, 60)

    def test_api_config_fallback_to_defaults_when_env_vars_missing(self):
        """Test that APIConfig falls back to defaults when environment variables are missing"""
        # Arrange & Act
        with patch.dict(os.environ, {}, clear=True):
            config = APIConfig(
                base_url=os.getenv("CPLN_BASE_URL") or DEFAULT_CPLN_API_URL,
                org=os.getenv("CPLN_ORG") or "default-org",
                token=os.getenv("CPLN_TOKEN") or "default-token",
                version=os.getenv("CPLN_VERSION") or DEFAULT_CPLN_API_VERSION,  # type: ignore
                timeout=int(os.getenv("CPLN_TIMEOUT") or str(DEFAULT_TIMEOUT_SECONDS)),
            )

        # Assert
        self.assertEqual(config.base_url, DEFAULT_CPLN_API_URL)
        self.assertEqual(config.org, "default-org")
        self.assertEqual(config.token, "default-token")
        self.assertEqual(config.version, DEFAULT_CPLN_API_VERSION)
        self.assertEqual(config.timeout, DEFAULT_TIMEOUT_SECONDS)

    def test_api_config_mixed_env_and_explicit_values_prioritizes_explicit(self):
        """Test that explicit values take priority over environment variables"""
        # Arrange
        env_values = {
            "CPLN_BASE_URL": "https://env-url.cpln.io",
            "CPLN_ORG": "env-org",
            "CPLN_TOKEN": "env-token",
        }

        explicit_base_url = "https://explicit-url.cpln.io"
        explicit_org = "explicit-org"

        # Act
        with patch.dict(os.environ, env_values, clear=True):
            config = APIConfig(
                base_url=explicit_base_url,  # Explicit value
                org=explicit_org,  # Explicit value
                token=os.getenv("CPLN_TOKEN") or "fallback-token",  # type: ignore
            )

        # Assert
        self.assertEqual(config.base_url, explicit_base_url)  # Explicit wins
        self.assertEqual(config.org, explicit_org)  # Explicit wins
        self.assertEqual(config.token, "env-token")  # From environment


if __name__ == "__main__":
    unittest.main()  # type: ignore
