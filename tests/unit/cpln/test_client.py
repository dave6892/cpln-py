import os
import unittest
from unittest.mock import patch

from cpln.client import CPLNClient
from cpln.models.gvcs import GVCCollection
from cpln.models.images import ImageCollection
from cpln.models.resource import Collection
from cpln.models.workloads import WorkloadCollection


class TestCPLNClientIntegration(unittest.TestCase):
    """Test CPLNClient integration with collection properties and initialization methods"""

    def setUp(self) -> None:
        """Set up test client with mocked dependencies"""
        self.test_config = {
            "base_url": "https://api.example.com",
            "org": "test-org",
            "token": "test-token",
        }

        self.api_client_patcher = patch("cpln.client.APIClient")
        self.mock_api_client = self.api_client_patcher.start()

        self.client = CPLNClient(**self.test_config)

    def tearDown(self) -> None:
        """Clean up patches"""
        self.api_client_patcher.stop()

    def _shared_function_for_testing_configured_collection(
        self, collection: Collection, collection_type: type[Collection]
    ) -> None:
        """Shared function for testing configured collection"""
        self.assertIsInstance(collection, collection_type)
        self.assertEqual(collection.client, self.client)
        self.assertEqual(collection.model, collection_type.model)

    def test_gvcs_property_returns_configured_collection(self) -> None:
        """Test that gvcs property returns a GVCCollection configured with this client"""
        gvcs = self.client.gvcs
        self._shared_function_for_testing_configured_collection(gvcs, GVCCollection)

    def test_images_property_returns_configured_collection(self) -> None:
        """Test that images property returns an ImageCollection configured with this client"""
        images = self.client.images
        self._shared_function_for_testing_configured_collection(images, ImageCollection)

    def test_workloads_property_returns_configured_collection(self) -> None:
        """Test that workloads property returns a WorkloadCollection configured with this client"""
        workloads = self.client.workloads
        self._shared_function_for_testing_configured_collection(
            workloads, WorkloadCollection
        )

    def test_collection_properties_create_new_instances_each_time(self) -> None:
        """Test that collection properties create new instances on each access"""
        gvcs1 = self.client.gvcs
        gvcs2 = self.client.gvcs

        self.assertIsNot(gvcs1, gvcs2)
        self.assertEqual(gvcs1.client, gvcs2.client)

    def test_collections_maintain_client_reference_consistency(self) -> None:
        """Test that all collection instances maintain consistent client references"""
        gvcs = self.client.gvcs
        images = self.client.images
        workloads = self.client.workloads

        self.assertIs(gvcs.client, self.client)
        self.assertIs(images.client, self.client)
        self.assertIs(workloads.client, self.client)

    @patch.dict(
        os.environ,
        {
            "CPLN_TOKEN": "env-token",
            "CPLN_ORG": "env-org",
            "CPLN_BASE_URL": "https://api.env.com",
        },
    )
    @patch("cpln.client.kwargs_from_env")
    def test_from_env_creates_client_with_environment_config(
        self, mock_kwargs_from_env
    ) -> None:
        """Test that from_env class method creates client using environment configuration"""
        expected_config = {
            "base_url": "https://api.env.com",
            "org": "env-org",
            "token": "env-token",
        }
        mock_kwargs_from_env.return_value = expected_config

        client = CPLNClient.from_env()

        mock_kwargs_from_env.assert_called_once()
        self.mock_api_client.assert_called_with(**expected_config)
        self.assertIsInstance(client, CPLNClient)

    @patch("cpln.client.kwargs_from_env")
    def test_from_env_with_additional_kwargs_merges_configurations(
        self, mock_kwargs_from_env
    ) -> None:
        """Test that from_env accepts additional kwargs and passes them to initialization"""
        env_config = {"token": "env-token"}
        additional_kwargs = {"timeout": 30, "retries": 3}
        mock_kwargs_from_env.return_value = env_config

        CPLNClient.from_env(**additional_kwargs)

        mock_kwargs_from_env.assert_called_once_with(**additional_kwargs)
        self.mock_api_client.assert_called_with(**env_config)

    def test_client_initialization_with_minimal_config(self) -> None:
        """Test that client can be initialized with minimal configuration"""
        client = CPLNClient()

        self.mock_api_client.assert_called_with()
        self.assertEqual(client.api, self.mock_api_client.return_value)

    def test_client_initialization_with_extra_kwargs(self) -> None:
        """Test that client passes through additional kwargs to API client"""
        config = {
            "base_url": "https://api.example.com",
            "org": "test-org",
            "timeout": "60",
            "retries": "5",
        }

        CPLNClient(**config)

        self.mock_api_client.assert_called_with(**config)

    def test_client_filters_none_values_from_config(self) -> None:
        """Test that client only passes non-None configuration values to API client"""
        CPLNClient(
            base_url="https://api.example.com",
            org=None,  # Should be filtered out
            token="test-token",
        )

        expected_config = {"base_url": "https://api.example.com", "token": "test-token"}
        self.mock_api_client.assert_called_with(**expected_config)

    @patch("cpln.client.kwargs_from_env")
    def test_from_env_handles_empty_environment(self, mock_kwargs_from_env) -> None:
        """Test that from_env handles cases where no environment variables are set"""
        mock_kwargs_from_env.return_value = {}

        client = CPLNClient.from_env()

        mock_kwargs_from_env.assert_called_once()
        self.mock_api_client.assert_called_with()
        self.assertIsInstance(client, CPLNClient)


if __name__ == "__main__":
    unittest.main()  # type: ignore
