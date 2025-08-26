"""Tests for utils module following unit testing best practices."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from cpln.utils.utils import (
    convert_dictionary_keys,
    get_default_workload_template,
    kwargs_from_env,
    load_template,
)


class TestEnvironmentConfiguration(unittest.TestCase):
    """Test environment variable configuration extraction"""

    def test_kwargs_from_env_with_valid_environment_returns_complete_config(self):
        """Test that kwargs_from_env returns complete config with valid environment variables"""
        # Arrange
        test_environment = {
            "CPLN_TOKEN": "test-token-123",
            "CPLN_ORG": "test-organization",
        }
        expected_config = {
            "base_url": "https://api.cpln.io",
            "token": "test-token-123",
            "org": "test-organization",
        }

        # Act
        result = kwargs_from_env(environment=test_environment)

        # Assert
        self.assertEqual(result, expected_config)

    def test_kwargs_from_env_with_none_environment_uses_os_environ(self):
        """Test that kwargs_from_env uses os.environ when environment is None"""
        # Arrange
        with patch.dict(
            os.environ, {"CPLN_TOKEN": "env-token-456", "CPLN_ORG": "env-organization"}
        ):
            expected_config = {
                "base_url": "https://api.cpln.io",
                "token": "env-token-456",
                "org": "env-organization",
            }

            # Act
            result = kwargs_from_env(environment=None)

            # Assert
            self.assertEqual(result, expected_config)

    def test_kwargs_from_env_with_missing_token_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_TOKEN is missing"""
        # Arrange
        test_environment = {
            "CPLN_ORG": "test-organization",
            # CPLN_TOKEN is intentionally missing
        }

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            kwargs_from_env(environment=test_environment)

        self.assertIn("CPLN_TOKEN is not set", str(context.exception))

    def test_kwargs_from_env_with_missing_org_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_ORG is missing"""
        # Arrange
        test_environment = {
            "CPLN_TOKEN": "test-token-123",
            # CPLN_ORG is intentionally missing
        }

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            kwargs_from_env(environment=test_environment)

        self.assertIn("CPLN_ORG is not set", str(context.exception))

    def test_kwargs_from_env_with_empty_token_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_TOKEN is empty"""
        # Arrange
        test_environment = {
            "CPLN_TOKEN": "",  # Empty token
            "CPLN_ORG": "test-organization",
        }

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            kwargs_from_env(environment=test_environment)

        self.assertIn("CPLN_TOKEN is not set", str(context.exception))

    def test_kwargs_from_env_with_empty_org_raises_value_error(self):
        """Test that kwargs_from_env raises ValueError when CPLN_ORG is empty"""
        # Arrange
        test_environment = {
            "CPLN_TOKEN": "test-token-123",
            "CPLN_ORG": "",  # Empty org
        }

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            kwargs_from_env(environment=test_environment)

        self.assertIn("CPLN_ORG is not set", str(context.exception))

    def test_kwargs_from_env_with_empty_environment_uses_defaults(self):
        """Test that kwargs_from_env handles empty environment dictionary"""
        # Arrange
        test_environment = {}

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            kwargs_from_env(environment=test_environment)

        self.assertIn("CPLN_TOKEN is not set", str(context.exception))


