"""Tests for API client following unit testing best practices."""

import os
import unittest
from unittest.mock import Mock, patch

import requests
from cpln.api.client import APIClient
from cpln.api.config import APIConfig
from cpln.config import WorkloadConfig
from cpln.errors import APIError
from cpln.exceptions import NotFound


class TestAPIClientInitialization(unittest.TestCase):
    """Test APIClient initialization and basic properties"""

    def test_api_client_initialization_with_config_sets_attributes_correctly(self):
        """Test that APIClient initializes correctly with provided config"""
        # Arrange
        mock_config = Mock(spec=APIConfig)
        mock_config.base_url = "https://api.cpln.io"
        mock_config.org = "test-org"
        mock_config.token = "test-token"

        # Act
        client = APIClient(config=mock_config)

        # Assert
        self.assertEqual(client.config, mock_config)
        self.assertEqual(client.config.base_url, "https://api.cpln.io")
        self.assertEqual(client.config.org, "test-org")
        self.assertEqual(client.config.token, "test-token")

    def test_api_client_headers_property_returns_correct_authorization(self):
        """Test that _headers property returns correct Authorization header"""
        # Arrange
        test_token = "test-bearer-token"
        mock_config = Mock(spec=APIConfig)
        mock_config.token = test_token
        client = APIClient(config=mock_config)

        # Act
        headers = client._headers

        # Assert
        expected_headers = {"Authorization": f"Bearer {test_token}"}
        self.assertEqual(headers, expected_headers)

    def test_api_client_initialization_with_environment_config_uses_env_values(self):
        """Test that APIClient works with environment-based config"""
        # Arrange
        with patch.dict(
            os.environ,
            {
                "CPLN_BASE_URL": "https://test-api.cpln.io",
                "CPLN_ORG": "test-env-org",
                "CPLN_TOKEN": "test-env-token",
            },
        ):
            mock_config = Mock(spec=APIConfig)
            mock_config.base_url = os.getenv("CPLN_BASE_URL")
            mock_config.org = os.getenv("CPLN_ORG")
            mock_config.token = os.getenv("CPLN_TOKEN")

            # Act
            client = APIClient(config=mock_config)

            # Assert
            self.assertEqual(client.config.base_url, "https://test-api.cpln.io")
            self.assertEqual(client.config.org, "test-env-org")
            self.assertEqual(client.config.token, "test-env-token")


