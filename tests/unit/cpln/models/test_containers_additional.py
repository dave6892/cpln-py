"""Additional tests for container functionality to improve coverage."""

from unittest import mock

import pytest
from cpln.config.workload import WorkloadConfig
from cpln.errors import APIError
from cpln.models.containers import (
    AdvancedListingOptions,
    Container,
    ContainerCollection,
    ContainerParser,
)


class TestContainerAdditional:
    def test_container_update_status(self):
        """Test container status update functionality."""
        container = Container(
            name="test-container",
            image="test:latest",
            workload_name="test-workload",
            gvc_name="test-gvc",
            location="us-east",
        )

        # Test updating various status fields
        status_update = {
            "status": "Running",
            "health_status": "Healthy",
            "ready_replicas": 2,
            "total_replicas": 3,
            "restart_count": 1,
        }

        container.update_status(status_update)

        # The update_status method sets the entire status dict, not individual fields
        assert container.status == status_update
        assert (
            container.health_status is None
        )  # Individual fields are not set by update_status
        assert container.ready_replicas is None
        assert container.total_replicas is None
        assert container.restart_count is None


class TestContainerParserAdditional:
    def test_parse_deployment_containers_with_ignored_containers(self):
        """Test parsing deployment containers while ignoring system containers."""
        deployment_data = {
            "status": {
                "versions": [
                    {
                        "containers": {
                            "cpln-mounter": {
                                "image": "system:latest"
                            },  # Should be ignored
                            "app-container": {"image": "app:latest"},
                        }
                    }
                ]
            },
            "metadata": {"name": "test-deployment"},
        }

        containers = ContainerParser.parse_deployment_containers(
            deployment_data, "test-workload", "test-gvc", "us-east"
        )

        # Should only have the app container, not the system container
        assert len(containers) == 1
        assert containers[0].name == "app-container"

    def test_parse_job_containers_with_ignored_containers(self):
        """Test parsing job containers while ignoring system containers."""
        job_data = {
            "spec": {
                "job": {
                    "containers": [
                        {
                            "name": "cpln-mounter",
                            "image": "system:latest",
                        },  # Should be ignored
                        {"name": "job-container", "image": "job:latest"},
                    ]
                }
            }
        }

        containers = ContainerParser.parse_job_containers(
            job_data, "test-workload", "test-gvc", "us-east"
        )

        # Should only have the job container, not the system container
        assert len(containers) == 1
        assert containers[0].name == "job-container"

    def test_parse_workload_spec_containers_with_ignored_containers(self):
        """Test parsing workload spec containers while ignoring system containers."""
        workload_spec = {
            "containers": [
                {"name": "cpln-mounter", "image": "system:latest"},  # Should be ignored
                {"name": "spec-container", "image": "spec:latest"},
            ]
        }

        containers = ContainerParser.parse_workload_spec_containers(
            workload_spec, "test-workload", "test-gvc", "us-east"
        )

        # Should only have the spec container, not the system container
        assert len(containers) == 1
        assert containers[0].name == "spec-container"

    def test_parse_deployment_containers_invalid_version_data(self):
        """Test parsing deployment containers with invalid version data."""
        deployment_data = {
            "status": {
                "versions": [
                    "invalid_version_data",  # Not a dict
                    {"no_containers": True},  # Missing containers
                    {"containers": {"valid-container": {"image": "valid:latest"}}},
                ]
            },
            "metadata": {"name": "test-deployment"},
        }

        containers = ContainerParser.parse_deployment_containers(
            deployment_data, "test-workload", "test-gvc", "us-east"
        )

        # Should only parse the valid container
        assert len(containers) == 1
        assert containers[0].name == "valid-container"

    def test_parse_job_containers_invalid_container_data(self):
        """Test parsing job containers with invalid container data."""
        job_data = {
            "spec": {
                "job": {
                    "containers": [
                        "invalid_container_data",  # Not a dict
                        {"name": "valid-container", "image": "valid:latest"},
                    ]
                }
            }
        }

        containers = ContainerParser.parse_job_containers(
            job_data, "test-workload", "test-gvc", "us-east"
        )

        # Should only parse the valid container
        assert len(containers) == 1
        assert containers[0].name == "valid-container"

    def test_parse_workload_spec_containers_invalid_container_data(self):
        """Test parsing workload spec containers with invalid container data."""
        workload_spec = {
            "containers": [
                "invalid_container_data",  # Not a dict
                {"name": "valid-container", "image": "valid:latest"},
            ]
        }

        containers = ContainerParser.parse_workload_spec_containers(
            workload_spec, "test-workload", "test-gvc", "us-east"
        )

        # Should only parse the valid container
        assert len(containers) == 1
        assert containers[0].name == "valid-container"


