"""Tests for Workload models following unit testing best practices."""

import unittest
from unittest.mock import MagicMock, call, patch

from cpln.config import WorkloadConfig
from cpln.errors import WebSocketExitCodeError
from cpln.models.workloads import Workload, WorkloadCollection
from cpln.parsers.container import Container
from cpln.parsers.deployment import Deployment
from cpln.parsers.spec import Spec


class TestWorkloadInitialization(unittest.TestCase):
    """Test Workload model initialization and basic properties"""

    def setUp(self):
        """Set up common test fixtures"""
        self.basic_attrs = {
            "id": "wl-123456",
            "name": "test-workload",
            "description": "Test workload description",
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

    def test_workload_initialization_with_all_parameters_sets_attributes_correctly(
        self,
    ):
        """Test that Workload initializes correctly with all parameters"""
        # Arrange
        test_client = MagicMock()
        test_collection = MagicMock()
        test_state = {"deployment": "active"}

        # Act
        workload = Workload(
            attrs=self.basic_attrs,
            client=test_client,
            collection=test_collection,
            state=test_state,
        )

        # Assert
        self.assertEqual(workload.attrs, self.basic_attrs)
        self.assertEqual(workload.client, test_client)
        self.assertEqual(workload.collection, test_collection)
        self.assertEqual(workload.state, test_state)

    def test_workload_initialization_with_minimal_parameters_uses_defaults(self):
        """Test that Workload initializes correctly with minimal parameters"""
        # Act
        workload = Workload()

        # Assert
        self.assertEqual(workload.attrs, {})
        self.assertIsNone(workload.client)
        self.assertIsNone(workload.collection)
        self.assertEqual(workload.state, {})

    def test_workload_inherits_model_properties_correctly(self):
        """Test that Workload inherits Model base class properties"""
        # Arrange
        workload = Workload(attrs=self.basic_attrs)

        # Act & Assert
        self.assertEqual(workload.id, "wl-123456")
        self.assertEqual(workload.name, "test-workload")
        self.assertEqual(workload.short_id, "wl-123456")  # Less than 12 chars
        self.assertEqual(workload.label, "test-workload")


class TestWorkloadBasicOperations(unittest.TestCase):
    """Test basic Workload CRUD operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "api-workload",
            "id": "wl-api-789",
            "spec": {
                "containers": [
                    {
                        "name": "web",
                        "image": "nginx:alpine",
                        "cpu": "100m",
                        "memory": 128,
                    }
                ],
                "type": "serverless",
            },
        }
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.workload = Workload(
            attrs=self.test_attrs,
            client=self.mock_client,
            collection=self.mock_collection,
        )

    def test_get_operation_calls_client_api_with_workload_config(self):
        """Test that get() calls the client API with correct workload configuration"""
        # Arrange
        expected_response = {"name": "api-workload", "status": "active"}
        self.mock_client.api.get_workload.return_value = expected_response

        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            result = self.workload.get()

            # Assert
            self.assertEqual(result, expected_response)
            mock_config.assert_called_once_with()
            self.mock_client.api.get_workload.assert_called_once_with(
                mock_config.return_value
            )

    @patch("builtins.print")
    def test_delete_operation_calls_client_api_and_prints_messages(self, mock_print):
        """Test that delete() calls client API and prints appropriate messages"""
        # Arrange
        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            self.workload.delete()

            # Assert
            mock_config.assert_called_once_with()
            self.mock_client.api.delete_workload.assert_called_once_with(
                mock_config.return_value
            )
            # Verify print statements were called
            expected_calls = [
                call(f"Deleting Workload: {self.workload}"),
                call("Deleted!"),
            ]
            mock_print.assert_has_calls(expected_calls)

    def test_config_method_returns_workload_config_instance(self):
        """Test that config() method returns properly configured WorkloadConfig"""
        # Act
        result = self.workload.config()

        # Assert
        self.assertIsInstance(result, WorkloadConfig)
        # Verify config was created with correct workload name
        self.assertEqual(result.workload_id, "api-workload")

    def test_config_method_with_location_parameter_includes_location(self):
        """Test that config() method includes location when provided"""
        # Act
        result = self.workload.config(location="us-west-2")

        # Assert
        self.assertIsInstance(result, WorkloadConfig)
        self.assertEqual(result.workload_id, "api-workload")
        self.assertEqual(result.location, "us-west-2")


class TestWorkloadSpecAndDeploymentOperations(unittest.TestCase):
    """Test Workload spec and deployment-related operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "spec-workload",
            "spec": {
                "containers": [
                    {
                        "name": "web",
                        "image": "nginx:latest",
                        "cpu": "500m",
                        "memory": 512,
                    }
                ],
                "type": "standard",
                "defaultOptions": {"suspend": False},
            },
        }
        self.mock_client = MagicMock()
        self.workload = Workload(attrs=self.test_attrs, client=self.mock_client)

    @patch("cpln.models.workloads.Spec.parse")
    def test_get_spec_returns_parsed_spec_object(self, mock_spec_parse):
        """Test that get_spec() returns parsed Spec object from attrs"""
        # Arrange
        mock_spec = MagicMock(spec=Spec)
        mock_spec_parse.return_value = mock_spec

        # Act
        result = self.workload.get_spec()

        # Assert
        self.assertEqual(result, mock_spec)
        mock_spec_parse.assert_called_once_with(self.test_attrs["spec"])

    @patch("cpln.models.workloads.Deployment.parse")
    def test_get_deployment_returns_parsed_deployment_object(
        self, mock_deployment_parse
    ):
        """Test that get_deployment() returns parsed Deployment object"""
        # Arrange
        mock_deployment_data = {"status": "running", "replicas": 3}
        self.mock_client.api.get_workload_deployment.return_value = mock_deployment_data
        mock_deployment = MagicMock(spec=Deployment)
        mock_deployment_parse.return_value = mock_deployment

        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            result = self.workload.get_deployment()

            # Assert
            self.assertEqual(result, mock_deployment)
            mock_config.assert_called_once_with(location=None)
            self.mock_client.api.get_workload_deployment.assert_called_once_with(
                mock_config.return_value
            )
            mock_deployment_parse.assert_called_once_with(
                mock_deployment_data,
                api_client=self.mock_client.api,
                config=mock_config.return_value,
            )

    @patch("cpln.models.workloads.Deployment.parse")
    def test_get_deployment_with_location_parameter_passes_location(
        self, mock_deployment_parse
    ):
        """Test that get_deployment() with location parameter passes location correctly"""
        # Arrange
        test_location = "eu-central-1"
        mock_deployment_data = {"status": "running"}
        self.mock_client.api.get_workload_deployment.return_value = mock_deployment_data
        mock_deployment = MagicMock(spec=Deployment)
        mock_deployment_parse.return_value = mock_deployment

        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            result = self.workload.get_deployment(location=test_location)

            # Assert
            self.assertEqual(result, mock_deployment)
            mock_config.assert_called_once_with(location=test_location)


