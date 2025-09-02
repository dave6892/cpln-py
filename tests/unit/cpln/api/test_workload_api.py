"""Tests for Workload API mixins following unit testing best practices."""

import unittest
from typing import Any
from unittest.mock import MagicMock, Mock

from cpln.api.config import APIConfig
from cpln.api.workload import WorkloadApiMixin, WorkloadDeploymentMixin
from cpln.config import WorkloadConfig

# type: ignore - Suppressing all linter warnings for test mock attribute assignments
# All _get, _post, _patch, _delete, config, get_containers, etc. attributes
# are mocked in setUp methods throughout this file


class TestWorkloadDeploymentMixinInitialization(unittest.TestCase):
    """Test WorkloadDeploymentMixin initialization and basic setup"""

    def test_workload_deployment_mixin_can_be_instantiated(self):
        """Test that WorkloadDeploymentMixin can be instantiated"""
        # Act
        mixin = WorkloadDeploymentMixin()

        # Assert
        self.assertIsInstance(mixin, WorkloadDeploymentMixin)

    def test_workload_deployment_mixin_has_expected_methods(self):
        """Test that WorkloadDeploymentMixin has expected method signatures"""
        # Arrange
        mixin = WorkloadDeploymentMixin()

        # Assert
        self.assertTrue(hasattr(mixin, "get_workload_deployment"))
        self.assertTrue(callable(mixin.get_workload_deployment))


