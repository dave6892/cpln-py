import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from cpln.config import WorkloadConfig
from cpln.errors import APIError
from cpln.models.containers import Container, ContainerCollection, ContainerParser


class TestContainer(unittest.TestCase):
    """Tests for the Container dataclass"""

    def setUp(self) -> None:
        """Set up test data"""
        self.container_data = {
            "name": "test-container",
            "image": "nginx:latest",
            "env": [
                {"name": "ENV_VAR1", "value": "value1"},
                {"name": "ENV_VAR2", "value": "value2"},
            ],
            "resources": {
                "cpu": "100m",
                "memory": "128Mi",
            },
            "ports": [
                {"containerPort": 80, "protocol": "TCP"},
            ],
        }

        self.workload_name = "test-workload"
        self.gvc_name = "test-gvc"
        self.location = "aws-us-west-2"

    def test_container_creation_basic(self) -> None:
        """Test basic container creation"""
        container = Container(
            name="test-container",
            image="nginx:latest",
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )

        self.assertEqual(container.name, "test-container")
        self.assertEqual(container.image, "nginx:latest")
        self.assertEqual(container.workload_name, self.workload_name)
        self.assertEqual(container.gvc_name, self.gvc_name)
        self.assertEqual(container.location, self.location)

        # Check default values
        self.assertEqual(container.environment_variables, {})
        self.assertEqual(container.resource_limits, {})
        self.assertEqual(container.ports, [])

    def test_from_deployment_payload(self) -> None:
        """Test creating container from deployment payload"""
        container = Container.from_deployment_payload(
            container_data=self.container_data,
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
            deployment_name="test-deployment",
        )

        self.assertEqual(container.name, "test-container")
        self.assertEqual(container.image, "nginx:latest")
        self.assertEqual(container.workload_name, self.workload_name)
        self.assertEqual(container.gvc_name, self.gvc_name)
        self.assertEqual(container.location, self.location)
        self.assertEqual(container.deployment_name, "test-deployment")

        # Check parsed environment variables
        expected_env = {"ENV_VAR1": "value1", "ENV_VAR2": "value2"}
        self.assertEqual(container.environment_variables, expected_env)

        # Check parsed resource limits
        expected_resources = {"cpu": "100m", "memory": "128Mi"}
        self.assertEqual(container.resource_limits, expected_resources)

        # Check parsed ports
        self.assertEqual(len(container.ports), 1)
        self.assertEqual(container.ports[0]["containerPort"], 80)

    def test_from_job_payload(self) -> None:
        """Test creating container from job payload"""
        job_data = {"name": "test-job", "version": "v1.0"}

        container = Container.from_job_payload(
            container_data=self.container_data,
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
            job_data=job_data,
        )

        self.assertEqual(container.name, "test-container")
        self.assertEqual(container.deployment_name, "test-job")
        self.assertEqual(container.version, "v1.0")

    def test_update_status(self) -> None:
        """Test updating container status"""
        container = Container(
            name="test-container",
            image="nginx:latest",
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )

        # Update status
        container.update_status(
            status="running",
            health_status="healthy",
            ready_replicas=2,
            total_replicas=2,
            restart_count=0,
            cpu_usage=50.0,
            memory_usage=75.0,
        )

        self.assertEqual(container.status, "running")
        self.assertEqual(container.health_status, "healthy")
        self.assertEqual(container.ready_replicas, 2)
        self.assertEqual(container.total_replicas, 2)
        self.assertEqual(container.restart_count, 0)
        self.assertEqual(container.cpu_usage, 50.0)
        self.assertEqual(container.memory_usage, 75.0)
        self.assertIsInstance(container.updated_at, datetime)

    def test_is_healthy(self) -> None:
        """Test health status checking"""
        container = Container(
            name="test-container",
            image="nginx:latest",
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )

        # Test with explicit health status
        container.health_status = "healthy"
        self.assertTrue(container.is_healthy())

        container.health_status = "unhealthy"
        self.assertFalse(container.is_healthy())

        # Test with replica status fallback
        container.health_status = None
        container.ready_replicas = 2
        container.total_replicas = 2
        self.assertTrue(container.is_healthy())

        container.ready_replicas = 1
        container.total_replicas = 2
        self.assertFalse(container.is_healthy())

        # Test default (no status available)
        container.ready_replicas = None
        container.total_replicas = None
        self.assertFalse(container.is_healthy())

    def test_get_resource_utilization(self) -> None:
        """Test resource utilization getter"""
        container = Container(
            name="test-container",
            image="nginx:latest",
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )

        container.cpu_usage = 45.5
        container.memory_usage = 67.8

        utilization = container.get_resource_utilization()
        self.assertEqual(utilization["cpu"], 45.5)
        self.assertEqual(utilization["memory"], 67.8)

    def test_to_dict(self) -> None:
        """Test dictionary conversion"""
        now = datetime.now()
        container = Container(
            name="test-container",
            image="nginx:latest",
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
            status="running",
            health_status="healthy",
            created_at=now,
        )

        container_dict = container.to_dict()

        self.assertEqual(container_dict["name"], "test-container")
        self.assertEqual(container_dict["image"], "nginx:latest")
        self.assertEqual(container_dict["workload_name"], self.workload_name)
        self.assertEqual(container_dict["gvc_name"], self.gvc_name)
        self.assertEqual(container_dict["location"], self.location)
        self.assertEqual(container_dict["status"], "running")
        self.assertEqual(container_dict["health_status"], "healthy")
        self.assertEqual(container_dict["created_at"], now.isoformat())


