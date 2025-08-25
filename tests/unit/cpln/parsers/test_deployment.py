"""Tests for the deployment parser module."""

from unittest.mock import Mock, patch

import pytest
from cpln.api.config import APIConfig
from cpln.errors import WebSocketExitCodeError
from cpln.parsers.deployment import (
    ContainerDeployment,
    Deployment,
    Internal,
    Link,
    Status,
    Version,
    WorkloadReplica,
)


class TestContainerDeployment:
    def test_parse_basic(self):
        data = {
            "name": "test-container",
            "image": "nginx:latest",
            "ready": True,
            "message": "Ready",
            "resources": {"memory": 128, "cpu": 100, "replicas": 1, "replicasReady": 1},
        }
        container = ContainerDeployment.parse(data)
        assert container.name == "test-container"
        assert container.image == "nginx:latest"
        assert container.ready is True
        assert container.message == "Ready"
        assert container.resources.memory == 128
        assert container.resources.cpu == 100

    def test_is_healthy_when_ready_and_has_replicas(self):
        data = {
            "name": "healthy-container",
            "image": "nginx:latest",
            "ready": True,
            "message": "Running",
            "resources": {"memory": 128, "cpu": 100, "replicas": 2, "replicasReady": 2},
        }
        container = ContainerDeployment.parse(data)
        assert container.is_healthy() is True

    def test_is_healthy_when_not_ready(self):
        data = {
            "name": "unhealthy-container",
            "image": "nginx:latest",
            "ready": False,
            "message": "Starting",
            "resources": {"memory": 128, "cpu": 100, "replicas": 1, "replicasReady": 0},
        }
        container = ContainerDeployment.parse(data)
        assert container.is_healthy() is False

    def test_is_healthy_when_no_ready_replicas(self):
        data = {
            "name": "unhealthy-container",
            "image": "nginx:latest",
            "ready": True,
            "message": "Ready",
            "resources": {"memory": 128, "cpu": 100, "replicas": 2, "replicasReady": 0},
        }
        container = ContainerDeployment.parse(data)
        assert container.is_healthy() is False

    def test_is_healthy_with_error_message(self):
        data = {
            "name": "error-container",
            "image": "nginx:latest",
            "ready": True,
            "message": "Container failed to start",
            "resources": {"memory": 128, "cpu": 100, "replicas": 1, "replicasReady": 1},
        }
        container = ContainerDeployment.parse(data)
        assert container.is_healthy() is False

    def test_get_resource_utilization_full_replicas(self):
        data = {
            "name": "test-container",
            "image": "nginx:latest",
            "ready": True,
            "message": "Ready",
            "resources": {"memory": 128, "cpu": 100, "replicas": 3, "replicasReady": 3},
        }
        container = ContainerDeployment.parse(data)
        utilization = container.get_resource_utilization()

        assert utilization["replica_utilization"] == 100.0
        assert utilization["cpu"] is None  # Placeholder
        assert utilization["memory"] is None  # Placeholder

    def test_get_resource_utilization_partial_replicas(self):
        data = {
            "name": "test-container",
            "image": "nginx:latest",
            "ready": True,
            "message": "Ready",
            "resources": {"memory": 128, "cpu": 100, "replicas": 4, "replicasReady": 2},
        }
        container = ContainerDeployment.parse(data)
        utilization = container.get_resource_utilization()

        assert utilization["replica_utilization"] == 50.0
        assert utilization["cpu"] is None
        assert utilization["memory"] is None

    def test_get_resource_utilization_no_replicas(self):
        data = {
            "name": "test-container",
            "image": "nginx:latest",
            "ready": False,
            "message": "Stopped",
            "resources": {"memory": 128, "cpu": 100, "replicas": 0, "replicasReady": 0},
        }
        container = ContainerDeployment.parse(data)
        utilization = container.get_resource_utilization()

        assert utilization["replica_utilization"] == 0.0
        assert utilization["cpu"] is None
        assert utilization["memory"] is None


class TestVersion:
    def test_parse_with_containers(self):
        data = {
            "message": "Deployment ready",
            "ready": True,
            "created": "2023-01-01T00:00:00Z",
            "workload": 1,
            "containers": {
                "container1": {
                    "name": "test-container",
                    "image": "nginx:latest",
                    "ready": True,
                    "message": "Ready",
                    "resources": {
                        "memory": 128,
                        "cpu": 100,
                        "replicas": 1,
                        "replicasReady": 1,
                    },
                }
            },
        }
        version = Version.parse(data)
        assert version.message == "Deployment ready"
        assert version.ready is True
        assert version.created == "2023-01-01T00:00:00Z"
        assert version.workload == 1
        assert len(version.containers) == 1
        assert version.containers[0].name == "test-container"