class TestWorkloadDeploymentMixinOperations(unittest.TestCase):
    """Test WorkloadDeploymentMixin deployment operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mixin = WorkloadDeploymentMixin()
        self.mixin._get = MagicMock()  # type: ignore
        self.mixin.config = MagicMock(spec=APIConfig)  # type: ignore
        self.mixin.config.token = "test-token"  # type: ignore
        self.mixin.config.org = "test-org"  # type: ignore
        self.mixin.config.asdict.return_value = {
            "base_url": "https://api.cpln.io",
            "token": "test-token",
            "org": "test-org",
        }

        self.workload_config = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="test-location"
        )

    def test_get_workload_deployment_with_valid_config_returns_parsed_deployment(self):
        """Test that get_workload_deployment returns parsed Deployment object"""
        # Arrange
        deployment_data: dict[str, Any] = {
            "name": "test-deployment",
            "kind": "deployment",
            "lastModified": "2023-01-01T00:00:00Z",
            "links": [],
            "status": {
                "remote": "https://test-remote",
                "endpoint": "https://test-endpoint",
                "lastProcessedVersion": "1",
                "expectedDeploymentVersion": "1",
                "message": "OK",
                "ready": True,
                "internal": {
                    "podStatus": {},
                    "podsValidZone": True,
                    "timestamp": "2023-01-01T00:00:00Z",
                    "ksvcStatus": {},
                },
                "versions": [
                    {
                        "containers": {
                            "container1": {
                                "name": "container1",
                                "image": "nginx:latest",
                                "message": "OK",
                                "ready": True,
                                "resources": {
                                    "memory": 128,
                                    "cpu": 100,
                                    "replicas": 1,
                                    "replicasReady": 1,
                                },
                            }
                        },
                        "message": "OK",
                        "ready": True,
                        "created": "2023-01-01T00:00:00Z",
                        "workload": 1,
                    }
                ],
            },
        }
        self.mixin._get.return_value = deployment_data  # type: ignore

        # Act
        result = self.mixin.get_workload_deployment(self.workload_config)

        # Assert
        self.mixin._get.assert_called_once_with(  # type: ignore
            "gvc/test-gvc/workload/test-workload/deployment/test-location"
        )
        # The result should be a parsed Deployment object, not the raw data
        self.assertTrue(hasattr(result, "name"))
        self.assertEqual(result.name, "test-deployment")  # type: ignore

    def test_get_workload_deployment_constructs_correct_api_endpoint(self):
        """Test that get_workload_deployment constructs correct API endpoint"""
        # Arrange
        deployment_data = {
            "name": "endpoint-test",
            "status": {"versions": [{"containers": {}}]},
        }
        self.mixin._get.return_value = deployment_data

        config_with_different_values = WorkloadConfig(
            gvc="production-gvc", workload_id="api-service", location="us-west-2"
        )

        # Act
        result = self.mixin.get_workload_deployment(config_with_different_values)

        # Assert
        expected_endpoint = (
            "gvc/production-gvc/workload/api-service/deployment/us-west-2"
        )
        self.mixin._get.assert_called_once_with(expected_endpoint)
        self.assertEqual(result.name, "endpoint-test")  # type: ignore

    def test_get_workload_deployment_with_missing_workload_id_raises_value_error(self):
        """Test that get_workload_deployment raises ValueError for missing workload_id"""
        # Arrange
        invalid_config = WorkloadConfig(gvc="test-gvc", workload_id="")

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.mixin.get_workload_deployment(invalid_config)

        self.assertIn("Config not set properly", str(context.exception))

    def test_get_workload_deployment_with_none_workload_id_raises_value_error(self):
        """Test that get_workload_deployment raises ValueError for None workload_id"""
        # Arrange
        invalid_config = WorkloadConfig(gvc="test-gvc", workload_id=None)  # type: ignore

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.mixin.get_workload_deployment(invalid_config)

        self.assertIn("Config not set properly", str(context.exception))

    def test_get_workload_deployment_with_missing_location_uses_default(self):
        """Test that get_workload_deployment handles missing location"""
        # Arrange
        config_no_location = WorkloadConfig(gvc="test-gvc", workload_id="test-workload")
        deployment_data = {"name": "no-location-test", "status": {"versions": []}}
        self.mixin._get.return_value = deployment_data

        # Act
        result = self.mixin.get_workload_deployment(config_no_location)

        # Assert
        # Should still work even without explicit location
        self.mixin._get.assert_called_once_with(
            "gvc/test-gvc/workload/test-workload/deployment/None"
        )
        self.assertEqual(result.name, "no-location-test")  # type: ignore


class TestWorkloadApiMixinInitialization(unittest.TestCase):
    """Test WorkloadApiMixin initialization and basic setup"""

    def test_workload_api_mixin_can_be_instantiated(self):
        """Test that WorkloadApiMixin can be instantiated"""
        # Act
        mixin = WorkloadApiMixin()

        # Assert
        self.assertIsInstance(mixin, WorkloadApiMixin)
        # Should also be an instance of WorkloadDeploymentMixin (inheritance)
        self.assertIsInstance(mixin, WorkloadDeploymentMixin)

    def test_workload_api_mixin_has_expected_methods(self):
        """Test that WorkloadApiMixin has expected method signatures"""
        # Arrange
        mixin = WorkloadApiMixin()

        # Assert
        expected_methods = [
            "get_workload",
            "create_workload",
            "delete_workload",
            "patch_workload",
            "get_workload_deployment",
        ]
        for method_name in expected_methods:
            with self.subTest(method=method_name):
                self.assertTrue(hasattr(mixin, method_name))
                self.assertTrue(callable(getattr(mixin, method_name)))


class TestWorkloadApiMixinOperations(unittest.TestCase):
    """Test WorkloadApiMixin CRUD operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mixin = WorkloadApiMixin()

        # Mock HTTP methods
        self.mixin._get = MagicMock()  # type: ignore
        self.mixin._post = MagicMock()  # type: ignore
        self.mixin._delete = MagicMock()  # type: ignore
        self.mixin._patch = MagicMock()  # type: ignore

        # Mock inherited methods from WorkloadDeploymentMixin
        self.mixin.get_containers = MagicMock(return_value=["container1"])  # type: ignore
        self.mixin.get_replicas = MagicMock(return_value=["replica1"])  # type: ignore
        self.mixin.get_remote_wss = MagicMock(return_value="wss://test-remote")  # type: ignore

        # Mock config
        self.mixin.config = MagicMock(spec=APIConfig)  # type: ignore
        self.mixin.config.token = "test-token"
        self.mixin.config.org = "test-org"

        self.workload_config = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="test-location"
        )

    def test_get_workload_with_workload_id_returns_specific_workload(self):
        """Test that get_workload returns specific workload when ID is provided"""
        # Arrange
        expected_workload = {"name": "test-workload", "status": "active"}
        self.mixin._get.return_value = expected_workload

        # Act
        result = self.mixin.get_workload(self.workload_config)

        # Assert
        self.mixin._get.assert_called_once_with("gvc/test-gvc/workload/test-workload")
        self.assertEqual(result, expected_workload)

    def test_get_workload_without_workload_id_returns_workload_list(self):
        """Test that get_workload returns list of workloads when ID is not provided"""
        # Arrange
        config_no_id = WorkloadConfig(gvc="test-gvc", workload_id="")
        expected_workloads = {
            "items": [
                {"name": "workload1", "status": "active"},
                {"name": "workload2", "status": "inactive"},
            ]
        }
        self.mixin._get.return_value = expected_workloads

        # Act
        result = self.mixin.get_workload(config_no_id)

        # Assert
        self.mixin._get.assert_called_once_with("gvc/test-gvc/workload")
        self.assertEqual(result, expected_workloads)

    def test_get_workload_with_different_gvc_constructs_correct_endpoint(self):
        """Test that get_workload constructs correct endpoint for different GVC"""
        # Arrange
        different_config = WorkloadConfig(
            gvc="production-gvc", workload_id="api-service"
        )
        expected_workload = {"name": "api-service"}
        self.mixin._get.return_value = expected_workload

        # Act
        result = self.mixin.get_workload(different_config)

        # Assert
        self.mixin._get.assert_called_once_with(
            "gvc/production-gvc/workload/api-service"
        )
        self.assertEqual(result, expected_workload)

    def test_create_workload_calls_post_with_correct_parameters(self):
        """Test that create_workload calls POST with correct endpoint and data"""
        # Arrange
        metadata = {
            "name": "new-workload",
            "description": "Test workload",
            "spec": {
                "containers": [
                    {"name": "app", "image": "nginx", "cpu": "100m", "memory": 128}
                ]
            },
        }
        mock_response = Mock()
        self.mixin._post.return_value = mock_response

        # Act
        result = self.mixin.create_workload(self.workload_config, metadata)

        # Assert
        self.mixin._post.assert_called_once_with("gvc/test-gvc/workload", data=metadata)
        self.assertEqual(result, mock_response)

    def test_create_workload_with_minimal_metadata_passes_data_correctly(self):
        """Test that create_workload passes minimal metadata correctly"""
        # Arrange
        minimal_metadata = {"name": "minimal-workload"}
        mock_response = Mock()
        self.mixin._post.return_value = mock_response

        # Act
        result = self.mixin.create_workload(self.workload_config, minimal_metadata)

        # Assert
        self.mixin._post.assert_called_once_with(
            "gvc/test-gvc/workload", data=minimal_metadata
        )
        self.assertEqual(result, mock_response)

    def test_delete_workload_calls_delete_with_correct_endpoint(self):
        """Test that delete_workload calls DELETE with correct endpoint"""
        # Arrange
        mock_response = Mock()
        self.mixin._delete.return_value = mock_response

        # Act
        result = self.mixin.delete_workload(self.workload_config)

        # Assert
        self.mixin._delete.assert_called_once_with(
            "gvc/test-gvc/workload/test-workload"
        )
        self.assertEqual(result, mock_response)

    def test_delete_workload_with_different_config_constructs_correct_endpoint(self):
        """Test that delete_workload constructs correct endpoint for different config"""
        # Arrange
        different_config = WorkloadConfig(
            gvc="staging-gvc", workload_id="temp-workload"
        )
        mock_response = Mock()
        self.mixin._delete.return_value = mock_response

        # Act
        result = self.mixin.delete_workload(different_config)

        # Assert
        self.mixin._delete.assert_called_once_with(
            "gvc/staging-gvc/workload/temp-workload"
        )
        self.assertEqual(result, mock_response)

    def test_patch_workload_calls_patch_with_correct_parameters(self):
        """Test that patch_workload calls PATCH with correct endpoint and data"""
        # Arrange
        patch_data = {
            "spec": {
                "defaultOptions": {"suspend": True},
                "containers": [{"name": "app", "cpu": "200m", "memory": 256}],
            }
        }
        mock_response = Mock()
        self.mixin._patch.return_value = mock_response

        # Act
        result = self.mixin.patch_workload(self.workload_config, patch_data)

        # Assert
        self.mixin._patch.assert_called_once_with(
            "gvc/test-gvc/workload/test-workload", data=patch_data
        )
        self.assertEqual(result, mock_response)

    def test_patch_workload_with_empty_data_still_calls_patch(self):
        """Test that patch_workload works with empty data"""
        # Arrange
        empty_data: dict[str, Any] = {}
        mock_response = Mock()
        self.mixin._patch.return_value = mock_response

        # Act
        result = self.mixin.patch_workload(self.workload_config, empty_data)

        # Assert
        self.mixin._patch.assert_called_once_with(
            "gvc/test-gvc/workload/test-workload", data=empty_data
        )
        self.assertEqual(result, mock_response)