class TestContainerParser(unittest.TestCase):
    """Tests for the ContainerParser utility class"""

    def setUp(self) -> None:
        """Set up test data"""
        self.workload_name = "test-workload"
        self.gvc_name = "test-gvc"
        self.location = "aws-us-west-2"

        self.deployment_data = {
            "metadata": {"name": "test-deployment"},
            "status": {
                "versions": [
                    {
                        "version": "v1.0",
                        "containers": {
                            "app-container": {
                                "image": "nginx:latest",
                                "env": [{"name": "ENV1", "value": "val1"}],
                            },
                            "cpln-mounter": {  # Should be ignored
                                "image": "cpln/mounter:latest",
                            },
                        },
                    }
                ],
            },
        }

        self.job_data = {
            "name": "test-job",
            "spec": {
                "job": {
                    "containers": [
                        {
                            "name": "job-container",
                            "image": "busybox:latest",
                        }
                    ]
                }
            },
        }

        self.workload_spec = {
            "containers": [
                {
                    "name": "spec-container",
                    "image": "alpine:latest",
                }
            ]
        }

    def test_parse_deployment_containers(self) -> None:
        """Test parsing containers from deployment data"""
        containers = ContainerParser.parse_deployment_containers(
            deployment_data=self.deployment_data,
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )

        # Should only have one container (cpln-mounter ignored)
        self.assertEqual(len(containers), 1)

        container = containers[0]
        self.assertEqual(container.name, "app-container")
        self.assertEqual(container.image, "nginx:latest")
        self.assertEqual(container.workload_name, self.workload_name)
        self.assertEqual(container.gvc_name, self.gvc_name)
        self.assertEqual(container.location, self.location)
        self.assertEqual(container.deployment_name, "test-deployment")
        self.assertEqual(container.environment_variables["ENV1"], "val1")

    def test_parse_deployment_containers_malformed(self) -> None:
        """Test parsing malformed deployment data"""
        malformed_data = {"invalid": "structure"}

        with self.assertRaises(APIError) as cm:
            ContainerParser.parse_deployment_containers(
                deployment_data=malformed_data,
                workload_name=self.workload_name,
                gvc_name=self.gvc_name,
                location=self.location,
            )

        self.assertIn(
            "Invalid deployment data: missing status.versions", str(cm.exception)
        )

    def test_parse_job_containers(self) -> None:
        """Test parsing containers from job data"""
        containers = ContainerParser.parse_job_containers(
            job_data=self.job_data,
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )

        self.assertEqual(len(containers), 1)

        container = containers[0]
        self.assertEqual(container.name, "job-container")
        self.assertEqual(container.image, "busybox:latest")
        self.assertEqual(container.workload_name, self.workload_name)
        self.assertEqual(container.gvc_name, self.gvc_name)
        self.assertEqual(container.location, self.location)

    def test_parse_job_containers_malformed(self) -> None:
        """Test parsing malformed job data"""
        malformed_data = {"invalid": "structure"}

        with self.assertRaises(APIError) as cm:
            ContainerParser.parse_job_containers(
                job_data=malformed_data,
                workload_name=self.workload_name,
                gvc_name=self.gvc_name,
                location=self.location,
            )

        self.assertIn(
            "Invalid job data: missing spec.job.containers", str(cm.exception)
        )

    def test_parse_workload_spec_containers(self) -> None:
        """Test parsing containers from workload spec"""
        containers = ContainerParser.parse_workload_spec_containers(
            workload_spec=self.workload_spec,
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )

        self.assertEqual(len(containers), 1)

        container = containers[0]
        self.assertEqual(container.name, "spec-container")
        self.assertEqual(container.image, "alpine:latest")
        self.assertEqual(container.workload_name, self.workload_name)
        self.assertEqual(container.gvc_name, self.gvc_name)
        self.assertEqual(container.location, self.location)

    def test_parse_workload_spec_containers_malformed(self) -> None:
        """Test parsing malformed workload spec"""
        malformed_data = {"invalid": "structure"}

        with self.assertRaises(APIError) as cm:
            ContainerParser.parse_workload_spec_containers(
                workload_spec=malformed_data,
                workload_name=self.workload_name,
                gvc_name=self.gvc_name,
                location=self.location,
            )

        self.assertIn("Invalid workload spec: missing containers", str(cm.exception))


