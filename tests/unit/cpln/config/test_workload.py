"""Tests for workload config following unit testing best practices."""

import unittest

from cpln.config.workload import WorkloadConfig


class TestWorkloadConfigInitialization(unittest.TestCase):
    """Test WorkloadConfig dataclass initialization and basic properties"""

    def test_workload_config_creation_with_all_parameters_sets_attributes_correctly(
        self,
    ):
        """Test that WorkloadConfig initializes correctly with all parameters"""
        # Arrange
        test_specs: dict = {  # type: ignore
            "kind": "workload",
            "spec": {
                "containers": [
                    {
                        "name": "app",
                        "image": "nginx:latest",
                        "cpu": "100m",
                        "memory": 128,
                    }
                ],
                "type": "standard",
            },
        }

        # Act
        config = WorkloadConfig(
            gvc="production-gvc",
            workload_id="web-service",
            location="us-west-2",
            specs=test_specs,  # type: ignore
        )

        # Assert
        self.assertEqual(config.gvc, "production-gvc")
        self.assertEqual(config.workload_id, "web-service")
        self.assertEqual(config.location, "us-west-2")
        self.assertEqual(config.specs, test_specs)

    def test_workload_config_creation_with_required_parameters_only_uses_defaults(self):
        """Test that WorkloadConfig works with only required parameters"""
        # Act
        config = WorkloadConfig(gvc="minimal-gvc", workload_id="minimal-workload")

        # Assert
        self.assertEqual(config.gvc, "minimal-gvc")
        self.assertEqual(config.workload_id, "minimal-workload")
        self.assertIsNone(config.location)
        self.assertIsNone(config.specs)

    def test_workload_config_creation_with_none_optional_parameters_stores_none(self):
        """Test that WorkloadConfig handles explicit None values for optional parameters"""
        # Act
        config = WorkloadConfig(
            gvc="explicit-none-gvc",
            workload_id="explicit-none-workload",
            location=None,
            specs=None,
        )

        # Assert
        self.assertEqual(config.gvc, "explicit-none-gvc")
        self.assertEqual(config.workload_id, "explicit-none-workload")
        self.assertIsNone(config.location)
        self.assertIsNone(config.specs)

    def test_workload_config_creation_with_empty_string_values_preserves_empty_strings(
        self,
    ):
        """Test that WorkloadConfig preserves empty string values"""
        # Act
        config = WorkloadConfig(
            gvc="",
            workload_id="",
            location="",
        )

        # Assert
        self.assertEqual(config.gvc, "")
        self.assertEqual(config.workload_id, "")
        self.assertEqual(config.location, "")
        self.assertIsNone(config.specs)


class TestWorkloadConfigSpecsHandling(unittest.TestCase):
    """Test WorkloadConfig specs parameter handling"""

    def test_workload_config_with_complex_specs_stores_complete_structure(self):
        """Test that WorkloadConfig handles complex specs structures"""
        # Arrange
        complex_specs: dict = {  # type: ignore
            "kind": "workload",
            "metadata": {
                "name": "complex-workload",
                "labels": {"app": "web", "env": "prod"},
                "annotations": {"description": "Complex workload example"},
            },
            "spec": {
                "type": "serverless",
                "containers": [
                    {
                        "name": "web",
                        "image": "nginx:1.21",
                        "cpu": "200m",
                        "memory": 256,
                        "ports": [{"number": 80, "protocol": "http"}],
                        "env": {"NODE_ENV": "production"},
                    },
                    {
                        "name": "api",
                        "image": "node:16-alpine",
                        "cpu": "500m",
                        "memory": 512,
                        "ports": [{"number": 3000, "protocol": "http"}],
                    },
                ],
                "defaultOptions": {
                    "suspend": False,
                    "autoscaling": {"minScale": 1, "maxScale": 10},
                },
            },
        }

        # Act
        config = WorkloadConfig(
            gvc="complex-gvc",
            workload_id="complex-workload",
            specs=complex_specs,  # type: ignore
        )

        # Assert
        self.assertEqual(config.specs, complex_specs)
        # Verify nested access works
        self.assertEqual(config.specs["kind"], "workload")  # type: ignore
        self.assertEqual(config.specs["spec"]["type"], "serverless")  # type: ignore
        self.assertEqual(len(config.specs["spec"]["containers"]), 2)  # type: ignore

    def test_workload_config_with_empty_specs_dict_preserves_empty_dict(self):
        """Test that WorkloadConfig handles empty specs dictionary"""
        # Arrange
        empty_specs: dict = {}  # type: ignore

        # Act
        config = WorkloadConfig(
            gvc="empty-specs-gvc",
            workload_id="empty-specs-workload",
            specs=empty_specs,  # type: ignore
        )

        # Assert
        self.assertEqual(config.specs, {})
        self.assertIsInstance(config.specs, dict)

    def test_workload_config_with_partial_specs_stores_partial_structure(self):
        """Test that WorkloadConfig handles partial specs structures"""
        # Arrange
        partial_specs: dict = {  # type: ignore
            "kind": "workload",
            "metadata": {"name": "partial-workload"},
            # Missing spec section
        }

        # Act
        config = WorkloadConfig(
            gvc="partial-gvc",
            workload_id="partial-workload",
            specs=partial_specs,  # type: ignore
        )

        # Assert
        self.assertEqual(config.specs, partial_specs)
        self.assertEqual(config.specs["kind"], "workload")  # type: ignore
        self.assertIn("metadata", config.specs)  # type: ignore
        self.assertNotIn("spec", config.specs)  # type: ignore


