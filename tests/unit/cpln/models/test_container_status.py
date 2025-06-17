"""Unit tests for container status parsing functionality - Issue #30."""

import unittest
from unittest.mock import MagicMock, patch

from cpln.errors import APIError
from cpln.models.containers import (
    Container,
    ContainerCollection,
    HealthEvaluator,
    MetricsExtractor,
    StatusParser,
)


class TestStatusParser(unittest.TestCase):
    """Tests for the StatusParser utility class"""

    def setUp(self) -> None:
        """Set up test data"""
        self.sample_deployment_status = {
            "endpoint": "https://example.com",
            "remote": "https://remote.example.com",
            "lastProcessedVersion": 3,
            "expectedDeploymentVersion": 3,
            "ready": True,
            "deploying": False,
            "message": "Deployment successful",
            "versions": [
                {
                    "name": "v1.0.0",
                    "created": "2024-01-01T12:00:00Z",
                    "workload": 1,
                    "gvc": 1,
                    "ready": True,
                    "message": "Version ready",
                    "zone": "us-east-1",
                    "containers": {
                        "app-container": {
                            "image": "nginx:latest",
                            "status": "running",
                        },
                        "cpln-mounter": {
                            "image": "cpln/mounter:latest",
                        },
                    },
                }
            ],
            "jobExecutions": [
                {
                    "workloadVersion": 1,
                    "status": "successful",
                    "startTime": "2024-01-01T12:00:00Z",
                    "completionTime": "2024-01-01T12:05:00Z",
                    "name": "deploy-job",
                    "replica": "deploy-job-abc123",
                    "conditions": [
                        {
                            "status": "True",
                            "type": "Complete",
                            "message": "Job completed successfully",
                            "reason": "JobFinished",
                            "lastDetectionTime": "2024-01-01T12:05:00Z",
                            "lastTransitionTime": "2024-01-01T12:05:00Z",
                        }
                    ],
                }
            ],
        }

    def test_parse_deployment_status_basic(self) -> None:
        """Test parsing basic deployment status information"""
        status_info = StatusParser.parse_deployment_status(
            self.sample_deployment_status
        )

        # Check basic deployment info
        self.assertEqual(status_info["endpoint"], "https://example.com")
        self.assertEqual(status_info["remote"], "https://remote.example.com")
        self.assertEqual(status_info["last_processed_version"], 3)
        self.assertEqual(status_info["expected_deployment_version"], 3)
        self.assertTrue(status_info["ready"])
        self.assertFalse(status_info["deploying"])
        self.assertEqual(status_info["message"], "Deployment successful")

    def test_parse_deployment_status_versions(self) -> None:
        """Test parsing version information from deployment status"""
        status_info = StatusParser.parse_deployment_status(
            self.sample_deployment_status
        )

        # Check latest version info
        self.assertEqual(status_info["latest_version_name"], "v1.0.0")
        self.assertEqual(status_info["latest_version_created"], "2024-01-01T12:00:00Z")
        self.assertEqual(status_info["latest_version_workload"], 1)
        self.assertEqual(status_info["latest_version_gvc"], 1)
        self.assertTrue(status_info["latest_version_ready"])
        self.assertEqual(status_info["latest_version_message"], "Version ready")
        self.assertEqual(status_info["latest_version_zone"], "us-east-1")

    def test_parse_deployment_status_job_executions(self) -> None:
        """Test parsing job execution information from deployment status"""
        status_info = StatusParser.parse_deployment_status(
            self.sample_deployment_status
        )

        # Check latest job execution info
        self.assertEqual(status_info["latest_job_workload_version"], 1)
        self.assertEqual(status_info["latest_job_status"], "successful")
        self.assertEqual(status_info["latest_job_start_time"], "2024-01-01T12:00:00Z")
        self.assertEqual(
            status_info["latest_job_completion_time"], "2024-01-01T12:05:00Z"
        )
        self.assertEqual(status_info["latest_job_name"], "deploy-job")
        self.assertEqual(status_info["latest_job_replica"], "deploy-job-abc123")

        # Check job condition info
        self.assertEqual(status_info["latest_job_condition_status"], "True")
        self.assertEqual(status_info["latest_job_condition_type"], "Complete")
        self.assertEqual(
            status_info["latest_job_condition_message"], "Job completed successfully"
        )
        self.assertEqual(status_info["latest_job_condition_reason"], "JobFinished")

    def test_parse_deployment_status_empty(self) -> None:
        """Test parsing empty deployment status"""
        empty_status = {}
        status_info = StatusParser.parse_deployment_status(empty_status)

        # Check that defaults are applied
        self.assertIsNone(status_info["endpoint"])
        self.assertIsNone(status_info["remote"])
        self.assertFalse(status_info["ready"])
        self.assertFalse(status_info["deploying"])

    def test_parse_container_status_from_versions(self) -> None:
        """Test parsing container-specific status from versions"""
        versions = self.sample_deployment_status["versions"]
        container_status = StatusParser.parse_container_status_from_versions(
            versions, "app-container"
        )

        # Check container-specific info
        self.assertTrue(container_status["version_ready"])
        self.assertEqual(container_status["version_name"], "v1.0.0")
        self.assertEqual(container_status["version_zone"], "us-east-1")
        self.assertEqual(container_status["version_message"], "Version ready")
        self.assertIn("container_data", container_status)

    def test_parse_container_status_not_found(self) -> None:
        """Test parsing container status when container is not found"""
        versions = self.sample_deployment_status["versions"]
        container_status = StatusParser.parse_container_status_from_versions(
            versions, "nonexistent-container"
        )

        # Check defaults
        self.assertFalse(container_status["ready"])
        self.assertEqual(container_status["total_replicas"], 0)
        self.assertEqual(container_status["ready_replicas"], 0)