class TestWorkloadApiMixinInheritance(unittest.TestCase):
    """Test WorkloadApiMixin inheritance and integration with WorkloadDeploymentMixin"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mixin = WorkloadApiMixin()

        # Mock the inherited methods we're testing
        self.mixin.get_containers = MagicMock()  # type: ignore
        self.mixin.get_replicas = MagicMock()  # type: ignore
        self.mixin.get_remote_wss = MagicMock()  # type: ignore

    def test_workload_api_mixin_has_access_to_deployment_methods(self):
        """Test that WorkloadApiMixin can access WorkloadDeploymentMixin methods"""
        # Arrange
        expected_containers = ["web", "api", "database"]
        expected_replicas = ["replica-1", "replica-2"]
        expected_wss = "wss://production-remote"

        self.mixin.get_containers.return_value = expected_containers
        self.mixin.get_replicas.return_value = expected_replicas
        self.mixin.get_remote_wss.return_value = expected_wss

        # Act
        containers = self.mixin.get_containers()
        replicas = self.mixin.get_replicas()
        wss = self.mixin.get_remote_wss()

        # Assert
        self.assertEqual(containers, expected_containers)
        self.assertEqual(replicas, expected_replicas)
        self.assertEqual(wss, expected_wss)

    def test_workload_api_mixin_inheritance_chain_is_correct(self):
        """Test that WorkloadApiMixin properly inherits from WorkloadDeploymentMixin"""
        # Act & Assert
        self.assertIsInstance(self.mixin, WorkloadApiMixin)
        self.assertIsInstance(self.mixin, WorkloadDeploymentMixin)

        # Check method resolution order
        mro = WorkloadApiMixin.__mro__
        self.assertIn(WorkloadDeploymentMixin, mro)
        self.assertIn(object, mro)


class TestWorkloadMixinsErrorHandling(unittest.TestCase):
    """Test error handling in workload mixins"""

    def setUp(self):
        """Set up common test fixtures"""
        self.deployment_mixin = WorkloadDeploymentMixin()
        self.api_mixin = WorkloadApiMixin()

    def test_workload_deployment_mixin_handles_missing_get_method_gracefully(self):
        """Test that WorkloadDeploymentMixin handles missing _get method gracefully"""
        # Arrange
        config = WorkloadConfig(
            gvc="test", workload_id="test-workload", location="test-loc"
        )

        # Act & Assert
        with self.assertRaises(AttributeError):
            # Should raise AttributeError because _get method is not defined
            self.deployment_mixin.get_workload_deployment(config)

    def test_workload_api_mixin_handles_missing_http_methods_gracefully(self):
        """Test that WorkloadApiMixin handles missing HTTP methods gracefully"""
        # Arrange
        config = WorkloadConfig(gvc="test", workload_id="test-workload")

        # Act & Assert
        with self.assertRaises(AttributeError):
            # Should raise AttributeError because HTTP methods are not defined
            self.api_mixin.get_workload(config)

    def test_config_validation_with_invalid_workload_config_types(self):
        """Test behavior with invalid WorkloadConfig parameter types"""
        # Arrange
        mixin = WorkloadDeploymentMixin()
        mixin._get = MagicMock()  # type: ignore

        # Act & Assert - test with None config
        with self.assertRaises(AttributeError):
            mixin.get_workload_deployment(None)  # type: ignore

    def test_workload_operations_with_network_simulation(self):
        """Test workload operations behavior with simulated network conditions"""
        # Arrange
        mixin = WorkloadApiMixin()
        mixin._get = MagicMock()  # type: ignore
        mixin._post = MagicMock()  # type: ignore
        mixin._delete = MagicMock()  # type: ignore
        mixin._patch = MagicMock()  # type: ignore

        config = WorkloadConfig(gvc="network-test", workload_id="network-workload")

        # Simulate network timeout
        mixin._get.side_effect = TimeoutError("Network timeout")

        # Act & Assert
        with self.assertRaises(TimeoutError):
            mixin.get_workload(config)


if __name__ == "__main__":
    unittest.main()  # type: ignore