class TestWorkloadSuspendOperations(unittest.TestCase):
    """Test Workload suspend and unsuspend operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {"name": "suspend-test", "spec": {"type": "standard"}}
        self.mock_client = MagicMock()
        self.workload = Workload(attrs=self.test_attrs, client=self.mock_client)

    def test_suspend_operation_calls_change_suspend_state_with_true(self):
        """Test that suspend() calls internal _change_suspend_state with True"""
        # Arrange
        with patch.object(self.workload, "_change_suspend_state") as mock_change_state:
            # Act
            self.workload.suspend()

            # Assert
            mock_change_state.assert_called_once_with(True)

    def test_unsuspend_operation_calls_change_suspend_state_with_false(self):
        """Test that unsuspend() calls internal _change_suspend_state with False"""
        # Arrange
        with patch.object(self.workload, "_change_suspend_state") as mock_change_state:
            # Act
            self.workload.unsuspend()

            # Assert
            mock_change_state.assert_called_once_with(False)

    @patch("builtins.print")
    def test_change_suspend_state_with_true_updates_workload_to_suspended(
        self, mock_print
    ):
        """Test that _change_suspend_state(True) updates workload to suspended state"""
        # Arrange
        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            self.workload._change_suspend_state(True)

            # Assert
            mock_config.assert_called_once_with()
            self.mock_client.api.update_workload.assert_called_once()
            # Verify the suspend state was set correctly in the update call
            call_args = self.mock_client.api.update_workload.call_args[0]
            update_data = call_args[1]
            self.assertTrue(update_data["spec"]["defaultOptions"]["suspend"])

    @patch("builtins.print")
    def test_change_suspend_state_with_false_updates_workload_to_active(
        self, mock_print
    ):
        """Test that _change_suspend_state(False) updates workload to active state"""
        # Arrange
        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            self.workload._change_suspend_state(False)

            # Assert
            mock_config.assert_called_once_with()
            self.mock_client.api.update_workload.assert_called_once()
            # Verify the suspend state was set correctly in the update call
            call_args = self.mock_client.api.update_workload.call_args[0]
            update_data = call_args[1]
            self.assertFalse(update_data["spec"]["defaultOptions"]["suspend"])


class TestWorkloadContainerOperations(unittest.TestCase):
    """Test Workload container-related operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "container-test",
            "spec": {
                "containers": [
                    {
                        "name": "web",
                        "image": "nginx:latest",
                        "cpu": "200m",
                        "memory": 256,
                    },
                    {
                        "name": "api",
                        "image": "python:3.9",
                        "cpu": "100m",
                        "memory": 128,
                    },
                ]
            },
        }
        self.mock_client = MagicMock()
        self.workload = Workload(attrs=self.test_attrs, client=self.mock_client)

    @patch("cpln.models.workloads.Container")
    def test_get_containers_returns_list_of_container_objects(
        self, mock_container_class
    ):
        """Test that get_containers() returns list of Container objects"""
        # Arrange
        mock_container1 = MagicMock(spec=Container)
        mock_container2 = MagicMock(spec=Container)
        mock_container_class.side_effect = [mock_container1, mock_container2]

        # Act
        result = self.workload.get_containers()

        # Assert
        self.assertEqual(result, [mock_container1, mock_container2])
        self.assertEqual(mock_container_class.call_count, 2)
        # Verify Container was called with correct container specs
        mock_container_class.assert_any_call(
            {"name": "web", "image": "nginx:latest", "cpu": "200m", "memory": 256},
            self.workload,
        )
        mock_container_class.assert_any_call(
            {"name": "api", "image": "python:3.9", "cpu": "100m", "memory": 128},
            self.workload,
        )

    @patch("cpln.models.workloads.Container")
    def test_get_container_returns_specific_container_by_name(
        self, mock_container_class
    ):
        """Test that get_container() returns specific Container by name"""
        # Arrange
        mock_container = MagicMock(spec=Container)
        mock_container_class.return_value = mock_container

        # Act
        result = self.workload.get_container("api")

        # Assert
        self.assertEqual(result, mock_container)
        mock_container_class.assert_called_once_with(
            {"name": "api", "image": "python:3.9", "cpu": "100m", "memory": 128},
            self.workload,
        )

    def test_get_container_with_nonexistent_name_returns_none(self):
        """Test that get_container() returns None for nonexistent container name"""
        # Act
        result = self.workload.get_container("nonexistent")

        # Assert
        self.assertIsNone(result)

    def test_get_replicas_calls_api_with_correct_config(self):
        """Test that get_replicas() calls API with correct configuration"""
        # Arrange
        mock_replicas = ["replica-1", "replica-2", "replica-3"]
        self.mock_client.api.get_workload_replicas.return_value = mock_replicas

        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            result = self.workload.get_replicas()

            # Assert
            self.assertEqual(result, mock_replicas)
            mock_config.assert_called_once_with(location=None)
            self.mock_client.api.get_workload_replicas.assert_called_once_with(
                mock_config.return_value
            )

    def test_get_replicas_with_location_passes_location_parameter(self):
        """Test that get_replicas() with location parameter passes it correctly"""
        # Arrange
        test_location = "asia-pacific-1"
        mock_replicas = ["replica-1"]
        self.mock_client.api.get_workload_replicas.return_value = mock_replicas

        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act
            result = self.workload.get_replicas(location=test_location)

            # Assert
            self.assertEqual(result, mock_replicas)
            mock_config.assert_called_once_with(location=test_location)