class TestHealthEvaluator(unittest.TestCase):
    """Tests for the HealthEvaluator utility class"""

    def test_evaluate_health_status_healthy(self) -> None:
        """Test health evaluation for healthy deployment"""
        status_info = {
            "ready": True,
            "deploying": False,
            "latest_version_ready": True,
            "latest_job_status": "successful",
        }

        health_status = HealthEvaluator.evaluate_health_status(status_info)
        self.assertEqual(health_status, "healthy")

    def test_evaluate_health_status_deploying(self) -> None:
        """Test health evaluation for deploying deployment"""
        status_info = {
            "ready": False,
            "deploying": True,
            "latest_version_ready": False,
        }

        health_status = HealthEvaluator.evaluate_health_status(status_info)
        self.assertEqual(health_status, "degraded")

    def test_evaluate_health_status_failed_job(self) -> None:
        """Test health evaluation for deployment with failed job"""
        status_info = {
            "ready": True,
            "deploying": False,
            "latest_version_ready": True,
            "latest_job_status": "failed",
        }

        health_status = HealthEvaluator.evaluate_health_status(status_info)
        self.assertEqual(health_status, "unhealthy")

    def test_evaluate_health_status_active_job(self) -> None:
        """Test health evaluation for deployment with active job"""
        status_info = {
            "ready": True,
            "deploying": False,
            "latest_version_ready": True,
            "latest_job_status": "active",
        }

        health_status = HealthEvaluator.evaluate_health_status(status_info)
        self.assertEqual(health_status, "degraded")

    def test_evaluate_health_status_not_ready(self) -> None:
        """Test health evaluation for deployment not ready"""
        status_info = {
            "ready": False,
            "deploying": False,
            "latest_version_ready": False,
        }

        health_status = HealthEvaluator.evaluate_health_status(status_info)
        self.assertEqual(health_status, "unhealthy")

    def test_evaluate_health_status_unknown(self) -> None:
        """Test health evaluation for unknown status"""
        status_info = {
            "ready": False,
            "deploying": False,
        }

        health_status = HealthEvaluator.evaluate_health_status(status_info)
        self.assertEqual(health_status, "degraded")

    def test_get_health_summary(self) -> None:
        """Test comprehensive health summary generation"""
        status_info = {
            "ready": True,
            "deploying": False,
            "latest_version_ready": True,
            "latest_job_status": "successful",
            "message": "All systems operational",
        }

        summary = HealthEvaluator.get_health_summary(status_info)

        self.assertEqual(summary["health_status"], "healthy")
        self.assertTrue(summary["deployment_ready"])
        self.assertFalse(summary["deployment_deploying"])
        self.assertTrue(summary["version_ready"])
        self.assertEqual(summary["job_status"], "successful")
        self.assertEqual(summary["status_message"], "All systems operational")
        self.assertEqual(summary["reason"], "Deployment and version are ready")


class TestMetricsExtractor(unittest.TestCase):
    """Tests for the MetricsExtractor utility class"""

    def test_extract_resource_metrics(self) -> None:
        """Test resource metrics extraction"""
        status_info = {"ready": True}
        metrics = MetricsExtractor.extract_resource_metrics(status_info)

        # For now, metrics should be None since the schema doesn't include them
        self.assertIsNone(metrics["cpu_usage"])
        self.assertIsNone(metrics["memory_usage"])

    def test_calculate_replica_metrics(self) -> None:
        """Test replica metrics calculation"""
        status_info = {"ready": True}
        replica_metrics = MetricsExtractor.calculate_replica_metrics(status_info)

        # For now, replica metrics should be None since schema doesn't include them
        self.assertIsNone(replica_metrics["total_replicas"])
        self.assertIsNone(replica_metrics["ready_replicas"])
        self.assertIsNone(replica_metrics["restart_count"])