class TestInternal:
    def test_parse_basic(self):
        data = {
            "podStatus": {"phase": "Running"},
            "podsValidZone": True,
            "timestamp": "2023-01-01T00:00:00Z",
            "ksvcStatus": {"ready": True},
        }
        internal = Internal.parse(data)
        assert internal.pod_status == {"phase": "Running"}
        assert internal.pods_valid_zone is True
        assert internal.timestamp == "2023-01-01T00:00:00Z"
        assert internal.ksvc_status == {"ready": True}

    def test_post_init_with_none_values(self):
        """Test that __post_init__ properly initializes None values to empty dicts."""
        internal = Internal(
            pod_status=None,
            pods_valid_zone=False,
            timestamp="",
            ksvc_status=None,
        )
        # __post_init__ should have converted None values to empty dicts
        assert internal.pod_status == {}
        assert internal.ksvc_status == {}
        assert internal.pods_valid_zone is False
        assert internal.timestamp == ""


class TestStatus:
    def test_parse_with_internal_and_versions(self):
        data = {
            "endpoint": "https://example.com",
            "remote": "https://remote.example.com",
            "lastProcessedVersion": "v1",
            "expectedDeploymentVersion": "v1",
            "message": "Ready",
            "ready": True,
            "internal": {
                "podStatus": {"phase": "Running"},
                "podsValidZone": True,
                "timestamp": "2023-01-01T00:00:00Z",
                "ksvcStatus": {"ready": True},
            },
            "versions": [
                {
                    "message": "Deployment ready",
                    "ready": True,
                    "created": "2023-01-01T00:00:00Z",
                    "workload": 1,
                    "containers": {
                        "container1": {
                            "name": "test-container",
                            "image": "nginx:latest",
                            "ready": True,
                            "message": "Ready",
                            "resources": {
                                "memory": 128,
                                "cpu": 100,
                                "replicas": 1,
                                "replicasReady": 1,
                            },
                        }
                    },
                }
            ],
        }
        status = Status.parse(data)
        assert status.endpoint == "https://example.com"
        assert status.remote == "https://remote.example.com"
        assert status.last_processed_version == "v1"
        assert status.expected_deployment_version == "v1"
        assert status.message == "Ready"
        assert status.ready is True
        assert isinstance(status.internal, Internal)
        assert len(status.versions) == 1
        assert isinstance(status.versions[0], Version)


class TestLink:
    def test_parse_basic(self):
        data = {"rel": "self", "href": "https://example.com/api/workload/test"}
        link = Link.parse(data)
        assert link.rel == "self"
        assert link.href == "https://example.com/api/workload/test"