class TestAPIClientGVCOperations(unittest.TestCase):
    """Test APIClient GVC operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_config = Mock(spec=APIConfig)
        self.mock_config.base_url = "https://api.cpln.io"
        self.mock_config.org = "test-org"
        self.mock_config.token = "test-token"

        self.client = APIClient(config=self.mock_config)

        # Create mock responses
        self.mock_get_response = Mock(spec=requests.Response)
        self.mock_delete_response = Mock(spec=requests.Response)

        # Create and assign mock HTTP methods
        self.mock_get = Mock(return_value=self.mock_get_response)
        self.mock_delete = Mock(return_value=self.mock_delete_response)

        self.client.get = self.mock_get  # type: ignore
        self.client.delete = self.mock_delete  # type: ignore

    def test_get_gvc_with_successful_response_returns_json_data(self):
        """Test that get_gvc() returns JSON data for successful response"""
        # Arrange
        expected_data = {"name": "test-gvc", "status": "active"}
        self.mock_get_response.status_code = 200
        self.mock_get_response.json.return_value = expected_data

        # Act
        result = self.client.get_gvc()

        # Assert
        self.assertEqual(result, expected_data)
        expected_url = f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc"
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_get.assert_called_once_with(expected_url, headers=expected_headers)

    def test_get_gvc_with_specific_name_includes_name_in_url(self):
        """Test that get_gvc(name) includes the name in the API URL"""
        # Arrange
        gvc_name = "production-gvc"
        expected_data = {"name": gvc_name}
        self.mock_get_response.status_code = 200
        self.mock_get_response.json.return_value = expected_data

        # Act
        result = self.client.get_gvc(gvc_name)

        # Assert
        self.assertEqual(result, expected_data)
        expected_url = (
            f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc/{gvc_name}"
        )
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_get.assert_called_once_with(expected_url, headers=expected_headers)

    def test_get_gvc_with_404_response_raises_not_found_exception(self):
        """Test that get_gvc() raises NotFound for 404 response"""
        # Arrange
        self.mock_get_response.status_code = 404
        self.mock_get_response.text = "GVC not found"

        # Act & Assert
        with self.assertRaises(NotFound):
            self.client.get_gvc()

        expected_url = f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc"
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_get.assert_called_once_with(expected_url, headers=expected_headers)

    def test_get_gvc_with_500_response_raises_api_error_exception(self):
        """Test that get_gvc() raises APIError for server errors"""
        # Arrange
        self.mock_get_response.status_code = 500
        self.mock_get_response.text = "Internal Server Error"

        # Act & Assert
        with self.assertRaises(APIError):
            self.client.get_gvc()

        expected_url = f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc"
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_get.assert_called_once_with(expected_url, headers=expected_headers)

    def test_delete_gvc_with_successful_response_returns_response_object(self):
        """Test that delete_gvc() returns response object for successful deletion"""
        # Arrange
        gvc_name = "test-gvc-to-delete"
        self.mock_delete_response.status_code = 204

        # Act
        result = self.client.delete_gvc(gvc_name)

        # Assert
        self.assertEqual(result, self.mock_delete_response)
        expected_url = (
            f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc/{gvc_name}"
        )
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_delete.assert_called_once_with(expected_url, headers=expected_headers)

    def test_delete_gvc_with_404_response_raises_not_found_exception(self):
        """Test that delete_gvc() raises NotFound for non-existent GVC"""
        # Arrange
        gvc_name = "nonexistent-gvc"
        self.mock_delete_response.status_code = 404
        self.mock_delete_response.text = "GVC not found"

        # Act & Assert
        with self.assertRaises(NotFound):
            self.client.delete_gvc(gvc_name)

        expected_url = (
            f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc/{gvc_name}"
        )
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_delete.assert_called_once_with(expected_url, headers=expected_headers)


class TestAPIClientImageOperations(unittest.TestCase):
    """Test APIClient Image operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_config = Mock(spec=APIConfig)
        self.mock_config.base_url = "https://api.cpln.io"
        self.mock_config.org = "test-org"
        self.mock_config.token = "test-token"

        self.client = APIClient(config=self.mock_config)

        # Create and assign mock GET method
        self.mock_get_response = Mock(spec=requests.Response)
        self.mock_get = Mock(return_value=self.mock_get_response)
        self.client.get = self.mock_get  # type: ignore

    def test_get_image_with_successful_response_returns_json_data(self):
        """Test that get_image() returns JSON data for successful response"""
        # Arrange
        expected_data = {"name": "nginx", "tag": "latest", "status": "active"}
        self.mock_get_response.status_code = 200
        self.mock_get_response.json.return_value = expected_data

        # Act
        result = self.client.get_image()

        # Assert
        self.assertEqual(result, expected_data)
        expected_url = f"{self.mock_config.base_url}/org/{self.mock_config.org}/image"
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_get.assert_called_once_with(expected_url, headers=expected_headers)

    def test_get_image_with_specific_name_includes_name_in_url(self):
        """Test that get_image(name) includes the name in the API URL"""
        # Arrange
        image_name = "nginx-production"
        expected_data = {"name": image_name, "tag": "v1.21"}
        self.mock_get_response.status_code = 200
        self.mock_get_response.json.return_value = expected_data

        # Act
        result = self.client.get_image(image_name)

        # Assert
        self.assertEqual(result, expected_data)
        expected_url = (
            f"{self.mock_config.base_url}/org/{self.mock_config.org}/image/{image_name}"
        )
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_get.assert_called_once_with(expected_url, headers=expected_headers)


