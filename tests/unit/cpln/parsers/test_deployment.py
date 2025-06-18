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
        # Use Mock for workload config to avoid constructor issues
        self.workload_config = Mock()
        self.workload_config.gvc = "test-gvc"
        self.workload_config.workload_id = "test-workload"

    def test_parse_deployment(self):
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

    def test_post_init(self):
        deployment = Deployment(
            name="test",
            status=Mock(),
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )
        deployment.status.remote = "https://remote.example.com"

        # Mock the post_init method on config
        deployment.__post_init__()

        assert (
            deployment.api_client.config.base_url
            == "https://remote.example.com/replicas/"
        )

    def test_export(self):
        status_mock = Mock()
        status_mock.to_dict.return_value = {"ready": True}

        deployment = Deployment(
            name="test-deployment",
            status=status_mock,
            last_modified="2023-01-01T00:00:00Z",
            kind="Deployment",
            links=[],
            api_client=self.api_client,
            config=self.workload_config,
        )

        result = deployment.export()

        expected = {
            "name": "test-deployment",
            "status": {"ready": True},
            "last_modified": "2023-01-01T00:00:00Z",
            "kind": "Deployment",
        }
        assert result == expected

    def test_get_remote_deployment(self):
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

    def test_get_remote_wss(self):
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

    def test_get_remote(self):
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

    def test_get_containers(self):
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