class TestWorkloadReplica:
    def setup_method(self):
        self.api_config = APIConfig(token="test-token", org="test-org")
        # Use Mock for workload config to avoid constructor issues
        self.workload_config = Mock()
        self.workload_config.gvc = "test-gvc"
        self.workload_config.workload_id = "test-workload"
        self.workload_config.container = "test-container"
        self.workload_config.replica = "test-replica"
        self.workload_config.remote_wss = "wss://test.com"

    def test_exec_validation_errors(self):
        # Test missing container
        config_mock = Mock()
        config_mock.container = None
        config_mock.replica = "test-replica"
        config_mock.remote_wss = "wss://test.com"
        config_mock.gvc = "test-gvc"

        replica = WorkloadReplica(
            name="test-replica",
            container=None,
            config=config_mock,
            api_config=self.api_config,
            remote_wss="wss://test.com",
        )

        with pytest.raises(ValueError, match="Container not set"):
            replica.exec("echo test")

        # Test missing replica
        config_mock2 = Mock()
        config_mock2.container = "test-container"
        config_mock2.replica = None
        config_mock2.remote_wss = "wss://test.com"
        config_mock2.gvc = "test-gvc"

        replica = WorkloadReplica(
            name=None,
            container="test-container",
            config=config_mock2,
            api_config=self.api_config,
            remote_wss="wss://test.com",
        )

        with pytest.raises(ValueError, match="Replica not set"):
            replica.exec("echo test")

        # Test missing remote WSS
        config_mock3 = Mock()
        config_mock3.container = "test-container"
        config_mock3.replica = "test-replica"
        config_mock3.remote_wss = None
        config_mock3.gvc = "test-gvc"

        replica = WorkloadReplica(
            name="test-replica",
            container="test-container",
            config=config_mock3,
            api_config=self.api_config,
            remote_wss=None,
        )

        with pytest.raises(ValueError, match="Remote WSS not set"):
            replica.exec("echo test")

    @patch("cpln.parsers.deployment.WebSocketAPI")
    def test_exec_success_with_string_command(self, mock_websocket):
        mock_websocket_instance = Mock()
        mock_websocket.return_value = mock_websocket_instance
        mock_websocket_instance.exec.return_value = {"status": "success"}

        replica = WorkloadReplica(
            name="test-replica",
            container="test-container",
            config=self.workload_config,
            api_config=self.api_config,
            remote_wss="wss://test.com",
        )

        result = replica.exec("echo test")

        assert result == {"status": "success"}
        mock_websocket_instance.exec.assert_called_once_with(
            token="test-token",
            org="test-org",
            gvc="test-gvc",
            container="test-container",
            pod="test-replica",
            command=["echo", "test"],
        )

    @patch("cpln.parsers.deployment.WebSocketAPI")
    def test_exec_success_with_list_command(self, mock_websocket):
        mock_websocket_instance = Mock()
        mock_websocket.return_value = mock_websocket_instance
        mock_websocket_instance.exec.return_value = {"status": "success"}

        replica = WorkloadReplica(
            name="test-replica",
            container="test-container",
            config=self.workload_config,
            api_config=self.api_config,
            remote_wss="wss://test.com",
        )

        result = replica.exec(["echo", "test"])

        assert result == {"status": "success"}
        mock_websocket_instance.exec.assert_called_once_with(
            token="test-token",
            org="test-org",
            gvc="test-gvc",
            container="test-container",
            pod="test-replica",
            command=["echo", "test"],
        )

    @patch("cpln.parsers.deployment.WebSocketAPI")
    def test_exec_websocket_error(self, mock_websocket):
        mock_websocket_instance = Mock()
        mock_websocket.return_value = mock_websocket_instance
        mock_websocket_instance.exec.side_effect = WebSocketExitCodeError(
            "Command failed", 1
        )

        replica = WorkloadReplica(
            name="test-replica",
            container="test-container",
            config=self.workload_config,
            api_config=self.api_config,
            remote_wss="wss://test.com",
        )

        with pytest.raises(WebSocketExitCodeError):
            replica.exec("echo test")

    @patch("cpln.parsers.deployment.WebSocketAPI")
    def test_ping(self, mock_websocket):
        mock_websocket_instance = Mock()
        mock_websocket.return_value = mock_websocket_instance
        mock_websocket_instance.exec.return_value = {"status": "success"}

        replica = WorkloadReplica(
            name="test-replica",
            container="test-container",
            config=self.workload_config,
            api_config=self.api_config,
            remote_wss="wss://test.com",
        )

        replica.ping()

        mock_websocket_instance.exec.assert_called_once_with(
            token="test-token",
            org="test-org",
            gvc="test-gvc",
            container="test-container",
            pod="test-replica",
            command=["echo", "ping"],
        )