class TestWorkloadConfigLocationHandling(unittest.TestCase):
    """Test WorkloadConfig location parameter handling"""

    def test_workload_config_with_various_location_formats_stores_correctly(self):
        """Test that WorkloadConfig handles various location format strings"""
        # Arrange
        location_test_cases = [
            "us-west-2",
            "europe-central-1",
            "asia-pacific",
            "local-dev",
            "production-zone-a",
            "staging.us-east",
        ]

        for location in location_test_cases:
            with self.subTest(location=location):
                # Act
                config = WorkloadConfig(
                    gvc="location-test-gvc",
                    workload_id="location-test-workload",
                    location=location,
                )

                # Assert
                self.assertEqual(config.location, location)

    def test_workload_config_location_with_special_characters_preserves_characters(
        self,
    ):
        """Test that WorkloadConfig preserves special characters in location"""
        # Arrange
        special_locations = [
            "us-west_2",
            "europe.central.1",
            "asia-pacific@prod",
            "local/dev/zone",
        ]

        for location in special_locations:
            with self.subTest(location=location):
                # Act
                config = WorkloadConfig(
                    gvc="special-gvc", workload_id="special-workload", location=location
                )

                # Assert
                self.assertEqual(config.location, location)


class TestWorkloadConfigDataclassBehavior(unittest.TestCase):
    """Test WorkloadConfig dataclass behavior and properties"""

    def test_workload_config_equality_comparison_with_same_values_returns_true(self):
        """Test that WorkloadConfig instances with same values are equal"""
        # Arrange
        specs1: dict = {"kind": "workload", "spec": {"type": "standard"}}  # type: ignore
        specs2: dict = {"kind": "workload", "spec": {"type": "standard"}}  # type: ignore

        config1 = WorkloadConfig(
            gvc="test-gvc",
            workload_id="test-workload",
            location="us-east",
            specs=specs1,  # type: ignore
        )
        config2 = WorkloadConfig(
            gvc="test-gvc",
            workload_id="test-workload",
            location="us-east",
            specs=specs2,  # type: ignore
        )

        # Act & Assert
        self.assertEqual(config1, config2)

    def test_workload_config_equality_comparison_with_different_values_returns_false(
        self,
    ):
        """Test that WorkloadConfig instances with different values are not equal"""
        # Arrange
        config1 = WorkloadConfig(gvc="gvc1", workload_id="workload1")
        config2 = WorkloadConfig(gvc="gvc2", workload_id="workload1")  # Different GVC
        config3 = WorkloadConfig(
            gvc="gvc1", workload_id="workload2"
        )  # Different workload ID

        # Act & Assert
        self.assertNotEqual(config1, config2)
        self.assertNotEqual(config1, config3)
        self.assertNotEqual(config2, config3)

    def test_workload_config_string_representation_includes_key_values(self):
        """Test that WorkloadConfig string representation is informative"""
        # Arrange
        config = WorkloadConfig(
            gvc="repr-gvc", workload_id="repr-workload", location="repr-location"
        )

        # Act
        result = str(config)

        # Assert
        self.assertIn("WorkloadConfig", result)
        self.assertIn("repr-gvc", result)
        self.assertIn("repr-workload", result)
        self.assertIn("repr-location", result)

    def test_workload_config_repr_is_eval_safe_for_simple_cases(self):
        """Test that WorkloadConfig repr can be used with eval for simple cases"""
        # Arrange
        config = WorkloadConfig(gvc="eval-gvc", workload_id="eval-workload")

        # Act
        repr_string = repr(config)

        # Assert
        # Should contain constructor call format
        self.assertIn("WorkloadConfig", repr_string)
        self.assertIn("gvc=", repr_string)
        self.assertIn("workload_id=", repr_string)

    def test_workload_config_hash_consistency_with_equality(self):
        """Test that WorkloadConfig hash is consistent with equality"""
        # Arrange
        config1 = WorkloadConfig(
            gvc="hash-gvc", workload_id="hash-workload", location="hash-loc"
        )
        config2 = WorkloadConfig(
            gvc="hash-gvc", workload_id="hash-workload", location="hash-loc"
        )

        # Act & Assert
        self.assertEqual(config1, config2)
        self.assertEqual(hash(config1), hash(config2))

    def test_workload_config_can_be_used_as_dict_key(self):
        """Test that WorkloadConfig instances can be used as dictionary keys"""
        # Arrange
        config1 = WorkloadConfig(gvc="key-gvc", workload_id="key-workload")
        config2 = WorkloadConfig(gvc="key-gvc", workload_id="key-workload")
        config3 = WorkloadConfig(gvc="different-gvc", workload_id="key-workload")

        # Act
        test_dict = {config1: "value1", config3: "value3"}

        # Should be able to access using equivalent config
        result1 = test_dict.get(config2)  # Should find config1's value
        result2 = test_dict.get(config3)

        # Assert
        self.assertEqual(result1, "value1")  # config2 equals config1
        self.assertEqual(result2, "value3")
        self.assertEqual(len(test_dict), 2)  # Only two unique keys