class TestWorkloadExecOperations(unittest.TestCase):
    """Test Workload exec and ping operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {"name": "exec-test", "spec": {"type": "standard"}}
        self.mock_client = MagicMock()
        self.workload = Workload(attrs=self.test_attrs, client=self.mock_client)

    @patch("cpln.models.workloads.Deployment")
    def test_exec_operation_calls_deployment_exec_with_correct_parameters(
        self, mock_deployment_class
    ):
        """Test that exec() calls deployment exec with correct parameters"""
        # Arrange
        mock_deployment = MagicMock(spec=Deployment)
        mock_deployment.exec.return_value = {
            "status": "success",
            "output": "command output",
        }

        with patch.object(self.workload, "get_deployment") as mock_get_deployment:
            mock_get_deployment.return_value = mock_deployment

            # Act
            result = self.workload.exec(
                "echo hello", location="us-east-1", container="web"
            )

            # Assert
            self.assertEqual(result, {"status": "success", "output": "command output"})
            mock_get_deployment.assert_called_once_with(location="us-east-1")
            mock_deployment.exec.assert_called_once_with(
                "echo hello",
                container="web",
                location="us-east-1",
                workload="exec-test",
            )

    @patch("cpln.models.workloads.Deployment")
    def test_ping_operation_calls_deployment_ping_with_correct_parameters(
        self, mock_deployment_class
    ):
        """Test that ping() calls deployment ping with correct parameters"""
        # Arrange
        mock_deployment = MagicMock(spec=Deployment)
        mock_deployment.ping.return_value = {"status": "success", "latency": "5ms"}

        with patch.object(self.workload, "get_deployment") as mock_get_deployment:
            mock_get_deployment.return_value = mock_deployment

            # Act
            result = self.workload.ping(location="eu-west-1", container="api")

            # Assert
            self.assertEqual(result, {"status": "success", "latency": "5ms"})
            mock_get_deployment.assert_called_once_with(location="eu-west-1")
            mock_deployment.ping.assert_called_once_with(
                container="api", location="eu-west-1", workload="exec-test"
            )


class TestWorkloadUpdateOperations(unittest.TestCase):
    """Test Workload update operations and validation"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "update-test",
            "spec": {
                "containers": [
                    {
                        "name": "app",
                        "image": "nginx:latest",
                        "cpu": "100m",
                        "memory": 256,
                    }
                ],
                "type": "standard",
            },
        }
        self.mock_client = MagicMock()
        self.workload = Workload(attrs=self.test_attrs, client=self.mock_client)

    def test_validate_cpu_spec_with_valid_cpu_values_passes(self):
        """Test that _validate_cpu_spec accepts valid CPU specifications"""
        # Arrange
        valid_cpu_values = ["100m", "0.5", "1", "2", "500m", "1.5"]

        for cpu_value in valid_cpu_values:
            with self.subTest(cpu_value=cpu_value):
                # Act & Assert - should not raise any exception
                try:
                    self.workload._validate_cpu_spec(cpu_value)
                except ValueError:
                    self.fail(
                        f"_validate_cpu_spec raised ValueError for valid CPU value: {cpu_value}"
                    )

    def test_validate_cpu_spec_with_invalid_cpu_values_raises_value_error(self):
        """Test that _validate_cpu_spec rejects invalid CPU specifications"""
        # Arrange
        invalid_cpu_values = ["invalid", "100", "1.5.5", "-100m", ""]

        for cpu_value in invalid_cpu_values:
            with self.subTest(cpu_value=cpu_value):
                # Act & Assert
                with self.assertRaises(ValueError) as context:
                    self.workload._validate_cpu_spec(cpu_value)

                self.assertIn("Invalid CPU specification", str(context.exception))

    def test_validate_memory_spec_with_valid_memory_values_passes(self):
        """Test that _validate_memory_spec accepts valid memory specifications"""
        # Arrange
        valid_memory_values = [128, 256, 512, 1024, 2048]

        for memory_value in valid_memory_values:
            with self.subTest(memory_value=memory_value):
                # Act & Assert - should not raise any exception
                try:
                    self.workload._validate_memory_spec(str(memory_value))
                except ValueError:
                    self.fail(
                        f"_validate_memory_spec raised ValueError for valid memory value: {memory_value}"
                    )

    def test_validate_memory_spec_with_invalid_memory_values_raises_value_error(self):
        """Test that _validate_memory_spec rejects invalid memory specifications"""
        # Arrange
        invalid_memory_values = ["invalid", "-256", "0", "1.5", ""]

        for memory_value in invalid_memory_values:
            with self.subTest(memory_value=memory_value):
                # Act & Assert
                with self.assertRaises(ValueError) as context:
                    self.workload._validate_memory_spec(memory_value)

                self.assertIn("Invalid memory specification", str(context.exception))

    @patch("builtins.print")
    def test_update_operation_with_valid_parameters_calls_api_correctly(
        self, mock_print
    ):
        """Test that update() with valid parameters calls API correctly"""
        # Arrange
        with patch.object(self.workload, "config") as mock_config, patch.object(
            self.workload, "_validate_cpu_spec"
        ) as mock_validate_cpu, patch.object(
            self.workload, "_validate_memory_spec"
        ) as mock_validate_memory:
            mock_config.return_value = MagicMock()

            # Act
            self.workload.update(image="nginx:1.21", cpu="200m", memory="512")

            # Assert
            mock_validate_cpu.assert_called_once_with("200m")
            mock_validate_memory.assert_called_once_with("512")
            mock_config.assert_called_once_with()
            self.mock_client.api.update_workload.assert_called_once()


