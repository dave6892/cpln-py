import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

from cpln.config import WorkloadConfig
from cpln.errors import WebSocketExitCodeError
from cpln.models.workloads import Workload, WorkloadCollection
from requests import Response


class TestWorkload(unittest.TestCase):
    def setUp(self) -> None:
        self.attrs: Dict[str, Any] = {
            "id": "test-workload-id",  # Add id to prevent NoneType error in short_id
            "name": "test-workload",
            "spec": {
                "defaultOptions": {
                    "suspend": "false",
                    "autoscaling": {  # Add autoscaling for clone tests
                        "metric": "memory"
                    },
                    "capacityAI": True,
                },
                "type": "standard",  # Add type for clone tests
            },
        }
        self.client = MagicMock()
        self.collection = MagicMock()
        self.state = {"gvc": "test-gvc"}
        self.workload = Workload(
            attrs=self.attrs,
            client=self.client,
            collection=self.collection,
            state=self.state,
        )

    def test_get(self) -> None:
        """Test get method"""
        expected_response: Dict[str, Any] = {"name": "test-workload"}
        self.client.api.get_workload.return_value = expected_response
        result = self.workload.get()
        self.assertEqual(result, expected_response)
        self.client.api.get_workload.assert_called_once_with(self.workload.config())

    def test_delete(self) -> None:
        """Test delete method"""
        self.workload.delete()
        self.client.api.delete_workload.assert_called_once_with(self.workload.config())

    def test_suspend(self) -> None:
        """Test suspend method"""
        self.workload.suspend()
        self.client.api.patch_workload.assert_called_once_with(
            config=self.workload.config(),
            data={"spec": {"defaultOptions": {"suspend": "true"}}},
        )

    def test_unsuspend(self) -> None:
        """Test unsuspend method"""
        self.workload.unsuspend()
        self.client.api.patch_workload.assert_called_once_with(
            config=self.workload.config(),
            data={"spec": {"defaultOptions": {"suspend": "false"}}},
        )

    def test_exec_success(self) -> None:
        """Test exec method with success"""
        command = "echo test"
        location = "test-location"
        expected_response = {"output": "test"}
        self.client.api.exec_workload.return_value = expected_response
        result = self.workload.exec(command, location)
        self.assertEqual(result, expected_response)
        self.client.api.exec_workload.assert_called_once_with(
            config=self.workload.config(location=location), command=command
        )

    def test_exec_error(self) -> None:
        """Test exec method with error"""
        command = "invalid-command"
        location = "test-location"
        error = WebSocketExitCodeError("Command failed")
        error.exit_code = 1
        self.client.api.exec_workload.side_effect = error
        with self.assertRaises(WebSocketExitCodeError):
            self.workload.exec(command, location)

    def test_ping_success(self) -> None:
        """Test ping method with success"""
        location = "test-location"
        expected_response = {"output": "ping"}
        self.client.api.exec_workload.return_value = expected_response
        result = self.workload.ping(location)
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["message"], "Successfully pinged workload")
        self.assertEqual(result["exit_code"], 0)

    def test_ping_error(self) -> None:
        """Test ping method with error"""
        location = "test-location"
        error = WebSocketExitCodeError("Command failed")
        error.exit_code = 1
        self.client.api.exec_workload.side_effect = error
        result = self.workload.ping(location)
        self.assertEqual(result["status"], 500)
        self.assertIn("Command failed with exit code", result["message"])
        self.assertEqual(result["exit_code"], 1)

    def test_ping_general_exception(self) -> None:
        """Test ping method with a general exception"""
        location = "test-location"
        self.client.api.exec_workload.side_effect = Exception("Connection failed")
        result = self.workload.ping(location)
        self.assertEqual(result["status"], 500)
        self.assertEqual(result["message"], "Connection failed")
        self.assertEqual(result["exit_code"], -1)

    def test_config(self) -> None:
        """Test config method"""
        location = "test-location"
        config = self.workload.config(location)
        self.assertIsInstance(config, WorkloadConfig)
        self.assertEqual(config.gvc, self.state["gvc"])
        self.assertEqual(config.workload_id, self.attrs["name"])
        self.assertEqual(config.location, location)

    def test_get_remote(self) -> None:
        """Test get_remote method"""
        location = "test-location"
        expected_remote = "wss://test-remote"
        self.client.api.get_remote.return_value = expected_remote
        result = self.workload.get_remote(location)
        self.assertEqual(result, expected_remote)
        self.client.api.get_remote.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_get_remote_wss(self) -> None:
        """Test get_remote_wss method"""
        location = "test-location"
        expected_remote = "wss://test-remote"
        self.client.api.get_remote_wss.return_value = expected_remote
        result = self.workload.get_remote_wss(location)
        self.assertEqual(result, expected_remote)
        self.client.api.get_remote_wss.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_get_replicas(self) -> None:
        """Test get_replicas method"""
        location = "test-location"
        expected_replicas = ["replica1", "replica2"]
        self.client.api.get_replicas.return_value = expected_replicas
        result = self.workload.get_replicas(location)
        self.assertEqual(result, expected_replicas)
        self.client.api.get_replicas.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_get_containers(self) -> None:
        """Test get_containers method"""
        location = "test-location"
        expected_containers = ["container1", "container2"]
        self.client.api.get_containers.return_value = expected_containers
        result = self.workload.get_containers(location)
        self.assertEqual(result, expected_containers)
        self.client.api.get_containers.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_clone_success(self) -> None:
        """Test clone method with success"""
        new_name = "cloned-workload"
        new_gvc = "new-gvc"
        new_workload_type = "serverless"

        # Mock the export method to return metadata
        self.workload.export = MagicMock()
        self.workload.export.return_value = {
            "name": self.attrs["name"],
            "gvc": self.state["gvc"],
            "spec": self.attrs["spec"],
        }

        # Mock the API response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "Created"
        self.client.api.create_workload.return_value = mock_response

        # Call the clone method
        self.workload.clone(name=new_name, gvc=new_gvc, workload_type=new_workload_type)

        # Verify the API was called with the correct parameters
        self.client.api.create_workload.assert_called_once()
        args, kwargs = self.client.api.create_workload.call_args

        # Check that the config parameter was passed correctly
        self.assertEqual(kwargs["config"].gvc, new_gvc)

        # Check that the metadata was updated correctly
        metadata = kwargs["metadata"]
        self.assertEqual(metadata["name"], new_name)
        self.assertEqual(metadata["gvc"], new_gvc)
        self.assertEqual(metadata["spec"]["type"], new_workload_type)

    def test_clone_error(self) -> None:
        """Test clone method with error response"""
        new_name = "cloned-workload"

        # Mock the export method to return metadata
        self.workload.export = MagicMock()
        self.workload.export.return_value = {
            "name": self.attrs["name"],
            "gvc": self.state["gvc"],
            "spec": self.attrs["spec"],
        }

        # Mock the API response for an error
        mock_response = Mock(spec=Response)
        mock_response.status_code = 400
        mock_response.json = MagicMock(return_value={"error": "Bad request"})
        self.client.api.create_workload.return_value = mock_response

        # Call the clone method and expect an exception
        with self.assertRaises((RuntimeError, ValueError)):
            self.workload.clone(name=new_name)


