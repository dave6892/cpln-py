import unittest
from datetime import datetime, timedelta
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

        # Should re-raise APIError so it can be handled by retry logic
        with self.assertRaises(APIError) as cm:
            self.collection._get_workload_containers(workload_config)
        self.assertEqual(str(cm.exception), "API Error")

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

        # Should re-raise APIError so it can be handled by retry logic
        with self.assertRaises(APIError) as cm:
            self.collection._get_workload_containers(
                workload_config, location_filter=self.location
            )
        self.assertEqual(str(cm.exception), "Deployment Error")


class TestAdvancedListingOptions(unittest.TestCase):
    """Tests for AdvancedListingOptions dataclass"""

    def test_default_values(self) -> None:
        """Test default values for AdvancedListingOptions"""
        from cpln.models.containers import AdvancedListingOptions

        options = AdvancedListingOptions()

        self.assertTrue(options.enable_parallel)
        self.assertEqual(options.max_workers, 5)
        self.assertTrue(options.enable_cache)
        self.assertEqual(options.cache_ttl_seconds, 300)
        self.assertFalse(options.enable_pagination)
        self.assertEqual(options.page_size, 50)
        self.assertIsNone(options.max_results)
        self.assertTrue(options.enable_retry)
        self.assertEqual(options.max_retries, 3)
        self.assertEqual(options.retry_delay_seconds, 1.0)
        self.assertEqual(options.retry_backoff_factor, 2.0)
        self.assertIsNone(options.progress_callback)
        self.assertFalse(options.filter_unhealthy)
        self.assertFalse(options.include_system_containers)
        self.assertTrue(options.collect_statistics)

    def test_custom_values(self) -> None:
        """Test custom values for AdvancedListingOptions"""
        from cpln.models.containers import AdvancedListingOptions

        def mock_callback(stage: str, current: int, total: int) -> None:
            pass

        options = AdvancedListingOptions(
            enable_parallel=False,
            max_workers=10,
            enable_cache=False,
            cache_ttl_seconds=600,
            enable_pagination=True,
            page_size=100,
            max_results=500,
            enable_retry=False,
            max_retries=5,
            retry_delay_seconds=2.0,
            retry_backoff_factor=3.0,
            progress_callback=mock_callback,
            filter_unhealthy=True,
            include_system_containers=True,
            collect_statistics=False,
        )

        self.assertFalse(options.enable_parallel)
        self.assertEqual(options.max_workers, 10)
        self.assertFalse(options.enable_cache)
        self.assertEqual(options.cache_ttl_seconds, 600)
        self.assertTrue(options.enable_pagination)
        self.assertEqual(options.page_size, 100)
        self.assertEqual(options.max_results, 500)
        self.assertFalse(options.enable_retry)
        self.assertEqual(options.max_retries, 5)
        self.assertEqual(options.retry_delay_seconds, 2.0)
        self.assertEqual(options.retry_backoff_factor, 3.0)
        self.assertEqual(options.progress_callback, mock_callback)
        self.assertTrue(options.filter_unhealthy)
        self.assertTrue(options.include_system_containers)
        self.assertFalse(options.collect_statistics)


class TestContainerListingStatistics(unittest.TestCase):
    """Tests for ContainerListingStatistics dataclass"""

    def test_initialization(self) -> None:
        """Test statistics initialization"""
        from cpln.models.containers import ContainerListingStatistics

        stats = ContainerListingStatistics()

        self.assertIsInstance(stats.start_time, datetime)
        self.assertIsNone(stats.end_time)
        self.assertIsNone(stats.duration_seconds)

        self.assertEqual(stats.total_workloads_processed, 0)
        self.assertEqual(stats.successful_workloads, 0)
        self.assertEqual(stats.failed_workloads, 0)

        self.assertEqual(stats.total_containers_found, 0)
        self.assertEqual(stats.healthy_containers, 0)
        self.assertEqual(stats.unhealthy_containers, 0)

        self.assertEqual(stats.cache_hits, 0)
        self.assertEqual(stats.cache_misses, 0)
        self.assertEqual(stats.api_calls_made, 0)

        self.assertEqual(stats.errors, [])

    def test_finalize(self) -> None:
        """Test statistics finalization"""
        from cpln.models.containers import ContainerListingStatistics

        stats = ContainerListingStatistics()
        start_time = stats.start_time

        # Simulate some processing time
        import time

        time.sleep(0.01)

        stats.finalize()

        self.assertIsNotNone(stats.end_time)
        self.assertIsNotNone(stats.duration_seconds)
        self.assertGreater(stats.duration_seconds, 0)
        self.assertGreaterEqual(stats.end_time, start_time)