class TestWorkloadCloneAndExport(unittest.TestCase):
    """Test Workload clone and export operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {
            "name": "source-workload",
            "spec": {
                "containers": [
                    {
                        "name": "app",
                        "image": "nginx:latest",
                        "cpu": "100m",
                        "memory": 256,
                    }
                ],
                "type": "serverless",
            },
            "metadata": {"description": "Source workload for cloning"},
        }
        self.mock_client = MagicMock()
        self.workload = Workload(attrs=self.test_attrs, client=self.mock_client)

    @patch("cpln.models.workloads.get_default_workload_template")
    def test_clone_operation_creates_new_workload_with_correct_name(
        self, mock_get_template
    ):
        """Test that clone() creates new workload with specified name"""
        # Arrange
        mock_template = {"kind": "workload", "spec": {"type": "serverless"}}
        mock_get_template.return_value = mock_template

        with patch.object(self.workload, "export") as mock_export:
            mock_export.return_value = self.test_attrs

            # Act
            self.workload.clone(name="cloned-workload", gvc="target-gvc")

            # Assert
            self.mock_client.api.create_workload.assert_called_once()
            # Verify the call was made with correct parameters
            call_args = self.mock_client.api.create_workload.call_args[0]
            self.assertIn("cloned-workload", str(call_args))

    def test_export_operation_returns_workload_metadata_copy(self):
        """Test that export() returns a deep copy of workload attributes"""
        # Act
        result = self.workload.export()

        # Assert
        self.assertEqual(result, self.test_attrs)
        # Verify it's a copy, not the same object
        self.assertIsNot(result, self.test_attrs)
        # Verify nested objects are also copied
        self.assertIsNot(result["spec"], self.test_attrs["spec"])


class TestWorkloadCollectionInitialization(unittest.TestCase):
    """Test WorkloadCollection initialization and basic properties"""

    def test_workload_collection_initialization_with_client_sets_client(self):
        """Test that WorkloadCollection initializes correctly with client"""
        # Arrange
        test_client = MagicMock()

        # Act
        collection = WorkloadCollection(client=test_client)

        # Assert
        self.assertEqual(collection.client, test_client)
        self.assertEqual(collection.model, Workload)

    def test_workload_collection_model_attribute_is_workload_class(self):
        """Test that collection.model points to Workload class"""
        # Act
        collection = WorkloadCollection()

        # Assert
        self.assertIs(collection.model, Workload)


class TestWorkloadCollectionOperations(unittest.TestCase):
    """Test WorkloadCollection operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_client = MagicMock()
        self.collection = WorkloadCollection(client=self.mock_client)

    def test_get_operation_returns_workload_instance_with_correct_attributes(self):
        """Test that get() returns Workload instance with data from API"""
        # Arrange
        test_config = WorkloadConfig(gvc="test-gvc", workload_id="test-workload")
        api_response = {
            "name": "test-workload",
            "id": "wl-test-123",
            "spec": {
                "containers": [
                    {
                        "name": "app",
                        "image": "nginx:latest",
                        "cpu": "100m",
                        "memory": 256,
                    }
                ]
            },
            "status": "active",
        }
        self.mock_client.api.get_workload.return_value = api_response

        # Act
        result = self.collection.get(test_config)

        # Assert
        self.assertIsInstance(result, Workload)
        self.assertEqual(result.attrs, api_response)
        self.assertEqual(result.client, self.mock_client)
        self.assertEqual(result.collection, self.collection)

    def test_list_operation_returns_list_of_workload_instances(self):
        """Test that list() returns list of Workload instances from API response"""
        # Arrange
        api_response = {
            "items": [
                {"name": "workload1", "id": "wl-1", "spec": {"type": "standard"}},
                {"name": "workload2", "id": "wl-2", "spec": {"type": "serverless"}},
            ]
        }
        self.mock_client.api.get_workload.return_value = api_response

        # Act
        result = self.collection.list()

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Verify each item is a properly configured Workload instance
        for i, workload in enumerate(result):
            with self.subTest(workload_index=i):
                self.assertIsInstance(workload, Workload)
                self.assertEqual(workload.attrs, api_response["items"][i])
                self.assertEqual(workload.client, self.mock_client)
                self.assertEqual(workload.collection, self.collection)

    def test_create_operation_with_template_creates_workload_correctly(self):
        """Test that create() operation creates workload using template"""
        # Arrange
        workload_config = MagicMock(spec=WorkloadConfig)
        workload_config.workload = "new-workload"
        workload_config.gvc = "test-gvc"

        with patch(
            "cpln.models.workloads.get_default_workload_template"
        ) as mock_get_template:
            mock_template = {"kind": "workload", "spec": {"type": "standard"}}
            mock_get_template.return_value = mock_template

            # Act
            self.collection.create(
                name="new-workload", config=workload_config, workload_type="standard"
            )

            # Assert
            mock_get_template.assert_called_once_with("standard")
            self.mock_client.api.create_workload.assert_called_once()