class TestTemplateLoading(unittest.TestCase):
    """Test JSON template file loading functionality"""

    def test_load_template_with_valid_json_file_returns_parsed_data(self):
        """Test that load_template successfully loads and parses valid JSON file"""
        # Arrange
        test_data = {
            "kind": "workload",
            "metadata": {"name": "test-workload"},
            "spec": {"containers": [{"name": "app", "image": "nginx"}]},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(test_data, temp_file)
            temp_file_path = temp_file.name

        try:
            # Act
            result = load_template(temp_file_path)

            # Assert
            self.assertEqual(result, test_data)
        finally:
            os.unlink(temp_file_path)

    def test_load_template_with_empty_json_file_returns_empty_dict(self):
        """Test that load_template handles empty JSON files correctly"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_file.write("{}")
            temp_file_path = temp_file.name

        try:
            # Act
            result = load_template(temp_file_path)

            # Assert
            self.assertEqual(result, {})
        finally:
            os.unlink(temp_file_path)

    def test_load_template_with_complex_nested_data_preserves_structure(self):
        """Test that load_template preserves complex nested JSON structures"""
        # Arrange
        complex_data = {
            "metadata": {
                "labels": {"app": "test", "version": "1.0"},
                "annotations": {"description": "Test workload"},
            },
            "spec": {
                "containers": [
                    {"name": "web", "ports": [8080, 8443]},
                    {"name": "db", "env": {"DB_NAME": "test"}},
                ]
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(complex_data, temp_file)
            temp_file_path = temp_file.name

        try:
            # Act
            result = load_template(temp_file_path)

            # Assert
            self.assertEqual(result, complex_data)
            # Verify nested structure integrity
            self.assertEqual(result["metadata"]["labels"]["app"], "test")
            self.assertEqual(result["spec"]["containers"][0]["ports"], [8080, 8443])
        finally:
            os.unlink(temp_file_path)

    def test_load_template_with_nonexistent_file_raises_file_not_found_error(self):
        """Test that load_template raises FileNotFoundError for nonexistent files"""
        # Arrange
        nonexistent_path = "/path/to/nonexistent/file.json"

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            load_template(nonexistent_path)

    def test_load_template_with_invalid_json_raises_json_decode_error(self):
        """Test that load_template raises JSONDecodeError for invalid JSON"""
        # Arrange
        invalid_json = "{ invalid json content }"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_file.write(invalid_json)
            temp_file_path = temp_file.name

        try:
            # Act & Assert
            with self.assertRaises(json.JSONDecodeError):
                load_template(temp_file_path)
        finally:
            os.unlink(temp_file_path)

    def test_load_template_with_empty_file_raises_json_decode_error(self):
        """Test that load_template raises JSONDecodeError for completely empty files"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            # Write nothing to create empty file
            temp_file_path = temp_file.name

        try:
            # Act & Assert
            with self.assertRaises(json.JSONDecodeError):
                load_template(temp_file_path)
        finally:
            os.unlink(temp_file_path)


class TestDefaultWorkloadTemplates(unittest.TestCase):
    """Test default workload template retrieval functionality"""

    @patch("cpln.utils.utils.load_template")
    def test_get_default_workload_template_serverless_loads_correct_template(
        self, mock_load_template
    ):
        """Test that get_default_workload_template loads serverless template correctly"""
        # Arrange
        expected_template = {
            "kind": "workload",
            "spec": {"type": "serverless", "containers": []},
        }
        mock_load_template.return_value = expected_template

        # Act
        result = get_default_workload_template("serverless")

        # Assert
        self.assertEqual(result, expected_template)
        mock_load_template.assert_called_once()
        # Verify correct template path is used
        call_args = mock_load_template.call_args[0][0]
        self.assertIn("default-serverless-workload.json", call_args)

    @patch("cpln.utils.utils.load_template")
    def test_get_default_workload_template_standard_loads_correct_template(
        self, mock_load_template
    ):
        """Test that get_default_workload_template loads standard template correctly"""
        # Arrange
        expected_template = {
            "kind": "workload",
            "spec": {"type": "standard", "containers": []},
        }
        mock_load_template.return_value = expected_template

        # Act
        result = get_default_workload_template("standard")

        # Assert
        self.assertEqual(result, expected_template)
        mock_load_template.assert_called_once()
        # Verify correct template path is used
        call_args = mock_load_template.call_args[0][0]
        self.assertIn("default-standard-workload.json", call_args)

    def test_get_default_workload_template_with_invalid_type_raises_value_error(self):
        """Test that get_default_workload_template raises ValueError for invalid workload types"""
        # Arrange
        invalid_types = ["invalid", "custom", "unknown", "", None]

        for invalid_type in invalid_types:
            with self.subTest(workload_type=invalid_type):
                # Act & Assert
                with self.assertRaises(ValueError) as context:
                    get_default_workload_template(invalid_type)  # type: ignore

                self.assertIn(
                    f"Invalid workload type: {invalid_type}", str(context.exception)
                )

    @patch("cpln.utils.utils.load_template")
    def test_get_default_workload_template_propagates_load_template_errors(
        self, mock_load_template
    ):
        """Test that get_default_workload_template propagates errors from load_template"""
        # Arrange
        mock_load_template.side_effect = FileNotFoundError("Template file not found")

        # Act & Assert
        with self.assertRaises(FileNotFoundError) as context:
            get_default_workload_template("serverless")

        self.assertIn("Template file not found", str(context.exception))

    @patch("cpln.utils.utils.load_template")
    def test_get_default_workload_template_handles_json_decode_errors(
        self, mock_load_template
    ):
        """Test that get_default_workload_template propagates JSON decode errors"""
        # Arrange
        mock_load_template.side_effect = json.JSONDecodeError(
            "Invalid JSON", "template.json", 0
        )

        # Act & Assert
        with self.assertRaises(json.JSONDecodeError):
            get_default_workload_template("standard")


class TestDictionaryKeyConversion(unittest.TestCase):
    """Test dictionary key transformation functionality"""

    def test_convert_dictionary_keys_with_default_underscore_transforms_camel_case(
        self,
    ):
        """Test that convert_dictionary_keys transforms camelCase keys to snake_case by default"""
        # Arrange
        input_data = {
            "firstName": "John",
            "lastName": "Doe",
            "dateOfBirth": "1990-01-01",
            "contactInfo": {"emailAddress": "john@example.com"},
        }
        expected_output = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "contact_info": {"email_address": "john@example.com"},
        }

        # Act
        result = convert_dictionary_keys(input_data)

        # Assert
        self.assertEqual(result, expected_output)

    def test_convert_dictionary_keys_with_custom_format_function_applies_transformation(
        self,
    ):
        """Test that convert_dictionary_keys uses custom format function correctly"""
        # Arrange
        input_data = {"firstName": "John", "lastName": "Doe"}

        def uppercase_func(key):
            return key.upper()

        expected_output = {"FIRSTNAME": "John", "LASTNAME": "Doe"}

        # Act
        result = convert_dictionary_keys(input_data, format_func=uppercase_func)

        # Assert
        self.assertEqual(result, expected_output)

    def test_convert_dictionary_keys_with_key_map_overrides_format_function(self):
        """Test that convert_dictionary_keys key_map takes precedence over format function"""
        # Arrange
        input_data = {"firstName": "John", "lastName": "Doe", "age": 30}
        custom_key_map = {"firstName": "given_name", "lastName": "family_name"}
        # age should still be processed by format function (underscore)
        expected_output = {"given_name": "John", "family_name": "Doe", "age": 30}

        # Act
        result = convert_dictionary_keys(input_data, key_map=custom_key_map)

        # Assert
        self.assertEqual(result, expected_output)

    def test_convert_dictionary_keys_with_nested_dictionaries_processes_recursively(
        self,
    ):
        """Test that convert_dictionary_keys processes nested dictionaries recursively"""
        # Arrange
        nested_data = {
            "userInfo": {
                "personalData": {
                    "firstName": "John",
                    "contactDetails": {"emailAddress": "john@example.com"},
                },
                "accountData": {"accountType": "premium"},
            }
        }
        expected_output = {
            "user_info": {
                "personal_data": {
                    "first_name": "John",
                    "contact_details": {"email_address": "john@example.com"},
                },
                "account_data": {"account_type": "premium"},
            }
        }

        # Act
        result = convert_dictionary_keys(nested_data)

        # Assert
        self.assertEqual(result, expected_output)

    def test_convert_dictionary_keys_with_list_of_dictionaries_processes_each_item(
        self,
    ):
        """Test that convert_dictionary_keys processes dictionaries within lists"""
        # Arrange
        data_with_lists = {
            "userList": [
                {"firstName": "John", "lastName": "Doe"},
                {"firstName": "Jane", "lastName": "Smith"},
            ],
            "metaData": {"totalCount": 2},
        }
        expected_output = {
            "user_list": [
                {"first_name": "John", "last_name": "Doe"},
                {"first_name": "Jane", "last_name": "Smith"},
            ],
            "meta_data": {"total_count": 2},
        }

        # Act
        result = convert_dictionary_keys(data_with_lists)

        # Assert
        self.assertEqual(result, expected_output)

    def test_convert_dictionary_keys_with_mixed_list_types_preserves_non_dict_items(
        self,
    ):
        """Test that convert_dictionary_keys preserves non-dictionary items in lists"""
        # Arrange
        mixed_data = {
            "mixedList": ["string_item", 123, {"keyName": "value"}, None, True]
        }
        expected_output = {
            "mixed_list": ["string_item", 123, {"key_name": "value"}, None, True]
        }

        # Act
        result = convert_dictionary_keys(mixed_data)

        # Assert
        self.assertEqual(result, expected_output)

    def test_convert_dictionary_keys_with_empty_dictionary_returns_empty_dictionary(
        self,
    ):
        """Test that convert_dictionary_keys handles empty dictionaries correctly"""
        # Arrange
        empty_data = {}

        # Act
        result = convert_dictionary_keys(empty_data)

        # Assert
        self.assertEqual(result, {})
        self.assertIsNot(
            result, empty_data
        )  # Should return new dict, not same instance

    def test_convert_dictionary_keys_with_none_key_map_uses_default_behavior(self):
        """Test that convert_dictionary_keys handles None key_map correctly"""
        # Arrange
        input_data = {"firstName": "John", "lastName": "Doe"}
        expected_output = {"first_name": "John", "last_name": "Doe"}

        # Act
        result = convert_dictionary_keys(input_data, key_map=None)

        # Assert
        self.assertEqual(result, expected_output)

    def test_convert_dictionary_keys_preserves_original_data_immutability(self):
        """Test that convert_dictionary_keys doesn't modify the original dictionary"""
        # Arrange
        original_data = {"firstName": "John", "nested": {"lastName": "Doe"}}
        original_copy = {"firstName": "John", "nested": {"lastName": "Doe"}}

        # Act
        result = convert_dictionary_keys(original_data)

        # Assert
        self.assertEqual(original_data, original_copy)  # Original unchanged
        self.assertIsNot(result, original_data)  # Different objects
        self.assertIsNot(result["nested"], original_data["nested"])  # Deep copy


class TestUtilsEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions across utils functions"""

    def test_load_template_with_permission_denied_raises_permission_error(self):
        """Test that load_template handles permission errors appropriately"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump({"test": "data"}, temp_file)
            temp_file_path = temp_file.name

        try:
            # Remove read permissions
            os.chmod(temp_file_path, 0o000)

            # Act & Assert
            with self.assertRaises(PermissionError):
                load_template(temp_file_path)
        finally:
            # Restore permissions and cleanup
            os.chmod(temp_file_path, 0o644)
            os.unlink(temp_file_path)

    def test_convert_dictionary_keys_with_very_deep_nesting_handles_correctly(self):
        """Test that convert_dictionary_keys handles very deeply nested structures"""
        # Arrange
        deep_data = {"level1": {"level2": {"level3": {"level4": {"deepKey": "value"}}}}}
        expected_output = {
            "level1": {"level2": {"level3": {"level4": {"deep_key": "value"}}}}
        }

        # Act
        result = convert_dictionary_keys(deep_data)

        # Assert
        self.assertEqual(result, expected_output)

    @patch.dict(os.environ, {}, clear=True)
    def test_kwargs_from_env_with_cleared_environment_raises_appropriate_errors(self):
        """Test that kwargs_from_env handles completely cleared environment"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            kwargs_from_env()

        self.assertIn("CPLN_TOKEN is not set", str(context.exception))


if __name__ == "__main__":
    unittest.main()  # type: ignore