class TestCacheEntry(unittest.TestCase):
    """Tests for CacheEntry dataclass"""

    def test_not_expired(self) -> None:
        """Test cache entry that is not expired"""
        from cpln.models.containers import CacheEntry, Container

        container = Container(
            name="test",
            image="nginx",
            workload_name="wl",
            gvc_name="gvc",
            location="loc",
        )

        entry = CacheEntry(data=[container], timestamp=datetime.now(), ttl_seconds=300)

        self.assertFalse(entry.is_expired())

    def test_expired(self) -> None:
        """Test cache entry that is expired"""
        from cpln.models.containers import CacheEntry, Container

        container = Container(
            name="test",
            image="nginx",
            workload_name="wl",
            gvc_name="gvc",
            location="loc",
        )

        # Create entry with past timestamp
        past_time = datetime.now() - timedelta(seconds=400)
        entry = CacheEntry(data=[container], timestamp=past_time, ttl_seconds=300)

        self.assertTrue(entry.is_expired())


class TestContainerCache(unittest.TestCase):
    """Tests for ContainerCache class"""

    def setUp(self) -> None:
        """Set up test data"""
        from cpln.models.containers import Container, ContainerCache

        self.cache = ContainerCache()
        self.container = Container(
            name="test",
            image="nginx",
            workload_name="wl",
            gvc_name="gvc",
            location="loc",
        )

    def test_set_and_get(self) -> None:
        """Test setting and getting cache data"""
        self.cache.set("key1", [self.container], 300)

        result = self.cache.get("key1")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.container)

    def test_get_nonexistent(self) -> None:
        """Test getting non-existent cache key"""
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)

    def test_get_expired(self) -> None:
        """Test getting expired cache entry"""
        # Set with very short TTL
        self.cache.set("key1", [self.container], 0)

        # Should return None for expired entry
        result = self.cache.get("key1")
        self.assertIsNone(result)

    def test_clear(self) -> None:
        """Test clearing cache"""
        self.cache.set("key1", [self.container], 300)
        self.cache.set("key2", [self.container], 300)

        self.assertEqual(self.cache.get_size(), 2)

        self.cache.clear()

        self.assertEqual(self.cache.get_size(), 0)
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_remove(self) -> None:
        """Test removing specific cache entry"""
        self.cache.set("key1", [self.container], 300)
        self.cache.set("key2", [self.container], 300)

        self.assertEqual(self.cache.get_size(), 2)

        self.cache.remove("key1")

        self.assertEqual(self.cache.get_size(), 1)
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNotNone(self.cache.get("key2"))

    def test_get_size_cleans_expired(self) -> None:
        """Test that get_size cleans up expired entries"""
        # Add some valid and expired entries
        self.cache.set("valid", [self.container], 300)
        self.cache.set("expired", [self.container], 0)

        # get_size should clean up expired entries
        size = self.cache.get_size()

        self.assertEqual(size, 1)
        self.assertIsNotNone(self.cache.get("valid"))
        self.assertIsNone(self.cache.get("expired"))


