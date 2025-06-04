import pytest
from unittest.mock import patch, Mock, MagicMock
from cpln.api.workload import WorkloadApiMixin, WorkloadDeploymentMixin
from cpln.api.config import APIConfig
from cpln.config import WorkloadConfig
from cpln.utils.websocket import WebSocketAPI
from cpln.errors import WebSocketExitCodeError


class TestWorkloadDeploymentMixin:
    """Tests for the WorkloadDeploymentMixin class"""

    def setup_method(self):
        """Set up the test"""
        self.mixin = WorkloadDeploymentMixin()
        self.mixin._get = MagicMock()
        self.mixin.config = MagicMock(spec=APIConfig)
        self.mixin.config.token = "test-token"
        self.mixin.config.org = "test-org"
        self.mixin.config.asdict.return_value = {
            "base_url": "https://api.cpln.io",
            "token": "test-token",
            "org": "test-org"
        }

        self.config = WorkloadConfig(
            gvc='test-gvc',
            workload_id='test-workload',
            location='test-location'
        )

    def test_get_workload_deployment(self):
        """Test get_workload_deployment method"""
        deployment_data = {
            "status": {
                "remote": "https://test-remote",
                "versions": [
                    {
                        "containers": {
                            "container1": {},
                            "container2": {}
                        }
                    }
                ]
            }
        }
        self.mixin._get.return_value = deployment_data
        result = self.mixin.get_workload_deployment(self.config)

        self.mixin._get.assert_called_once_with('gvc/test-gvc/workload/test-workload/deployment/test-location')
        assert result == deployment_data

    def test_get_workload_deployment_invalid_config(self):
        """Test get_workload_deployment with invalid config"""
        invalid_config = WorkloadConfig(gvc='test-gvc', workload_id=None)

        with pytest.raises(ValueError, match="Config not set properly"):
            self.mixin.get_workload_deployment(invalid_config)

    @patch.object(WorkloadDeploymentMixin, '__new__')
    def test_get_remote_api(self, mock_new):
        """Test get_remote_api method"""
        api_config = APIConfig(base_url="https://api.cpln.io", org="test-org", token="test-token")

        # Mock instance returned by __new__
        mock_instance = MagicMock()
        mock_instance.get_remote.return_value = "https://test-remote"
        mock_new.return_value = mock_instance

        # Call get_remote_api
        result = WorkloadDeploymentMixin.get_remote_api(api_config, self.config)

        # Verify the instance was created with the right args
        mock_new.assert_called()
        # Verify get_remote was called
        mock_instance.get_remote.assert_called_once_with(self.config)
        # The result should be the mock_instance
        assert result is mock_instance

    def test_get_remote(self):
        """Test get_remote method"""
        deployment_data = {
            "status": {
                "remote": "https://test-remote"
            }
        }
        self.mixin.get_workload_deployment = MagicMock(return_value=deployment_data)

        result = self.mixin.get_remote(self.config)

        self.mixin.get_workload_deployment.assert_called_once_with(self.config)
        assert result == "https://test-remote"

    def test_get_remote_wss(self):
        """Test get_remote_wss method"""
        self.mixin.get_remote = MagicMock(return_value="https://test-remote")

        result = self.mixin.get_remote_wss(self.config)

        self.mixin.get_remote.assert_called_once_with(self.config)
        assert result == "wss://test-remote/remote"

    def test_get_replicas(self):
        """Test get_replicas method"""
        # Mock the remote API client
        mock_remote_api = MagicMock()
        mock_remote_api._get.return_value = {"items": ["replica1", "replica2"]}
        self.mixin.get_remote_api = MagicMock(return_value=mock_remote_api)

        result = self.mixin.get_replicas(self.config)

        self.mixin.get_remote_api.assert_called_once_with(self.mixin.config, self.config)
        mock_remote_api._get.assert_called_once_with("/gvc/test-gvc/workload/test-workload")
        assert result == ["replica1", "replica2"]

    def test_get_containers(self):
        """Test get_containers method"""
        deployment_data = {
            "status": {
                "versions": [
                    {
                        "containers": {
                            "container1": {},
                            "container2": {},
                            "cpln-mounter": {}  # This should be ignored
                        }
                    }
                ]
            }
        }
        self.mixin.get_workload_deployment = MagicMock(return_value=deployment_data)

        result = self.mixin.get_containers(self.config)

        self.mixin.get_workload_deployment.assert_called_once_with(self.config)
        assert sorted(result) == ["container1", "container2"]
        assert "cpln-mounter" not in result