class TestAPIClientWorkloadOperations(unittest.TestCase):
    """Test APIClient Workload operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_config = Mock(spec=APIConfig)
        self.mock_config.base_url = "https://api.cpln.io"
        self.mock_config.org = "test-org"
        self.mock_config.token = "test-token"

        self.client = APIClient(config=self.mock_config)

        # Create mock responses
        self.mock_patch_response = Mock(spec=requests.Response)

        # Create and assign mock HTTP methods
        self.mock_patch = Mock(return_value=self.mock_patch_response)
        self.client.patch = self.mock_patch  # type: ignore

    def test_patch_workload_with_successful_response_returns_response_object(self):
        """Test that patch_workload() returns response object for successful update"""
        # Arrange
        workload_config = WorkloadConfig(gvc="test-gvc", workload_id="test-workload")
        test_data = {
            "spec": {"containers": [{"name": "app", "cpu": "200m", "memory": 512}]}
        }
        self.mock_patch_response.status_code = 200

        # Act
        result = self.client.patch_workload(config=workload_config, data=test_data)

        # Assert
        self.assertEqual(result, self.mock_patch_response)
        expected_url = f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc/{workload_config.gvc}/workload/{workload_config.workload_id}"
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_patch.assert_called_once_with(
            expected_url, json=test_data, headers=expected_headers
        )

    def test_patch_workload_with_400_response_raises_api_error_exception(self):
        """Test that patch_workload() raises APIError for bad requests"""
        # Arrange
        workload_config = WorkloadConfig(gvc="test-gvc", workload_id="test-workload")
        invalid_data = {"invalid": "data"}
        self.mock_patch_response.status_code = 400
        self.mock_patch_response.text = "Bad Request"

        # Act & Assert
        with self.assertRaises(APIError):
            self.client.patch_workload(config=workload_config, data=invalid_data)

        expected_url = f"{self.mock_config.base_url}/org/{self.mock_config.org}/gvc/{workload_config.gvc}/workload/{workload_config.workload_id}"
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_patch.assert_called_once_with(
            expected_url, json=invalid_data, headers=expected_headers
        )

    def test_patch_workload_with_404_response_raises_not_found_exception(self):
        """Test that patch_workload() raises NotFound for non-existent workload"""
        # Arrange
        workload_config = WorkloadConfig(
            gvc="nonexistent-gvc", workload_id="nonexistent-workload"
        )
        test_data = {"spec": {"suspend": True}}
        self.mock_patch_response.status_code = 404

        # Act & Assert
        with self.assertRaises(NotFound):
            self.client.patch_workload(config=workload_config, data=test_data)


class TestAPIClientPostOperations(unittest.TestCase):
    """Test APIClient POST operations"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_config = Mock(spec=APIConfig)
        self.mock_config.base_url = "https://api.cpln.io"
        self.mock_config.org = "test-org"
        self.mock_config.token = "test-token"

        self.client = APIClient(config=self.mock_config)

        # Create and assign mock POST method
        self.mock_post_response = Mock(spec=requests.Response)
        self.mock_post = Mock(return_value=self.mock_post_response)
        self.client.post = self.mock_post  # type: ignore

    def test_post_with_successful_response_returns_response_object(self):
        """Test that _post() returns response object for successful creation"""
        # Arrange
        endpoint = "test-endpoint"
        test_data = {"name": "test-resource", "description": "Test resource"}
        self.mock_post_response.status_code = 201

        # Act
        result = self.client._post(endpoint, test_data)

        # Assert
        self.assertEqual(result, self.mock_post_response)
        expected_url = (
            f"{self.mock_config.base_url}/org/{self.mock_config.org}/{endpoint}"
        )
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_post.assert_called_once_with(
            expected_url, json=test_data, headers=expected_headers
        )

    def test_post_with_422_response_raises_api_error_with_json_message(self):
        """Test that _post() raises APIError with JSON error message for validation errors"""
        # Arrange
        endpoint = "test-endpoint"
        test_data = {"invalid": "data"}
        self.mock_post_response.status_code = 422
        self.mock_post_response.text = "Unprocessable Entity"
        self.mock_post_response.json.return_value = {"error": "Validation failed"}

        # Act & Assert
        with self.assertRaises(APIError):
            self.client._post(endpoint, test_data)

        expected_url = (
            f"{self.mock_config.base_url}/org/{self.mock_config.org}/{endpoint}"
        )
        expected_headers = {"Authorization": f"Bearer {self.mock_config.token}"}
        self.mock_post.assert_called_once_with(
            expected_url, json=test_data, headers=expected_headers
        )

    def test_post_with_400_response_and_invalid_json_falls_back_to_text(self):
        """Test that _post() falls back to text error message when JSON parsing fails"""
        # Arrange
        endpoint = "test-endpoint"
        test_data = {"invalid": "data"}
        self.mock_post_response.status_code = 400
        self.mock_post_response.text = "Bad Request - Custom Error"
        self.mock_post_response.json.side_effect = ValueError("Invalid JSON")

        # Act & Assert
        with self.assertRaises(APIError) as context:
            self.client._post(endpoint, test_data)

        # Should contain the text error message
        self.assertIn("Bad Request - Custom Error", str(context.exception))


class TestAPIClientErrorHandling(unittest.TestCase):
    """Test APIClient error handling and edge cases"""

    def setUp(self):
        """Set up common test fixtures"""
        self.mock_config = Mock(spec=APIConfig)
        self.mock_config.base_url = "https://api.cpln.io"
        self.mock_config.org = "test-org"
        self.mock_config.token = "test-token"

        self.client = APIClient(config=self.mock_config)

    def test_api_client_handles_network_errors_gracefully(self):
        """Test that APIClient handles network-level errors"""
        # Arrange
        mock_get = Mock(side_effect=requests.ConnectionError("Network error"))
        self.client.get = mock_get  # type: ignore

        # Act & Assert
        with self.assertRaises(requests.ConnectionError):
            self.client.get_gvc()

    def test_api_client_handles_timeout_errors_gracefully(self):
        """Test that APIClient handles timeout errors"""
        # Arrange
        mock_get = Mock(side_effect=requests.Timeout("Request timeout"))
        self.client.get = mock_get  # type: ignore

        # Act & Assert
        with self.assertRaises(requests.Timeout):
            self.client.get_gvc()

    def test_api_client_with_empty_config_values_constructs_correct_urls(self):
        """Test that APIClient constructs URLs correctly even with minimal config"""
        # Arrange
        minimal_config = Mock(spec=APIConfig)
        minimal_config.base_url = "https://minimal-api.cpln.io"
        minimal_config.org = "minimal-org"
        minimal_config.token = "minimal-token"

        client = APIClient(config=minimal_config)
        mock_get_response = Mock(spec=requests.Response)
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"data": "minimal"}

        mock_get = Mock(return_value=mock_get_response)
        client.get = mock_get  # type: ignore

        # Act
        result = client.get_gvc()

        # Assert
        self.assertEqual(result, {"data": "minimal"})
        expected_url = "https://minimal-api.cpln.io/org/minimal-org/gvc"
        expected_headers = {"Authorization": "Bearer minimal-token"}
        mock_get.assert_called_once_with(expected_url, headers=expected_headers)


if __name__ == "__main__":
    unittest.main()  # type: ignore