class TestAdvancedContainerListing(unittest.TestCase):
    """Tests for advanced container listing features"""

    def setUp(self) -> None:
        """Set up test data"""
        from cpln.models.containers import AdvancedListingOptions, ContainerCollection

        self.client = MagicMock()
        self.collection = ContainerCollection(client=self.client)
        self.gvc_name = "test-gvc"
        self.location = "aws-us-west-2"
        self.options = AdvancedListingOptions()

    def test_list_advanced_default_options(self) -> None:
        """Test list_advanced with default options"""

        # Mock API responses
        self.client.api.get_workload.side_effect = [
            {"items": [{"name": "workload1"}]},
            {"name": "workload1"},
        ]
        self.client.api.get_workload_deployment.return_value = {
            "metadata": {"name": "test-deployment"},
            "status": {
                "versions": [
                    {
                        "version": "v1",
                        "containers": {"app": {"image": "nginx:latest", "env": []}},
                    }
                ]
            },
        }

        containers, stats = self.collection.list_advanced(
            gvc=self.gvc_name, location=self.location
        )

        self.assertIsInstance(containers, list)
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats.total_workloads_processed, 0)
        self.assertIsNotNone(stats.duration_seconds)

    def test_list_advanced_with_cache_hit(self) -> None:
        """Test list_advanced with cache hit"""
        from cpln.models.containers import Container

        # Pre-populate cache
        container = Container(
            name="cached",
            image="nginx",
            workload_name="wl",
            gvc_name=self.gvc_name,
            location=self.location,
        )

        cache_key = self.collection._generate_cache_key(
            self.gvc_name, self.location, None
        )
        self.collection._cache.set(cache_key, [container], 300)

        containers, stats = self.collection.list_advanced(
            gvc=self.gvc_name, location=self.location, options=self.options
        )

        self.assertEqual(len(containers), 1)
        self.assertEqual(containers[0], container)
        self.assertEqual(stats.cache_hits, 1)
        self.assertEqual(stats.cache_misses, 0)

    def test_list_advanced_with_cache_miss(self) -> None:
        """Test list_advanced with cache miss"""
        # Mock API responses
        self.client.api.get_workload.side_effect = [
            {"items": []},  # No workloads
        ]

        containers, stats = self.collection.list_advanced(
            gvc=self.gvc_name, location=self.location, options=self.options
        )

        self.assertEqual(len(containers), 0)
        self.assertEqual(stats.cache_hits, 0)
        self.assertEqual(stats.cache_misses, 1)

    def test_list_advanced_filter_unhealthy(self) -> None:
        """Test filtering unhealthy containers"""
        from cpln.models.containers import AdvancedListingOptions, Container

        # Create containers with different health statuses
        healthy_container = Container(
            name="healthy",
            image="nginx",
            workload_name="wl",
            gvc_name=self.gvc_name,
            location=self.location,
            health_status="healthy",
        )

        unhealthy_container = Container(
            name="unhealthy",
            image="nginx",
            workload_name="wl",
            gvc_name=self.gvc_name,
            location=self.location,
            health_status="unhealthy",
        )

        # Mock the internal method to return both containers
        with patch.object(self.collection, "_list_containers_sequential") as mock_list:
            mock_list.return_value = [healthy_container, unhealthy_container]

            options = AdvancedListingOptions(filter_unhealthy=True, enable_cache=False)

            containers, stats = self.collection.list_advanced(
                gvc=self.gvc_name, workload_name="wl", options=options
            )

            # Should only return healthy container
            self.assertEqual(len(containers), 1)
            self.assertEqual(containers[0].name, "healthy")

    def test_list_advanced_pagination(self) -> None:
        """Test pagination functionality"""
        from cpln.models.containers import AdvancedListingOptions, Container

        # Create multiple containers
        containers_data = []
        for i in range(10):
            container = Container(
                name=f"container-{i}",
                image="nginx",
                workload_name="wl",
                gvc_name=self.gvc_name,
                location=self.location,
            )
            containers_data.append(container)

        # Mock the internal method to return all containers
        with patch.object(self.collection, "_list_containers_sequential") as mock_list:
            mock_list.return_value = containers_data

            options = AdvancedListingOptions(
                enable_pagination=True, max_results=5, enable_cache=False
            )

            containers, stats = self.collection.list_advanced(
                gvc=self.gvc_name, workload_name="wl", options=options
            )

            # Should only return first 5 containers
            self.assertEqual(len(containers), 5)
            for i in range(5):
                self.assertEqual(containers[i].name, f"container-{i}")

    def test_count_containers(self) -> None:
        """Test container counting functionality"""
        from cpln.models.containers import Container

        # Mock list_advanced to return specific containers
        with patch.object(self.collection, "list_advanced") as mock_list:
            mock_containers = [
                Container(
                    name=f"container-{i}",
                    image="nginx",
                    workload_name="wl",
                    gvc_name=self.gvc_name,
                    location=self.location,
                )
                for i in range(3)
            ]
            mock_list.return_value = (mock_containers, MagicMock())

            count = self.collection.count_containers(
                gvc=self.gvc_name, location=self.location
            )

            self.assertEqual(count, 3)

    def test_cache_management(self) -> None:
        """Test cache management methods"""
        from cpln.models.containers import Container

        # Add some data to cache
        container = Container(
            name="test",
            image="nginx",
            workload_name="wl",
            gvc_name=self.gvc_name,
            location=self.location,
        )

        cache_key = self.collection._generate_cache_key(
            self.gvc_name, self.location, None
        )
        self.collection._cache.set(cache_key, [container], 300)

        # Test cache size
        self.assertEqual(self.collection.get_cache_size(), 1)

        # Test cache clear
        self.collection.clear_cache()
        self.assertEqual(self.collection.get_cache_size(), 0)

    def test_generate_cache_key(self) -> None:
        """Test cache key generation"""
        # Test with all parameters
        key1 = self.collection._generate_cache_key("gvc1", "loc1", "wl1")
        self.assertEqual(key1, "gvc1|loc:loc1|wl:wl1")

        # Test without workload
        key2 = self.collection._generate_cache_key("gvc1", "loc1", None)
        self.assertEqual(key2, "gvc1|loc:loc1")

        # Test without location
        key3 = self.collection._generate_cache_key("gvc1", None, "wl1")
        self.assertEqual(key3, "gvc1|wl:wl1")

        # Test with only GVC
        key4 = self.collection._generate_cache_key("gvc1", None, None)
        self.assertEqual(key4, "gvc1")

    @patch("time.sleep")  # Mock sleep to speed up test
    def test_retry_logic(self, mock_sleep) -> None:
        """Test retry logic for rate limiting"""
        from cpln.models.containers import AdvancedListingOptions

        # Configure retry options
        options = AdvancedListingOptions(
            enable_retry=True,
            max_retries=2,
            retry_delay_seconds=0.1,
            retry_backoff_factor=2.0,
        )

        workload_config = WorkloadConfig(gvc=self.gvc_name, workload_id="test-workload")

        # Mock get_workload to return workload data (this is called first to get workload details)
        self.client.api.get_workload.return_value = {
            "name": "test-workload",
            "spec": {"defaultOptions": {"locations": [self.location]}},
        }

        # Mock API to fail with rate limiting error first time, then succeed
        # This is the actual call that gets retried in _get_workload_containers
        rate_limit_error = APIError("Rate limit exceeded")
        self.client.api.get_workload_deployment.side_effect = [
            rate_limit_error,  # First call fails
            {
                "metadata": {"name": "test-deployment"},
                "status": {"versions": []},
            },  # Second call succeeds
        ]

        # Should succeed after retry
        containers = self.collection._get_workload_containers_with_retry(
            workload_config, self.location, options
        )

        # Verify sleep was called for retry delay
        mock_sleep.assert_called_once_with(0.1)

        # Should return empty list (no containers in deployment)
        self.assertEqual(containers, [])

    def test_progress_callback(self) -> None:
        """Test progress callback functionality"""
        from cpln.models.containers import AdvancedListingOptions

        callback_calls = []

        def mock_callback(stage: str, current: int, total: int) -> None:
            callback_calls.append((stage, current, total))

        options = AdvancedListingOptions(
            progress_callback=mock_callback,
            enable_parallel=False,  # Use sequential to test callback
            enable_cache=False,
        )

        # Mock API responses
        self.client.api.get_workload.side_effect = [
            {"items": [{"name": "wl1"}, {"name": "wl2"}]},
            {"name": "wl1"},
            {"name": "wl2"},
        ]
        self.client.api.get_workload_deployment.return_value = {
            "metadata": {"name": "test-deployment"},
            "status": {"versions": []},
        }

        containers, stats = self.collection.list_advanced(
            gvc=self.gvc_name, options=options
        )

        # Verify callback was called
        self.assertGreater(len(callback_calls), 0)

        # Check that all calls were for "Processing workloads"
        for stage, current, total in callback_calls:
            self.assertEqual(stage, "Processing workloads")
            self.assertGreaterEqual(current, 1)
            self.assertEqual(total, 2)


if __name__ == "__main__":
    unittest.main()
