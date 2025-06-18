import unittest

from cpln.client import CPLNClient
from cpln.models.gvcs import GVCCollection
from cpln.models.images import ImageCollection
from cpln.models.workloads import WorkloadCollection


class TestCPLNClientIntegration(unittest.TestCase):
    """Test CPLNClient integration with all collections including containers"""

    def setUp(self) -> None:
        """Set up test client"""
        # Mock the API client to avoid real API calls
        with unittest.mock.patch("cpln.client.APIClient"):
            self.client = CPLNClient(
                base_url="https://api.example.com", org="test-org", token="test-token"
            )

    def test_client_has_all_collections(self) -> None:
        """Test that client has all expected collection properties"""
        # Test that all collection properties exist
        self.assertTrue(hasattr(self.client, "gvcs"))
        self.assertTrue(hasattr(self.client, "images"))
        self.assertTrue(hasattr(self.client, "workloads"))

    def test_collection_types(self) -> None:
        """Test that collection properties return correct types"""
        self.assertIsInstance(self.client.gvcs, GVCCollection)
        self.assertIsInstance(self.client.images, ImageCollection)
        self.assertIsInstance(self.client.workloads, WorkloadCollection)

    def test_collection_client_references(self) -> None:
        """Test that collections have correct client references"""
        self.assertEqual(self.client.gvcs.client, self.client)
        self.assertEqual(self.client.images.client, self.client)
        self.assertEqual(self.client.workloads.client, self.client)

    def test_client_initialization_from_env(self) -> None:
        """Test client initialization from environment"""
        # Mock environment variables and APIClient
        env_vars = {
            "CPLN_TOKEN": "env-token",
            "CPLN_ORG": "env-org",
            "CPLN_BASE_URL": "https://api.env.com",
        }

        with (
            unittest.mock.patch.dict("os.environ", env_vars),
            unittest.mock.patch("cpln.client.APIClient"),
        ):
            client = CPLNClient.from_env()

            # Test that collections are properly initialized
            self.assertIsInstance(client.gvcs, GVCCollection)
            self.assertEqual(client.gvcs.client, client)


if __name__ == "__main__":
    unittest.main()