class TestWorkloadApiMixin:
    """Tests for the WorkloadApiMixin class"""

    def setup_method(self):
        """Set up the test"""
        self.mixin = WorkloadApiMixin()
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

        self.config = WorkloadConfig(
            gvc='test-gvc',
            workload_id='test-workload',
            location='test-location'
        )

    def test_get_workload_with_id(self):
        """Test get_workload method with workload ID"""
        self.mixin._get.return_value = {"name": "test-workload"}

        result = self.mixin.get_workload(self.config)

        self.mixin._get.assert_called_once_with('gvc/test-gvc/workload/test-workload')
        assert result == {"name": "test-workload"}

    def test_get_workload_without_id(self):
        """Test get_workload method without workload ID"""
        config = WorkloadConfig(gvc='test-gvc')
        self.mixin._get.return_value = {"items": [{"name": "workload1"}, {"name": "workload2"}]}

        result = self.mixin.get_workload(config)

        self.mixin._get.assert_called_once_with('gvc/test-gvc/workload')
        assert result == {"items": [{"name": "workload1"}, {"name": "workload2"}]}

    def test_create_workload(self):
        """Test create_workload method"""
        metadata = {"name": "new-workload", "description": "Test workload"}
        mock_response = Mock()
        self.mixin._post.return_value = mock_response

        result = self.mixin.create_workload(self.config, metadata)

        self.mixin._post.assert_called_once_with('gvc/test-gvc/workload', data=metadata)
        assert result == mock_response

    def test_delete_workload(self):
        """Test delete_workload method"""
        mock_response = Mock()
        self.mixin._delete.return_value = mock_response

        result = self.mixin.delete_workload(self.config)

        self.mixin._delete.assert_called_once_with('gvc/test-gvc/workload/test-workload')
        assert result == mock_response

    def test_patch_workload(self):
        """Test patch_workload method"""
        data = {"spec": {"defaultOptions": {"suspend": "true"}}}
        mock_response = Mock()
        self.mixin._patch.return_value = mock_response

        result = self.mixin.patch_workload(self.config, data)

        self.mixin._patch.assert_called_once_with('gvc/test-gvc/workload/test-workload', data=data)
        assert result == mock_response

    @patch('cpln.api.workload.WebSocketAPI')
    def test_exec_workload(self, mock_websocket_api):
        """Test exec_workload method"""
        command = "echo 'Hello, World!'"
        mock_instance = Mock()
        mock_websocket_api.return_value = mock_instance
        mock_instance.exec.return_value = {"output": "Hello, World!"}

        result = self.mixin.exec_workload(self.config, command)

        # Verify we get the containers, replicas, and remote URL
        self.mixin.get_containers.assert_called_once_with(self.config)
        self.mixin.get_replicas.assert_called_once_with(self.config)
        self.mixin.get_remote_wss.assert_called_once_with(self.config)

        # Verify we create the WebSocketAPI and call exec
        mock_websocket_api.assert_called_once_with("wss://test-remote")
        mock_instance.exec.assert_called_once_with(
            token="test-token",
            org="test-org",
            gvc="test-gvc",
            container="container1",
            pod="replica1",
            command=["echo", "'Hello,", "World!'"]
        )
        assert result == {"output": "Hello, World!"}