class TestContainerStatusIntegration(unittest.TestCase):
    """Integration tests for container status functionality"""

    def setUp(self) -> None:
        """Set up test data"""
        self.container = Container(
            name="test-container",
            image="nginx:latest",
            workload_name="test-workload",
            gvc_name="test-gvc",
            location="us-east-1",
        )

        self.sample_deployment_status = {
            "ready": True,
            "deploying": False,
            "message": "Deployment ready",
            "versions": [
                {
                    "name": "v1.0.0",
                    "ready": True,
                    "containers": {
                        "test-container": {
                            "image": "nginx:latest",
                            "status": "running",
                        }
                    },
                }
            ],
            "jobExecutions": [
                {
                    "status": "successful",
                    "conditions": [
                        {
                            "status": "True",
                            "type": "Complete",
                        }
                    ],
                }
            ],
        }

    def test_update_status_from_deployment(self) -> None:
        """Test updating container status from deployment data"""
        # Update status from deployment
        self.container.update_status_from_deployment(self.sample_deployment_status)

        # Check that status was updated
        self.assertEqual(self.container.health_status, "healthy")
        self.assertEqual(self.container.status, "running")
        self.assertIsNotNone(self.container.updated_at)

    def test_get_health_summary(self) -> None:
        """Test getting health summary from container"""
        # Update status first
        self.container.update_status_from_deployment(self.sample_deployment_status)

        # Get health summary
        summary = self.container.get_health_summary()

        self.assertEqual(summary["health_status"], "healthy")
        self.assertTrue(summary["is_healthy"])
        self.assertEqual(summary["status"], "running")
        self.assertIsNotNone(summary["last_updated"])

    def test_refresh_status_success(self) -> None:
        """Test successful status refresh from API"""
        # Mock client
        mock_client = MagicMock()
        mock_client.api.get_workload_deployment.return_value = {
            "status": self.sample_deployment_status
        }

        # Refresh status
        result = self.container.refresh_status(mock_client)

        # Check result
        self.assertTrue(result)
        self.assertEqual(self.container.health_status, "healthy")
        self.assertEqual(self.container.status, "running")

        # Verify API was called
        mock_client.api.get_workload_deployment.assert_called_once()

    def test_refresh_status_failure(self) -> None:
        """Test status refresh failure handling"""
        # Mock client to raise exception
        mock_client = MagicMock()
        mock_client.api.get_workload_deployment.side_effect = APIError("API Error")

        # Refresh status
        result = self.container.refresh_status(mock_client)

        # Check that failure was handled gracefully
        self.assertFalse(result)
        # Status should remain unchanged
        self.assertIsNone(self.container.health_status)