class TestContainerCollectionAdvanced:
    def test_get_workload_containers_exception_handling(self):
        """Test exception handling in _get_workload_containers."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        # Mock the API to raise a non-APIError exception for deployment
        client.api.get_workload.return_value = {"spec": {"defaultOptions": {}}}
        client.api.get_workload_deployment.side_effect = ValueError("Unexpected error")

        config = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="us-east", specs={}
        )

        # Should handle the exception gracefully and return empty list
        containers = collection._get_workload_containers(config)
        assert containers == []

    def test_infer_workload_locations_with_specified_locations(self):
        """Test inferring workload locations when locations are specified."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        workload_data = {
            "spec": {
                "defaultOptions": {
                    "locations": ["custom-location-1", "custom-location-2"]
                }
            }
        }

        locations = collection._infer_workload_locations(workload_data)
        assert locations == ["custom-location-1", "custom-location-2"]

    def test_infer_workload_locations_without_specified_locations(self):
        """Test inferring workload locations when no locations are specified."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        workload_data = {"spec": {"defaultOptions": {}}}

        locations = collection._infer_workload_locations(workload_data)
        # Should return common locations
        assert "aws-us-east-1" in locations
        assert "aws-us-west-2" in locations
        assert len(locations) == 5

    def test_get_workload_containers_with_retry_no_retry(self):
        """Test workload containers retrieval without retry."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        options = AdvancedListingOptions(enable_retry=False)
        config = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="us-east", specs={}
        )

        with mock.patch.object(collection, "_get_workload_containers") as mock_get:
            mock_get.return_value = [mock.Mock()]

            result = collection._get_workload_containers_with_retry(
                config, None, options
            )

            mock_get.assert_called_once_with(config, None)
            assert len(result) == 1

    def test_get_workload_containers_with_retry_rate_limit(self):
        """Test workload containers retrieval with rate limit retry."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        options = AdvancedListingOptions(
            enable_retry=True,
            max_retries=2,
            retry_delay_seconds=0.1,
            retry_backoff_factor=2.0,
        )
        config = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="us-east", specs={}
        )

        with mock.patch.object(
            collection, "_get_workload_containers"
        ) as mock_get, mock.patch("time.sleep") as mock_sleep:
            # First call raises rate limit error, second succeeds
            mock_get.side_effect = [
                APIError("Rate limit exceeded", None),
                [mock.Mock()],
            ]

            result = collection._get_workload_containers_with_retry(
                config, None, options
            )

            assert mock_get.call_count == 2
            mock_sleep.assert_called_once_with(0.1)
            assert len(result) == 1

    def test_get_workload_containers_with_retry_non_retryable_error(self):
        """Test workload containers retrieval with non-retryable error."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        options = AdvancedListingOptions(enable_retry=True, max_retries=2)
        config = WorkloadConfig(
            gvc="test-gvc", workload_id="test-workload", location="us-east", specs={}
        )

        with mock.patch.object(collection, "_get_workload_containers") as mock_get:
            mock_get.side_effect = APIError("Not found", None)

            with pytest.raises(APIError, match="Not found"):
                collection._get_workload_containers_with_retry(config, None, options)

            # Should not retry for non-rate-limit errors
            assert mock_get.call_count == 1

    def test_apply_pagination_with_max_results(self):
        """Test pagination with max_results."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        containers = [mock.Mock() for _ in range(10)]
        options = AdvancedListingOptions(max_results=5)

        result = collection._apply_pagination(containers, options)
        assert len(result) == 5

    def test_apply_pagination_without_max_results(self):
        """Test pagination without max_results."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        containers = [mock.Mock() for _ in range(10)]
        options = AdvancedListingOptions(max_results=None)

        result = collection._apply_pagination(containers, options)
        assert len(result) == 10

    def test_generate_cache_key_all_params(self):
        """Test cache key generation with all parameters."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        key = collection._generate_cache_key("test-gvc", "us-east", "test-workload")
        assert key == "test-gvc|loc:us-east|wl:test-workload"

    def test_generate_cache_key_partial_params(self):
        """Test cache key generation with partial parameters."""
        client = mock.Mock()
        collection = ContainerCollection(client)

        key = collection._generate_cache_key("test-gvc", "us-east", None)
        assert key == "test-gvc|loc:us-east"

        key = collection._generate_cache_key("test-gvc", None, "test-workload")
        assert key == "test-gvc|wl:test-workload"

        key = collection._generate_cache_key("test-gvc", None, None)
        assert key == "test-gvc"
