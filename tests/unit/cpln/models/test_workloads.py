import unittest
from typing import Any, Dict, List, Tuple, cast
from unittest.mock import MagicMock, Mock, patch

from cpln.config import WorkloadConfig
from cpln.errors import WebSocketExitCodeError
from cpln.models.workloads import Workload, WorkloadCollection
from requests import Response


class TestWorkload(unittest.TestCase):
    """Tests for the Workload class"""

    def setUp(self) -> None:
        """Set up the test"""
        self.attrs: Dict[str, Any] = {
            "id": "test-workload-id",
            "name": "test-workload",
            "description": "Test workload description",
            "spec": {
                "containers": [{"name": "app", "image": "nginx:latest"}],
                "defaultOptions": {
                    "suspend": "false",
                    "autoscaling": {
                        "metric": "memory",
                        "minReplicas": 1,
                        "maxReplicas": 5,
                    },
                    "capacityAI": True,
                },
                "type": "standard",
            },
        }
        self.client: MagicMock = MagicMock()
        self.collection: MagicMock = MagicMock()
        self.state: Dict[str, str] = {"gvc": "test-gvc"}
        self.workload = Workload(
            attrs=self.attrs,
            client=self.client,
            collection=self.collection,
            state=self.state,
        )

    def test_initialization(self) -> None:
        """Test workload initialization"""
        self.assertEqual(self.workload.attrs, self.attrs)
        self.assertEqual(self.workload.client, self.client)
        self.assertEqual(self.workload.collection, self.collection)
        self.assertEqual(self.workload.state, self.state)
        # The string representation includes the class name and workload name
        self.assertTrue("Workload" in str(self.workload))
        self.assertTrue("test-workload" in str(self.workload))

    def test_get(self) -> None:
        """Test get method"""
        expected_response: Dict[str, Any] = {"name": "test-workload", "updated": True}
        self.client.api.get_workload.return_value = expected_response

        result = self.workload.get()

        self.assertEqual(result, expected_response)
        self.client.api.get_workload.assert_called_once_with(self.workload.config())

    def test_delete(self) -> None:
        """Test delete method"""
        # Mock print to avoid output during test
        with patch("builtins.print"):
            self.workload.delete()

        self.client.api.delete_workload.assert_called_once_with(self.workload.config())

    def test_suspend(self) -> None:
        """Test suspend method"""
        # Mock print to avoid output during test
        with patch("builtins.print"):
            self.workload.suspend()

        self.client.api.patch_workload.assert_called_once_with(
            config=self.workload.config(),
            data={"spec": {"defaultOptions": {"suspend": "true"}}},
        )

    def test_unsuspend(self) -> None:
        """Test unsuspend method"""
        # Mock print to avoid output during test
        with patch("builtins.print"):
            self.workload.unsuspend()

        self.client.api.patch_workload.assert_called_once_with(
            config=self.workload.config(),
            data={"spec": {"defaultOptions": {"suspend": "false"}}},
        )

    def test_exec_success(self) -> None:
        """Test exec method with success"""
        command: str = "echo 'Hello, World!'"
        location: str = "test-location"
        expected_response: Dict[str, str] = {"output": "Hello, World!"}
        self.client.api.exec_workload.return_value = expected_response

        result = self.workload.exec(command, location)

        self.assertEqual(result, expected_response)
        self.client.api.exec_workload.assert_called_once_with(
            config=self.workload.config(location=location), command=command
        )

    def test_exec_error(self) -> None:
        """Test exec method with error"""
        command: str = "invalid-command"
        location: str = "test-location"

        # Create a WebSocketExitCodeError with exit_code
        error = WebSocketExitCodeError("Command failed")
        error.exit_code = 1

        self.client.api.exec_workload.side_effect = error

        # Mock print to avoid output during test
        with (
            patch("builtins.print"),
            self.assertRaises(WebSocketExitCodeError),
        ):
            self.workload.exec(command, location)

        self.client.api.exec_workload.assert_called_once_with(
            config=self.workload.config(location=location), command=command
        )

    def test_ping_success(self) -> None:
        """Test ping method with success"""
        location: str = "test-location"
        self.client.api.exec_workload.return_value = {"output": "ping"}

        result = self.workload.ping(location)

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["message"], "Successfully pinged workload")
        self.assertEqual(result["exit_code"], 0)
        self.client.api.exec_workload.assert_called_once()

    def test_ping_websocket_error(self) -> None:
        """Test ping method with WebSocketExitCodeError"""
        location: str = "test-location"

        # Create a WebSocketExitCodeError with exit_code
        error = WebSocketExitCodeError("Command failed")
        error.exit_code = 1

        self.client.api.exec_workload.side_effect = error

        result = self.workload.ping(location)

        self.assertEqual(result["status"], 500)
        self.assertIn("Command failed with exit code", result["message"])
        self.assertEqual(result["exit_code"], 1)

    def test_ping_general_exception(self) -> None:
        """Test ping method with general exception"""
        location: str = "test-location"
        self.client.api.exec_workload.side_effect = Exception("Connection failed")

        result = self.workload.ping(location)

        self.assertEqual(result["status"], 500)
        self.assertEqual(result["message"], "Connection failed")
        self.assertEqual(result["exit_code"], -1)

    def test_export(self) -> None:
        """Test export method"""
        # Mock the get method to avoid API call
        with patch.object(self.workload, "get"):
            result = self.workload.export()

            self.assertEqual(result["name"], self.attrs["name"])
            self.assertEqual(result["gvc"], self.state["gvc"])
            self.assertEqual(result["spec"], self.attrs["spec"])

    def test_config_default(self) -> None:
        """Test config method with default parameters"""
        config = self.workload.config()

        self.assertIsInstance(config, WorkloadConfig)
        self.assertEqual(config.gvc, self.state["gvc"])
        self.assertEqual(config.workload_id, self.attrs["name"])
        self.assertIsNone(config.location)

    def test_config_with_location(self) -> None:
        """Test config method with location parameter"""
        location: str = "test-location"
        config = self.workload.config(location=location)

        self.assertEqual(config.location, location)

    def test_config_with_custom_gvc(self) -> None:
        """Test config method with custom gvc parameter"""
        custom_gvc: str = "custom-gvc"
        config = self.workload.config(gvc=custom_gvc)

        self.assertEqual(config.gvc, custom_gvc)

    def test_get_remote(self) -> None:
        """Test get_remote method"""
        location: str = "test-location"
        expected_remote: str = "https://test-remote"
        self.client.api.get_remote.return_value = expected_remote

        result = self.workload.get_remote(location)

        self.assertEqual(result, expected_remote)
        self.client.api.get_remote.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_get_remote_wss(self) -> None:
        """Test get_remote_wss method"""
        location: str = "test-location"
        expected_remote: str = "wss://test-remote"
        self.client.api.get_remote_wss.return_value = expected_remote

        result = self.workload.get_remote_wss(location)

        self.assertEqual(result, expected_remote)
        self.client.api.get_remote_wss.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_get_replicas(self) -> None:
        """Test get_replicas method"""
        location: str = "test-location"
        expected_replicas: List[str] = ["replica1", "replica2"]
        self.client.api.get_replicas.return_value = expected_replicas

        result = self.workload.get_replicas(location)

        self.assertEqual(result, expected_replicas)
        self.client.api.get_replicas.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_get_containers(self) -> None:
        """Test get_containers method"""
        location: str = "test-location"
        expected_containers: List[str] = ["container1", "container2"]
        self.client.api.get_containers.return_value = expected_containers

        result = self.workload.get_containers(location)

        self.assertEqual(result, expected_containers)
        self.client.api.get_containers.assert_called_once_with(
            self.workload.config(location=location)
        )

    def test_clone_basic(self) -> None:
        """Test clone method with basic parameters"""
        # Setup test data
        new_name: str = "cloned-workload"

        # Mock successful API response
        mock_response: Mock = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "Created"
        self.client.api.create_workload.return_value = mock_response

        # Mock the export method to return the expected data
        with patch.object(self.workload, "export") as mock_export:
            mock_export.return_value = {
                "name": self.attrs["name"],
                "gvc": self.state["gvc"],
                "spec": self.attrs["spec"],
            }

            # Mock print to avoid output during test
            with patch("builtins.print"):
                # Call clone method - should not raise any exceptions
                self.workload.clone(name=new_name)

        # Verify API call
        self.client.api.create_workload.assert_called_once()

        # Check that both arguments are passed as keyword arguments
        args, kwargs = cast(
            Tuple[Tuple[Any, ...], Dict[str, Any]],
            self.client.api.create_workload.call_args,
        )
        self.assertIn("config", kwargs)
        self.assertIn("metadata", kwargs)

        # Check metadata
        metadata = kwargs["metadata"]
        self.assertEqual(metadata["name"], new_name)
        # Original spec should be preserved
        self.assertEqual(metadata["spec"]["type"], self.attrs["spec"]["type"])
        self.assertEqual(
            metadata["spec"]["containers"], self.attrs["spec"]["containers"]
        )

    def test_clone_with_gvc(self) -> None:
        """Test clone method with custom gvc"""
        # Setup test data
        new_name: str = "cloned-workload"
        new_gvc: str = "new-gvc"

        # Mock the export method
        self.workload.export = MagicMock(
            return_value={
                "name": self.attrs["name"],
                "gvc": self.state["gvc"],
                "spec": self.attrs["spec"],
            }
        )

        # Mock successful API response
        mock_response: Mock = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "Created"
        self.client.api.create_workload.return_value = mock_response

        # Mock print to avoid output during test
        with patch("builtins.print"):
            # Call clone method
            self.workload.clone(name=new_name, gvc=new_gvc)

        # Verify API call
        args, kwargs = cast(
            Tuple[Tuple[Any, ...], Dict[str, Any]],
            self.client.api.create_workload.call_args,
        )

        # Check that both arguments are passed as keyword arguments
        self.assertIn("config", kwargs)
        self.assertIn("metadata", kwargs)

        # Check config has new gvc
        self.assertEqual(kwargs["config"].gvc, new_gvc)

        # Check metadata has new gvc
        metadata = kwargs["metadata"]
        self.assertEqual(metadata["gvc"], new_gvc)

    def test_clone_with_type_change(self) -> None:
        """Test clone method with workload type change"""
        # Setup test data
        new_name: str = "cloned-workload"
        new_type: str = "serverless"  # Change from standard to serverless

        # Mock the export method
        self.workload.export = MagicMock(
            return_value={
                "name": self.attrs["name"],
                "gvc": self.state["gvc"],
                "spec": self.attrs["spec"],
            }
        )

        # Mock successful API response
        mock_response: Mock = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "Created"
        self.client.api.create_workload.return_value = mock_response

        # Mock print to avoid output during test
        with patch("builtins.print"):
            # Call clone method
            self.workload.clone(name=new_name, workload_type=new_type)

        # Verify API call
        _, kwargs = cast(
            Tuple[Tuple[Any, ...], Dict[str, Any]],
            self.client.api.create_workload.call_args,
        )

        # Check metadata has new type
        metadata = kwargs["metadata"]
        self.assertEqual(metadata["spec"]["type"], new_type)

        # Check that autoscaling and capacityAI were updated for serverless type
        self.assertEqual(
            metadata["spec"]["defaultOptions"]["autoscaling"]["metric"], "cpu"
        )
        self.assertFalse(metadata["spec"]["defaultOptions"]["capacityAI"])

    def test_clone_error(self) -> None:
        """Test clone method with API error"""
        # Setup test data
        new_name: str = "cloned-workload"

        # Mock the export method
        self.workload.export = MagicMock(
            return_value={
                "name": self.attrs["name"],
                "gvc": self.state["gvc"],
                "spec": self.attrs["spec"],
            }
        )

        # Mock error API response
        mock_response: Mock = Mock(spec=Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.text = "Bad request"
        self.client.api.create_workload.return_value = mock_response

        # Mock print to avoid output during test
        with (
            patch("builtins.print"),
            self.assertRaises((RuntimeError, ValueError)),
        ):
            self.workload.clone(name=new_name)

        # Verify API call was attempted
        self.client.api.create_workload.assert_called_once()


class TestWorkloadCollection(unittest.TestCase):
    """Tests for the WorkloadCollection class"""

    def setUp(self) -> None:
        """Set up the test"""
        self.client: MagicMock = MagicMock()
        self.collection = WorkloadCollection(client=self.client)

    def test_model_attribute(self) -> None:
        """Test the model attribute is set correctly"""
        self.assertEqual(self.collection.model, Workload)

    def test_get_workload(self) -> None:
        """Test get method to retrieve a specific workload"""
        # Setup test data
        config: WorkloadConfig = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload"
        )
        workload_data: Dict[str, Any] = {
            "name": "test-workload",
            "spec": {"type": "standard"},
        }

        # Mock API response
        self.client.api.get_workload.return_value = workload_data

        # Call get method
        result = self.collection.get(config)

        # Verify API call
        self.client.api.get_workload.assert_called_once_with(config=config)

        # Verify result
        self.assertIsInstance(result, Workload)
        self.assertEqual(result.attrs, workload_data)
        self.assertEqual(result.state["gvc"], config.gvc)

    def test_list_with_gvc(self) -> None:
        """Test list method with gvc parameter"""
        # Setup test data
        gvc: str = "test-gvc"
        workloads: List[Dict[str, Any]] = [
            {"name": "workload1", "spec": {"type": "standard"}},
            {"name": "workload2", "spec": {"type": "serverless"}},
        ]

        # Mock API responses
        self.client.api.get_workload.side_effect = [
            {"items": workloads},  # First call returns list
            workloads[0],  # Second call returns workload1
            workloads[1],  # Third call returns workload2
        ]

        # Call list method
        result = self.collection.list(gvc=gvc)

        # Verify result structure
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Verify result contents
        self.assertIsInstance(result[0], Workload)
        self.assertEqual(result[0].attrs, workloads[0])
        self.assertEqual(result[0].state["gvc"], gvc)

        self.assertIsInstance(result[1], Workload)
        self.assertEqual(result[1].attrs, workloads[1])
        self.assertEqual(result[1].state["gvc"], gvc)

        # Verify API calls
        self.assertEqual(self.client.api.get_workload.call_count, 3)

    def test_list_with_config(self) -> None:
        """Test list method with config parameter"""
        # Setup test data
        config: WorkloadConfig = WorkloadConfig(gvc="test-gvc")
        workloads: List[Dict[str, Any]] = [
            {"name": "workload1", "spec": {"type": "standard"}},
            {"name": "workload2", "spec": {"type": "serverless"}},
        ]

        # Mock API responses
        self.client.api.get_workload.side_effect = [
            {"items": workloads},  # First call returns list
            workloads[0],  # Second call returns workload1
            workloads[1],  # Third call returns workload2
        ]

        # Call list method
        result = self.collection.list(config=config)

        # Verify result structure
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Verify API calls
        self.assertEqual(self.client.api.get_workload.call_count, 3)

        # Check first call was with the original config
        first_call = self.client.api.get_workload.call_args_list[0]

        # The config might be passed as a positional or keyword argument
        # Try keyword first
        if "config" in first_call[1]:
            self.assertEqual(first_call[1]["config"], config)
        else:
            # If not a keyword, check if it was passed as a positional argument
            self.assertEqual(first_call[0][0], config)

    def test_list_no_args(self) -> None:
        """Test list method with no arguments"""
        with self.assertRaises(ValueError):
            self.collection.list()

    @patch("cpln.models.workloads.get_default_workload_template")
    def test_create_standard(self, mock_template: Mock) -> None:
        """Test create method with standard workload type"""
        # Setup test data
        name: str = "test-standard-workload"
        gvc: str = "test-gvc"
        description: str = "Standard workload description"
        image: str = "nginx:latest"
        container_name: str = "app"
        workload_type: str = "standard"

        # Mock template
        template: Dict[str, Any] = {
            "name": "",
            "description": "",
            "spec": {
                "containers": [{"name": "", "image": ""}],
                "type": "standard",
                "defaultOptions": {
                    "autoscaling": {"metric": "memory"},
                    "capacityAI": True,
                },
            },
        }
        mock_template.return_value = template

        # Mock successful API response
        mock_response: Mock = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.text = "Created"
        self.client.api.create_workload.return_value = mock_response

        # Mock print to avoid output during test
        with patch("builtins.print"):
            # Call create method
            self.collection.create(
                name=name,
                gvc=gvc,
                description=description,
                image=image,
                container_name=container_name,
                workload_type=workload_type,
            )

        # Verify template was requested
        mock_template.assert_called_once_with(workload_type)

        # Verify API call
        self.client.api.create_workload.assert_called_once()

        # Check that both arguments are being passed
        # They may be passed as positional or keyword arguments
        args, kwargs = cast(
            Tuple[Tuple[Any, ...], Dict[str, Any]],
            self.client.api.create_workload.call_args,
        )

        if args and len(args) >= 1:
            # If passed as positional args
            self.assertEqual(args[0].gvc, gvc)
            if len(args) >= 2:
                metadata = args[1]
            else:
                self.assertIn("metadata", kwargs)
                metadata = kwargs["metadata"]
        else:
            # If passed as keyword args
            self.assertIn("config", kwargs)
            self.assertEqual(kwargs["config"].gvc, gvc)
            self.assertIn("metadata", kwargs)
            metadata = kwargs["metadata"]

        # Verify metadata content
        self.assertEqual(metadata["name"], name)
        self.assertEqual(metadata["description"], description)
        self.assertEqual(metadata["spec"]["containers"][0]["image"], image)
        self.assertEqual(metadata["spec"]["containers"][0]["name"], container_name)

    def test_create_missing_params(self) -> None:
        """Test create method with missing required parameters"""
        # Missing image
        with self.assertRaises(ValueError) as cm:
            self.collection.create(
                name="test-workload", gvc="test-gvc", container_name="app"
            )
        self.assertEqual(str(cm.exception), "Image is required.")

        # Missing container_name
        with self.assertRaises(ValueError) as cm:
            self.collection.create(
                name="test-workload", gvc="test-gvc", image="nginx:latest"
            )
        self.assertEqual(str(cm.exception), "Container name is required.")

        # No gvc or config provided
        with self.assertRaises(ValueError) as cm:
            self.collection.create(
                name="test-workload", image="nginx:latest", container_name="app"
            )
        self.assertEqual(
            str(cm.exception), "Either GVC or WorkloadConfig must be defined."
        )


if __name__ == "__main__":
    unittest.main()