class TestContainerCollectionStatusFeatures(unittest.TestCase):
    """Tests for status-related features in ContainerCollection"""

    def setUp(self) -> None:
        """Set up test data"""
        self.client = MagicMock()
        self.collection = ContainerCollection(client=self.client)
        self.gvc_name = "test-gvc"
        self.workload_name = "test-workload"
        self.location = "us-east-1"

        # Create sample containers
        self.containers = [
            Container(
                name=f"container-{i}",
                image="nginx:latest",
                workload_name=self.workload_name,
                gvc_name=self.gvc_name,
                location=self.location,
                health_status="healthy" if i % 2 == 0 else "unhealthy",
            )
            for i in range(4)
        ]

    def test_refresh_all_status_sequential(self) -> None:
        """Test refreshing status for all containers sequentially"""
        from cpln.models.containers import AdvancedListingOptions

        # Configure options for sequential processing
        options = AdvancedListingOptions(enable_parallel=False)

        # Mock container refresh_status method
        for container in self.containers:
            container.refresh_status = MagicMock(return_value=True)

        # Refresh all status
        successful, failed = self.collection.refresh_all_status(
            self.containers, options
        )

        # Check results
        self.assertEqual(successful, len(self.containers))
        self.assertEqual(failed, 0)

        # Verify all containers had their status refreshed
        for container in self.containers:
            container.refresh_status.assert_called_once_with(self.client)

    def test_refresh_all_status_parallel(self) -> None:
        """Test refreshing status for all containers in parallel"""
        from cpln.models.containers import AdvancedListingOptions

        # Configure options for parallel processing
        options = AdvancedListingOptions(enable_parallel=True, max_workers=2)

        # Mock container refresh_status method
        for container in self.containers:
            container.refresh_status = MagicMock(return_value=True)

        # Refresh all status
        successful, failed = self.collection.refresh_all_status(
            self.containers, options
        )

        # Check results
        self.assertEqual(successful, len(self.containers))
        self.assertEqual(failed, 0)

        # Verify all containers had their status refreshed
        for container in self.containers:
            container.refresh_status.assert_called_once_with(self.client)

    def test_refresh_all_status_with_failures(self) -> None:
        """Test refreshing status with some failures"""
        from cpln.models.containers import AdvancedListingOptions

        options = AdvancedListingOptions(enable_parallel=False)

        # Mock some containers to fail
        for i, container in enumerate(self.containers):
            if i % 2 == 0:
                container.refresh_status = MagicMock(return_value=True)
            else:
                container.refresh_status = MagicMock(side_effect=APIError("Failed"))

        # Refresh all status
        successful, failed = self.collection.refresh_all_status(
            self.containers, options
        )

        # Check results
        self.assertEqual(successful, 2)  # Half succeeded
        self.assertEqual(failed, 2)  # Half failed

    @patch.object(ContainerCollection, "list_advanced")
    def test_get_containers_with_status(self, mock_list_advanced) -> None:
        """Test getting containers with status refresh"""
        from cpln.models.containers import ContainerListingStatistics

        # Mock list_advanced to return containers
        stats = ContainerListingStatistics()
        mock_list_advanced.return_value = (self.containers, stats)

        # Mock refresh_all_status
        with patch.object(self.collection, "refresh_all_status") as mock_refresh:
            mock_refresh.return_value = (len(self.containers), 0)

            # Get containers with status
            containers, returned_stats = self.collection.get_containers_with_status(
                self.gvc_name, self.workload_name, self.location
            )

        # Check results
        self.assertEqual(len(containers), len(self.containers))
        self.assertIsNotNone(returned_stats)

        # Verify methods were called
        mock_list_advanced.assert_called_once()
        mock_refresh.assert_called_once()

    @patch.object(ContainerCollection, "list_advanced")
    def test_get_containers_with_status_no_refresh(self, mock_list_advanced) -> None:
        """Test getting containers without status refresh"""
        from cpln.models.containers import ContainerListingStatistics

        # Mock list_advanced to return containers
        stats = ContainerListingStatistics()
        mock_list_advanced.return_value = (self.containers, stats)

        # Mock refresh_all_status
        with patch.object(self.collection, "refresh_all_status") as mock_refresh:
            # Get containers without status refresh
            containers, returned_stats = self.collection.get_containers_with_status(
                self.gvc_name, self.workload_name, self.location, refresh_status=False
            )

        # Check results
        self.assertEqual(len(containers), len(self.containers))
        self.assertIsNotNone(returned_stats)

        # Verify refresh was not called
        mock_list_advanced.assert_called_once()
        mock_refresh.assert_not_called()


class TestContainerStatusEdgeCases(unittest.TestCase):
    """Tests for edge cases in container status functionality"""

    def test_status_parser_malformed_data(self) -> None:
        """Test status parser with malformed data"""
        malformed_data = {
            "ready": "not_a_boolean",  # Should handle string instead of boolean
            "versions": "not_a_list",  # Should handle string instead of list
        }

        # Should not raise exception, but handle gracefully
        status_info = StatusParser.parse_deployment_status(malformed_data)

        # Check that it handled the malformed data gracefully
        self.assertFalse(status_info["ready"])  # Should default to False
        self.assertIsNone(status_info["latest_version_name"])  # Should be None

    def test_health_evaluator_edge_cases(self) -> None:
        """Test health evaluator with edge case inputs"""
        # Test with minimal status info
        minimal_status = {}
        health_status = HealthEvaluator.evaluate_health_status(minimal_status)
        self.assertEqual(health_status, "degraded")

        # Test with conflicting status info
        conflicting_status = {
            "ready": True,
            "deploying": True,  # Contradictory state
        }
        health_status = HealthEvaluator.evaluate_health_status(conflicting_status)
        self.assertEqual(health_status, "degraded")  # Should prefer deploying

    def test_container_refresh_status_no_client(self) -> None:
        """Test container status refresh with None client"""
        container = Container(
            name="test",
            image="nginx",
            workload_name="test-workload",
            gvc_name="test-gvc",
            location="us-east-1",
        )

        # Should handle None client gracefully
        result = container.refresh_status(None)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