class TestWorkloadCollection(unittest.TestCase):
    def setUp(self) -> None:
        self.client = MagicMock()
        self.collection = WorkloadCollection(client=self.client)

    def test_get(self) -> None:
        """Test get method"""
        config = WorkloadConfig(gvc="test-gvc", workload_id="test-workload")
        expected_workload = {"name": "test-workload"}
        self.client.api.get_workload.return_value = expected_workload
        result = self.collection.get(config)
        self.assertIsInstance(result, Workload)
        self.assertEqual(result.attrs, expected_workload)
        self.assertEqual(result.state["gvc"], config.gvc)
        self.client.api.get_workload.assert_called_once_with(config=config)

    def test_list_with_gvc(self) -> None:
        """Test list method with GVC"""
        gvc = "test-gvc"
        config = WorkloadConfig(gvc=gvc)
        response = {"items": [{"name": "workload1"}, {"name": "workload2"}]}

        # Set up the get_workload method to return different values for different calls
        self.client.api.get_workload = MagicMock()
        self.client.api.get_workload.side_effect = [
            response,  # First call returns the list
            {"name": "workload1"},  # Second call returns workload1
            {"name": "workload2"},  # Third call returns workload2
        ]

        result = self.collection.list(gvc=gvc)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn("workload1", result)
        self.assertIn("workload2", result)

        # Verify get_workload was called at least once
        self.assertTrue(self.client.api.get_workload.called)

        # Check the calls were made with the expected configs
        calls = self.client.api.get_workload.call_args_list
        self.assertEqual(len(calls), 3)  # Should be 3 calls total

        # Verify the first call (main list call)
        first_call = calls[0]
        # The call might be using positional or keyword args, so we'll check both
        if len(first_call.args) > 0:
            # If using positional args
            self.assertEqual(first_call.args[0], config)
        else:
            # If using keyword args
            self.assertEqual(first_call.kwargs.get("config"), config)

    def test_list_with_config(self) -> None:
        """Test list method with config"""
        config = WorkloadConfig(gvc="test-gvc")
        response = {"items": [{"name": "workload1"}, {"name": "workload2"}]}

        # Set up the get_workload method to return different values for different calls
        self.client.api.get_workload = MagicMock()
        self.client.api.get_workload.side_effect = [
            response,  # First call returns the list
            {"name": "workload1"},  # Second call returns workload1
            {"name": "workload2"},  # Third call returns workload2
        ]

        result = self.collection.list(config=config)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn("workload1", result)
        self.assertIn("workload2", result)

        # Verify get_workload was called at least once
        self.assertTrue(self.client.api.get_workload.called)

        # Check the calls were made with the expected configs
        calls = self.client.api.get_workload.call_args_list
        self.assertEqual(len(calls), 3)  # Should be 3 calls total

        # Verify the first call (main list call)
        first_call = calls[0]
        # The call might be using positional or keyword args, so we'll check both
        if len(first_call.args) > 0:
            # If using positional args
            self.assertEqual(first_call.args[0], config)
        else:
            # If using keyword args
            self.assertEqual(first_call.kwargs.get("config"), config)

        # Optionally, verify subsequent calls for individual workloads
        second_call = calls[1]
        third_call = calls[2]

        # Verify these calls have workload_id set
        workload1_config = None
        workload2_config = None

        if len(second_call.args) > 0:
            workload1_config = second_call.args[0]
        else:
            workload1_config = second_call.kwargs.get("config")

        if len(third_call.args) > 0:
            workload2_config = third_call.args[0]
        else:
            workload2_config = third_call.kwargs.get("config")

        self.assertEqual(workload1_config.gvc, config.gvc)
        self.assertEqual(workload2_config.gvc, config.gvc)

    def test_list_no_args(self) -> None:
        """Test list method with no arguments"""
        with self.assertRaises(ValueError):
            self.collection.list()

    def test_create_success(self) -> None:
        """Test create method with success"""
        name = "test-workload"
        gvc = "test-gvc"
        image = "test-image"
        container_name = "test-container"
        description = "Test workload"

        # Mock the API response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "Created"
        self.client.api.create_workload.return_value = mock_response

        # Mock the template function
        with patch(
            "cpln.models.workloads.get_default_workload_template"
        ) as mock_template:
            mock_template.return_value = {
                "name": "",
                "description": "",
                "spec": {
                    "containers": [{"name": "", "image": ""}],
                    "defaultOptions": {
                        "autoscaling": {"metric": ""},
                        "capacityAI": True,
                    },
                },
            }

            # Call the create method
            self.collection.create(
                name=name,
                gvc=gvc,
                description=description,
                image=image,
                container_name=container_name,
            )

            # Verify the API was called with the correct parameters
            self.client.api.create_workload.assert_called_once()
            config_arg, metadata_arg = self.client.api.create_workload.call_args[0]

            # Check config
            self.assertEqual(config_arg.gvc, gvc)

            # Check metadata
            self.assertEqual(metadata_arg["name"], name)
            self.assertEqual(metadata_arg["description"], description)
            self.assertEqual(metadata_arg["spec"]["containers"][0]["image"], image)
            self.assertEqual(
                metadata_arg["spec"]["containers"][0]["name"], container_name
            )

    def test_create_missing_required_params(self) -> None:
        """Test create method with missing required parameters"""
        name = "test-workload"
        gvc = "test-gvc"

        # No image provided
        with self.assertRaises(ValueError):
            self.collection.create(name=name, gvc=gvc, container_name="test-container")

        # No container_name provided
        with self.assertRaises(ValueError):
            self.collection.create(name=name, gvc=gvc, image="test-image")

        # No gvc or config provided
        with self.assertRaises(ValueError):
            self.collection.create(
                name=name, image="test-image", container_name="test-container"
            )

    def test_create_with_metadata_file(self) -> None:
        """Test create method with metadata file"""
        name = "test-workload"
        gvc = "test-gvc"
        metadata_file_path = "/path/to/metadata.json"

        # Mock the API response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "Created"
        self.client.api.create_workload.return_value = mock_response

        # Mock the load_template function
        with patch("cpln.models.workloads.load_template") as mock_load:
            mock_load.return_value = {
                "name": "template-name",
                "description": "Template description",
                "spec": {},
            }

            # Call the create method
            self.collection.create(
                name=name, gvc=gvc, metadata_file_path=metadata_file_path
            )

            # Verify the template was loaded
            mock_load.assert_called_once_with(metadata_file_path)

            # Verify the API was called with the correct parameters
            self.client.api.create_workload.assert_called_once()


if __name__ == "__main__":
    unittest.main()
