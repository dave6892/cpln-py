import os
from unittest.mock import Mock

import pytest
from cpln.api.client import APIClient
from cpln.errors import APIError, NotFound


def test_api_client_initialization(mock_config):
    client = APIClient(config=mock_config)
    assert client.config == mock_config
    assert client.config.base_url == os.getenv("CPLN_BASE_URL")
    assert client.config.org == os.getenv("CPLN_ORG")
    assert client.config.token == os.getenv("CPLN_TOKEN")


def test_api_client_headers(mock_config):
    client = APIClient(config=mock_config)
    headers = client._headers
    assert headers == {"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}


def test_api_client_get_gvc(mock_api_client):
    # Mock response is already set up in the fixture
    mock_api_client._mock_get_response.status_code = 200
    mock_api_client._mock_get_response.json.return_value = {"data": "test"}

    # Call the API method
    result = mock_api_client.get_gvc()

    # Verify the get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/gvc"
    mock_api_client._mock_get.assert_called_once_with(
        expected_url, headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == {"data": "test"}


def test_api_client_get_gvc_not_found(mock_api_client):
    # Set up the mock response for 404
    mock_api_client._mock_get_response.status_code = 404
    mock_api_client._mock_get_response.text = "Not Found"

    # Test that NotFound exception is raised
    with pytest.raises(NotFound):
        mock_api_client.get_gvc()

    # Verify the get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/gvc"
    mock_api_client._mock_get.assert_called_once_with(
        expected_url, headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )


def test_api_client_get_gvc_error(mock_api_client):
    # Set up the mock response for 500
    mock_api_client._mock_get_response.status_code = 500
    mock_api_client._mock_get_response.text = "Internal Server Error"

    # Test that APIError exception is raised
    with pytest.raises(APIError):
        mock_api_client.get_gvc()

    # Verify the get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/gvc"
    mock_api_client._mock_get.assert_called_once_with(
        expected_url, headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )


def test_api_client_get_image(mock_api_client):
    # Set up the mock response
    mock_api_client._mock_get_response.status_code = 200
    mock_api_client._mock_get_response.json.return_value = {"data": "test"}

    # Call the API method
    result = mock_api_client.get_image()

    # Verify the get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/image"
    mock_api_client._mock_get.assert_called_once_with(
        expected_url, headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == {"data": "test"}


def test_api_client_delete_gvc(mock_api_client):
    # Set up the mock response for successful delete
    mock_api_client._mock_delete_response.status_code = (
        204  # Success status code for DELETE
    )

    # Call the API method
    result = mock_api_client.delete_gvc("test-gvc")

    # Verify the delete method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/gvc/test-gvc"
    mock_api_client._mock_delete.assert_called_once_with(
        expected_url, headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == mock_api_client._mock_delete_response


def test_api_client_delete_gvc_not_found(mock_api_client):
    # Set up the mock response for 404
    mock_api_client._mock_delete_response.status_code = 404
    mock_api_client._mock_delete_response.text = "Not Found"

    # Test that NotFound exception is raised
    with pytest.raises(NotFound):
        mock_api_client.delete_gvc("nonexistent-gvc")

    # Verify the delete method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/gvc/nonexistent-gvc"
    mock_api_client._mock_delete.assert_called_once_with(
        expected_url, headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )


def test_api_client_patch_workload(mock_api_client):
    # Set up the mock response for successful patch
    mock_api_client._mock_patch_response.status_code = 200

    # Test data
    test_data = {"key": "value"}

    # Create a mock workload config
    mock_config = Mock()
    mock_config.gvc = "test-gvc"
    mock_config.workload_id = "test-workload"

    # Call the API method
    result = mock_api_client.patch_workload(config=mock_config, data=test_data)

    # Verify the patch method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/gvc/test-gvc/workload/test-workload"
    mock_api_client._mock_patch.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"},
    )

    # Verify the result
    assert result == mock_api_client._mock_patch_response


def test_api_client_patch_workload_error(mock_api_client):
    # Set up the mock response for error
    mock_api_client._mock_patch_response.status_code = 400
    mock_api_client._mock_patch_response.text = "Bad Request"

    # Test data
    test_data = {"invalid": "data"}

    # Create a mock workload config
    mock_config = Mock()
    mock_config.gvc = "test-gvc"
    mock_config.workload_id = "test-workload"

    # Test that APIError exception is raised
    with pytest.raises(APIError):
        mock_api_client.patch_workload(config=mock_config, data=test_data)

    # Verify the patch method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/gvc/test-gvc/workload/test-workload"
    mock_api_client._mock_patch.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"},
    )


def test_api_client_post(mock_api_client):
    # Set up the mock response for successful post
    mock_api_client._mock_post_response.status_code = (
        201  # Success status code for POST
    )

    # Test data
    test_data = {"name": "test-resource"}

    # Call the internal API method
    result = mock_api_client._post("test-endpoint", test_data)

    # Verify the post method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/test-endpoint"
    mock_api_client._mock_post.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"},
    )

    # Verify the result
    assert result == mock_api_client._mock_post_response


def test_api_client_post_error(mock_api_client):
    # Set up the mock response for error
    mock_api_client._mock_post_response.status_code = 422
    mock_api_client._mock_post_response.text = "Unprocessable Entity"
    # Provide a json method that will be called in error handling
    mock_api_client._mock_post_response.json.return_value = {
        "error": "Validation failed"
    }

    # Test data
    test_data = {"invalid": "data"}

    # Test that APIError exception is raised
    with pytest.raises(APIError):
        mock_api_client._post("test-endpoint", test_data)

    # Verify the post method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}/org/{os.getenv('CPLN_ORG', 'ledgestone')}/test-endpoint"
    mock_api_client._mock_post.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"},
    )


def test_api_client_post_error_invalid_json(mock_api_client):
    # Set up the mock response for error with invalid JSON
    mock_api_client._mock_post_response.status_code = 400
    mock_api_client._mock_post_response.text = "Bad Request"
    # Make json() method raise an exception
    mock_api_client._mock_post_response.json.side_effect = ValueError("Invalid JSON")

    # Test data
    test_data = {"invalid": "data"}

    # Test that APIError exception is raised
    with pytest.raises(APIError) as exc_info:
        mock_api_client._post("test-endpoint", test_data)

    # Should fall back to text error message
    assert "Bad Request" in str(exc_info.value)


def test_api_client_patch_not_found(mock_api_client):
    # Set up the mock response for 404
    mock_api_client._mock_patch_response.status_code = 404

    # Create a mock workload config
    mock_config = Mock()
    mock_config.gvc = "test-gvc"
    mock_config.workload_id = "test-workload"

    # Test that NotFound exception is raised
    with pytest.raises(NotFound):
        mock_api_client.patch_workload(config=mock_config, data={})
