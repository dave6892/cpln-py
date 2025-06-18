from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from cpln.api.config import APIConfig
from cpln.api.workload import WorkloadApiMixin, WorkloadDeploymentMixin
from cpln.config import WorkloadConfig


class TestWorkloadDeploymentMixin:
    """Tests for the WorkloadDeploymentMixin class"""

    def setup_method(self) -> None:
        """Set up the test"""
        self.mixin: WorkloadDeploymentMixin = WorkloadDeploymentMixin()
        self.mixin._get = MagicMock()
        self.mixin.config = MagicMock(spec=APIConfig)
        self.mixin.config.token = "test-token"
        self.mixin.config.org = "test-org"
        self.mixin.config.asdict.return_value = {
            "base_url": "https://api.cpln.io",
            "token": "test-token",
            "org": "test-org",
        }

        self.config: WorkloadConfig = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="test-location"
        )

    def test_get_workload_deployment(self) -> None:
        """Test get_workload_deployment method"""
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
        self.mixin._get.return_value = deployment_data
        result = self.mixin.get_workload_deployment(self.config)

        self.mixin._get.assert_called_once_with(
            "gvc/test-gvc/workload/test-workload/deployment/test-location"
        )
        # The result should be a parsed Deployment object, not the raw data
        assert hasattr(result, "name")
        assert result.name == "test-deployment"

    def test_get_workload_deployment_invalid_config(self) -> None:
        """Test get_workload_deployment with invalid config"""
        invalid_config: WorkloadConfig = WorkloadConfig(
            gvc="test-gvc", workload_id=None
        )

        with pytest.raises(ValueError, match="Config not set properly"):
            self.mixin.get_workload_deployment(invalid_config)

    # def test_get_containers(self) -> None:
    #     """Test get_containers method"""
    #     deployment_data: Dict[str, Any] = {
    #         "status": {
    #             "versions": [
    #                 {
    #                     "containers": {
    #                         "container1": {},
    #                         "container2": {},
    #                         "cpln-mounter": {},  # This should be ignored
    #                     }
    #                 }
    #             ]
    #         }
    #     }
    #     self.mixin.get_workload_deployment = MagicMock(return_value=deployment_data)

    #     result = self.mixin.get_containers(self.config)

    #     self.assertIsInstance(result, list)
    #     self.assertEqual(len(result), 2)  # Should ignore cpln-mounter
    #     self.assertIn("container1", result)
    #     self.assertIn("container2", result)
    #     self.assertNotIn("cpln-mounter", result)


class TestWorkloadApiMixin:
    """Tests for the WorkloadApiMixin class"""

    def setup_method(self) -> None:
        """Set up the test"""
        self.mixin: WorkloadApiMixin = WorkloadApiMixin()
        self.mixin._get = MagicMock()
        self.mixin._post = MagicMock()
        self.mixin._delete = MagicMock()
        self.mixin._patch = MagicMock()

        # Since WorkloadApiMixin inherits from WorkloadDeploymentMixin,
        # we need to mock those methods too
        self.mixin.get_containers = MagicMock(return_value=["container1"])
        self.mixin.get_replicas = MagicMock(return_value=["replica1"])
        self.mixin.get_remote_wss = MagicMock(return_value="wss://test-remote")

        self.mixin.config = MagicMock(spec=APIConfig)
        self.mixin.config.token = "test-token"
        self.mixin.config.org = "test-org"

        self.config: WorkloadConfig = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="test-location"
        )

    def test_get_workload_with_id(self) -> None:
        """Test get_workload method with workload ID"""
        self.mixin._get.return_value = {"name": "test-workload"}

        result = self.mixin.get_workload(self.config)

        self.mixin._get.assert_called_once_with("gvc/test-gvc/workload/test-workload")
        assert result == {"name": "test-workload"}

    def test_get_workload_without_id(self) -> None:
        """Test get_workload method without workload ID"""
        config: WorkloadConfig = WorkloadConfig(gvc="test-gvc")
        self.mixin._get.return_value = {
            "items": [{"name": "workload1"}, {"name": "workload2"}]
        }

        result = self.mixin.get_workload(config)

        self.mixin._get.assert_called_once_with("gvc/test-gvc/workload")
        assert result == {"items": [{"name": "workload1"}, {"name": "workload2"}]}

    def test_create_workload(self) -> None:
        """Test create_workload method"""
        metadata: dict[str, str] = {
            "name": "new-workload",
            "description": "Test workload",
        }
        mock_response: Mock = Mock()
        self.mixin._post.return_value = mock_response

        result = self.mixin.create_workload(self.config, metadata)

        self.mixin._post.assert_called_once_with("gvc/test-gvc/workload", data=metadata)
        assert result == mock_response

    def test_delete_workload(self) -> None:
        """Test delete_workload method"""
        mock_response: Mock = Mock()
        self.mixin._delete.return_value = mock_response

        result = self.mixin.delete_workload(self.config)

        self.mixin._delete.assert_called_once_with(
            "gvc/test-gvc/workload/test-workload"
        )
        assert result == mock_response

    def test_patch_workload(self) -> None:
        """Test patch_workload method"""
        data: dict[str, Any] = {"spec": {"defaultOptions": {"suspend": "true"}}}
        mock_response: Mock = Mock()
        self.mixin._patch.return_value = mock_response

        result = self.mixin.patch_workload(self.config, data)

        self.mixin._patch.assert_called_once_with(
            "gvc/test-gvc/workload/test-workload", data=data
        )
        assert result == mock_response