class TestDeployment:
    def setup_method(self):
        self.api_client = Mock()
        self.api_client.config = Mock()
        self.api_client.config.__post_init__ = Mock()
        # Use Mock for workload config to avoid constructor issues
        self.workload_config = Mock()
        self.workload_config.gvc = "test-gvc"
        self.workload_config.workload_id = "test-workload"

    @patch.object(Deployment, "__post_init__", return_value=None)
    def test_parse_deployment(self, mock_post_init):
        data = {
            "name": "test-deployment",
            "status": {
                "endpoint": "https://example.com",
                "remote": "https://remote.example.com",
                "lastProcessedVersion": "v1",
                "expectedDeploymentVersion": "v1",
                "message": "Ready",
                "ready": True,
                "internal": {
                    "podStatus": {"phase": "Running"},
                    "podsValidZone": True,
                    "timestamp": "2023-01-01T00:00:00Z",
                    "ksvcStatus": {"ready": True},
                },
                "versions": [],
            },
            "lastModified": "2023-01-01T00:00:00Z",
            "kind": "Deployment",
            "links": [
                {"rel": "self", "href": "https://example.com/api/deployment/test"}
            ],
        }

        deployment = Deployment.parse(data, self.api_client, self.workload_config)

        assert deployment.name == "test-deployment"
        assert deployment.last_modified == "2023-01-01T00:00:00Z"
        assert deployment.kind == "Deployment"
        assert len(deployment.links) == 1
        assert deployment.api_client == self.api_client
        assert deployment.config == self.workload_config

    @patch.object(Deployment, "__post_init__", return_value=None)
    def test_post_init(self, mock_post_init):
        # Test that post_init is called during deployment creation
        status_mock = Mock()
        status_mock.remote = "https://remote.example.com"

        Deployment(
            name="test",
            status=status_mock,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        # Verify that __post_init__ was called
        mock_post_init.assert_called_once()

    @patch.object(Deployment, "__post_init__", return_value=None)
    def test_export(self, mock_post_init):
        # Create a real Status object instead of a mock for proper to_dict behavior
        status_data = {
            "endpoint": "https://example.com",
            "remote": "https://remote.example.com",
            "lastProcessedVersion": "v1",
            "expectedDeploymentVersion": "v1",
            "message": "Ready",
            "ready": True,
            "internal": {
                "podStatus": {"phase": "Running"},
                "podsValidZone": True,
                "timestamp": "2023-01-01T00:00:00Z",
                "ksvcStatus": {"ready": True},
            },
            "versions": [],
        }
        status = Status.parse(status_data)

        deployment = Deployment(
            name="test-deployment",
            status=status,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        result = deployment.export()

        # The export method should return the status as a dictionary via to_dict()
        assert result["name"] == "test-deployment"
        assert result["last_modified"] == "2023-01-01T00:00:00Z"
        assert result["kind"] == "Deployment"
        assert isinstance(result["status"], dict)
        assert result["status"]["ready"] is True

    @patch.object(Deployment, "__post_init__", return_value=None)
    def test_get_remote_deployment(self, mock_post_init):
        self.api_client._get.return_value = {"items": []}

        deployment = Deployment(
            name="test",
            status=Mock(),
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        result = deployment.get_remote_deployment()

        self.api_client._get.assert_called_once_with(
            "/gvc/test-gvc/workload/test-workload"
        )
        assert result == {"items": []}

    @patch.object(Deployment, "__post_init__", return_value=None)
    def test_get_remote_wss(self, mock_post_init):
        status_mock = Mock()
        status_mock.remote = "https://remote.example.com"

        deployment = Deployment(
            name="test",
            status=status_mock,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        result = deployment.get_remote_wss()
        assert result == "wss://remote.example.com/remote"

    @patch.object(Deployment, "__post_init__", return_value=None)
    def test_get_remote(self, mock_post_init):
        status_mock = Mock()
        status_mock.remote = "https://remote.example.com"

        deployment = Deployment(
            name="test",
            status=status_mock,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        result = deployment.get_remote()
        assert result == "https://remote.example.com"

    @patch.object(Deployment, "__post_init__", return_value=None)
    def test_get_containers(self, mock_post_init):
        version1 = Mock()
        container1 = Mock()
        container1.name = "container1"
        container2 = Mock()
        container2.name = "container2"
        version1.containers = [container1, container2]

        status_mock = Mock()
        status_mock.versions = [version1]

        deployment = Deployment(
            name="test",
            status=status_mock,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        result = deployment.get_containers()
        expected = {"container1": container1, "container2": container2}
        assert result == expected

    def test_get_replicas(self):
        """Test get_replicas method which was missing coverage."""
        # Create a real deployment without mocking __post_init__
        # to ensure line 382 (the return statement) gets coverage

        # Mock the required methods
        status_mock = Mock()
        status_mock.remote = "https://remote.example.com"

        deployment = Deployment(
            name="test",
            status=status_mock,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        # Mock the helper methods
        deployment.get_remote_deployment = Mock(
            return_value={"items": ["replica1", "replica2"]}
        )
        deployment.get_containers = Mock(
            return_value={"container1": Mock(), "container2": Mock()}
        )
        deployment.get_remote_wss = Mock(return_value="wss://remote.example.com/remote")

        # Call get_replicas to cover line 382
        with patch("cpln.parsers.deployment.WorkloadReplica.parse") as mock_parse:
            mock_parse.return_value = Mock()
            result = deployment.get_replicas()

            # Verify the structure is correct
            assert isinstance(result, dict)
            assert "container1" in result
            assert "container2" in result

    def test_real_post_init_coverage(self):
        """Test the actual __post_init__ method without mocking to ensure line 346 is covered."""
        status_mock = Mock()
        status_mock.remote = "https://remote.example.com"

        # Create deployment normally (without mocking __post_init__)
        # This will execute the real __post_init__ method and cover line 346
        deployment = Deployment(
            name="test",
            status=status_mock,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        # Verify deployment was created successfully
        assert deployment.name == "test"
        assert deployment.api_client == self.api_client
        assert deployment.config == self.workload_config