class TestContainerCollection(unittest.TestCase):
    """Tests for the ContainerCollection class"""

    def setUp(self) -> None:
        """Set up test data"""
        self.client = MagicMock()
        self.collection = ContainerCollection(client=self.client)
        self.gvc_name = "test-gvc"
        self.location = "aws-us-west-2"
        self.workload_name = "test-workload"

    def test_model_attribute(self) -> None:
        """Test the model attribute is set correctly"""
        self.assertEqual(self.collection.model, Container)

    @patch("cpln.models.containers.ContainerParser.parse_deployment_containers")
    def test_list_containers_single_workload(self, mock_parse: MagicMock) -> None:
        """Test listing containers for a single workload"""
        # Mock API responses
        self.client.api.get_workload.return_value = {"name": self.workload_name}
        self.client.api.get_workload_deployment.return_value = {
            "status": {"versions": []}
        }

        # Mock parser response
        mock_container = Container(
            name="test-container",
            image="nginx:latest",
            workload_name=self.workload_name,
            gvc_name=self.gvc_name,
            location=self.location,
        )
        mock_parse.return_value = [mock_container]

        # Call list method
        containers = self.collection.list(
            gvc=self.gvc_name,
            location=self.location,
            workload_name=self.workload_name,
        )

        # Verify results
        self.assertEqual(len(containers), 1)
        self.assertEqual(containers[0], mock_container)

        # Verify API calls
        self.client.api.get_workload.assert_called()
        self.client.api.get_workload_deployment.assert_called()
        mock_parse.assert_called()

    @patch("cpln.models.containers.ContainerParser.parse_deployment_containers")
    def test_list_containers_all_workloads(self, mock_parse: MagicMock) -> None:
        """Test listing containers for all workloads in GVC"""
        # Mock API responses
        self.client.api.get_workload.side_effect = [
            # First call: list workloads
            {"items": [{"name": "workload1"}, {"name": "workload2"}]},
            # Second call: get workload1 details
            {"name": "workload1"},
            # Third call: get workload2 details
            {"name": "workload2"},
        ]

        self.client.api.get_workload_deployment.return_value = {
            "status": {"versions": []}
        }

        # Mock parser responses
        mock_container1 = Container(
            name="container1",
            image="nginx:latest",
            workload_name="workload1",
            gvc_name=self.gvc_name,
            location=self.location,
        )
        mock_container2 = Container(
            name="container2",
            image="nginx:latest",
            workload_name="workload2",
            gvc_name=self.gvc_name,
            location=self.location,
        )
        mock_parse.side_effect = [[mock_container1], [mock_container2]]

        # Call list method
        containers = self.collection.list(gvc=self.gvc_name, location=self.location)

        # Verify results
        self.assertEqual(len(containers), 2)
        self.assertEqual(containers[0], mock_container1)
        self.assertEqual(containers[1], mock_container2)

    def test_infer_workload_locations(self) -> None:
        """Test location inference from workload data"""
        # Test with explicit locations
        workload_data = {
            "spec": {
                "defaultOptions": {"locations": ["aws-us-east-1", "aws-us-west-2"]}
            }
        }

        locations = self.collection._infer_workload_locations(workload_data)
        self.assertEqual(locations, ["aws-us-east-1", "aws-us-west-2"])

        # Test fallback to common locations
        workload_data = {"spec": {}}
        locations = self.collection._infer_workload_locations(workload_data)
        self.assertIn("aws-us-east-1", locations)
        self.assertIn("aws-us-west-2", locations)

    def test_get_not_implemented(self) -> None:
        """Test that get method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError) as cm:
            self.collection.get(id="test-id")

        self.assertIn("Container retrieval by ID is not supported", str(cm.exception))

    def test_create_not_implemented(self) -> None:
        """Test that create method raises NotImplementedError"""
        with self.assertRaises(NotImplementedError) as cm:
            self.collection.create(name="test-container")

        self.assertIn("Container creation is not supported", str(cm.exception))

    def test_get_workload_containers_api_error(self) -> None:
        """Test handling of API errors when getting workload containers"""
        # Mock API to raise error
        self.client.api.get_workload.side_effect = APIError("API Error")

        workload_config = WorkloadConfig(
            gvc=self.gvc_name, workload_id=self.workload_name
        )

        # Should return empty list on API error
        containers = self.collection._get_workload_containers(workload_config)
        self.assertEqual(containers, [])

    def test_get_workload_containers_deployment_error(self) -> None:
        """Test handling of deployment errors when getting workload containers"""
        # Mock workload API to succeed
        self.client.api.get_workload.return_value = {"name": self.workload_name}

        # Mock deployment API to fail
        self.client.api.get_workload_deployment.side_effect = APIError(
            "Deployment Error"
        )

        workload_config = WorkloadConfig(
            gvc=self.gvc_name, workload_id=self.workload_name
        )

        # Should return empty list on deployment error
        containers = self.collection._get_workload_containers(
            workload_config, location_filter=self.location
        )
        self.assertEqual(containers, [])


if __name__ == "__main__":
    unittest.main()