class TestWorkloadErrorHandling(unittest.TestCase):
    """Test Workload error handling and edge cases"""

    def setUp(self):
        """Set up common test fixtures"""
        self.test_attrs = {"name": "error-test", "spec": {"type": "standard"}}
        self.mock_client = MagicMock()
        self.workload = Workload(attrs=self.test_attrs, client=self.mock_client)

    def test_get_operation_propagates_api_errors(self):
        """Test that get() operation propagates API client errors"""
        # Arrange
        api_error = Exception("Workload API connection failed")
        self.mock_client.api.get_workload.side_effect = api_error

        with patch.object(self.workload, "config") as mock_config:
            mock_config.return_value = MagicMock()

            # Act & Assert
            with self.assertRaises(Exception) as context:
                self.workload.get()

            self.assertEqual(context.exception, api_error)

    def test_get_spec_with_missing_spec_raises_key_error(self):
        """Test that get_spec() raises KeyError when spec is missing"""
        # Arrange
        workload_no_spec = Workload(attrs={"name": "no-spec"})

        # Act & Assert
        with self.assertRaises(KeyError):
            workload_no_spec.get_spec()

    def test_get_container_with_missing_containers_returns_none(self):
        """Test that get_container() returns None when containers are missing"""
        # Arrange
        workload_no_containers = Workload(attrs={"name": "no-containers", "spec": {}})

        # Act
        result = workload_no_containers.get_container("any-name")

        # Assert
        self.assertIsNone(result)

    @patch("cpln.models.workloads.Deployment")
    def test_exec_operation_with_websocket_error_raises_websocket_exit_code_error(
        self, mock_deployment_class
    ):
        """Test that exec() properly handles WebSocket errors"""
        # Arrange
        mock_deployment = MagicMock(spec=Deployment)
        websocket_error = WebSocketExitCodeError("Command failed with exit code 1")
        mock_deployment.exec.side_effect = websocket_error

        with patch.object(self.workload, "get_deployment") as mock_get_deployment:
            mock_get_deployment.return_value = mock_deployment

            # Act & Assert
            with self.assertRaises(WebSocketExitCodeError) as context:
                self.workload.exec("failing-command", location="us-east-1")

            self.assertEqual(context.exception, websocket_error)


if __name__ == "__main__":
    unittest.main()  # type: ignore