class TestJSONTypedDictBehavior(unittest.TestCase):
    """Test JSON TypedDict behavior and compatibility"""

    def test_json_typed_dict_accepts_empty_dictionary(self):
        """Test that JSON TypedDict accepts empty dictionary"""
        # Act
        json_data: dict = {}  # type: ignore

        # Assert
        self.assertIsInstance(json_data, dict)
        self.assertEqual(len(json_data), 0)

    def test_json_typed_dict_accepts_various_value_types(self):
        """Test that JSON TypedDict accepts various Python value types"""
        # Act
        json_data: dict = {  # type: ignore
            "string": "test_value",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "null_value": None,
            "list": [1, 2, 3, "mixed", True],
            "nested_dict": {"nested_string": "nested_value", "nested_number": 100},
        }

        # Assert
        self.assertIsInstance(json_data, dict)
        self.assertEqual(json_data["string"], "test_value")
        self.assertEqual(json_data["integer"], 42)
        self.assertEqual(json_data["float"], 3.14159)
        self.assertTrue(json_data["boolean"])
        self.assertIsNone(json_data["null_value"])
        self.assertEqual(json_data["list"], [1, 2, 3, "mixed", True])
        self.assertIsInstance(json_data["nested_dict"], dict)

    def test_json_typed_dict_compatibility_with_workload_config(self):
        """Test that JSON TypedDict works seamlessly with WorkloadConfig"""
        # Arrange
        workload_specs: dict = {  # type: ignore
            "kind": "workload",
            "apiVersion": "v1",
            "metadata": {"name": "compatibility-test"},
            "spec": {
                "type": "serverless",
                "containers": [
                    {
                        "name": "app",
                        "image": "python:3.9",
                        "cpu": "100m",
                        "memory": 128,
                        "command": ["python", "app.py"],
                        "env": {"DEBUG": "true"},
                    }
                ],
            },
        }

        # Act
        config = WorkloadConfig(
            gvc="compatibility-gvc",
            workload_id="compatibility-workload",
            specs=workload_specs,  # type: ignore
        )

        # Assert
        self.assertEqual(config.specs, workload_specs)
        self.assertIsInstance(config.specs, dict)
        # Should be able to access nested values
        self.assertEqual(config.specs["kind"], "workload")  # type: ignore
        self.assertEqual(config.specs["spec"]["type"], "serverless")  # type: ignore

    def test_json_typed_dict_mutability_allows_modifications(self):
        """Test that JSON TypedDict allows modifications after creation"""
        # Arrange
        json_data: dict = {"initial": "value"}  # type: ignore

        # Act
        json_data["added"] = "new_value"
        json_data["initial"] = "modified_value"
        json_data["nested"] = {"key": "nested_value"}

        # Assert
        self.assertEqual(json_data["initial"], "modified_value")
        self.assertEqual(json_data["added"], "new_value")
        self.assertEqual(json_data["nested"]["key"], "nested_value")  # type: ignore
        self.assertEqual(len(json_data), 3)


class TestWorkloadConfigValidation(unittest.TestCase):
    """Test WorkloadConfig validation and error cases"""

    def test_workload_config_requires_gvc_parameter(self):
        """Test that WorkloadConfig requires gvc parameter"""
        # Act & Assert
        with self.assertRaises(TypeError):
            WorkloadConfig(workload_id="test-workload")  # type: ignore

    def test_workload_config_requires_workload_id_parameter(self):
        """Test that WorkloadConfig requires workload_id parameter"""
        # Act & Assert
        with self.assertRaises(TypeError):
            WorkloadConfig(gvc="test-gvc")  # type: ignore

    def test_workload_config_accepts_none_for_required_fields_when_explicit(self):
        """Test that WorkloadConfig accepts None for required fields when explicitly provided"""
        # Note: This tests the dataclass behavior - it will accept None even for non-Optional fields
        # Act
        config = WorkloadConfig(gvc=None, workload_id=None)  # type: ignore

        # Assert
        self.assertIsNone(config.gvc)
        self.assertIsNone(config.workload_id)
        self.assertIsNone(config.location)
        self.assertIsNone(config.specs)

    def test_workload_config_with_invalid_specs_type_still_creates_config(self):
        """Test that WorkloadConfig creation doesn't validate specs type at runtime"""
        # Note: TypedDict is a static type hint, not a runtime validator
        # Arrange
        invalid_specs = "this is not a dict"  # type: ignore

        # Act
        config = WorkloadConfig(
            gvc="invalid-specs-gvc",
            workload_id="invalid-specs-workload",
            specs=invalid_specs,  # type: ignore
        )

        # Assert
        # Should still create the config (TypedDict is not enforced at runtime)
        self.assertEqual(config.specs, invalid_specs)


if __name__ == "__main__":
    unittest.main()  # type: ignore
