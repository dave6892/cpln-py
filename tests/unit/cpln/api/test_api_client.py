import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import requests
from cpln.api.client import APIClient
from cpln.api.config import APIConfig
from cpln.errors import NotFound, APIError

def test_api_client_initialization(mock_config):
    client = APIClient(config=mock_config)
    assert client.config == mock_config
    assert client.config.base_url == os.getenv('CPLN_BASE_URL')
    assert client.config.org == os.getenv('CPLN_ORG')
    assert client.config.token == os.getenv('CPLN_TOKEN')

def test_api_client_headers(mock_config):
    client = APIClient(config=mock_config)
    headers = client._headers
    assert headers == {"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}

import pytest
import os
from unittest.mock import Mock, patch
from cpln.api.client import APIClient
from cpln.api.config import APIConfig

def test_api_client_initialization(mock_config):
    client = APIClient(config=mock_config)
    assert client.config == mock_config
    assert client.config.base_url == os.getenv('CPLN_BASE_URL')
    assert client.config.org == os.getenv('CPLN_ORG')
    assert client.config.token == os.getenv('CPLN_TOKEN')

def test_api_client_headers(mock_config):
    client = APIClient(config=mock_config)
    headers = client._headers
    assert headers == {"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}

def test_api_client_get_gvc(mock_api_client):
    # Create a successful response for the session get method
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    # Set the mock response for the session.get method
    mock_api_client.session.get.return_value = mock_response

    # Call the API method
    result = mock_api_client.get_gvc()

    # Verify the session.get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc"
    mock_api_client.session.get.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == {"data": "test"}


def test_api_client_get_gvc_not_found(mock_api_client):
    # Create a 404 response for the session get method
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    # Set the mock response for the session.get method
    mock_api_client.session.get.return_value = mock_response

    # Test that NotFound exception is raised
    with pytest.raises(NotFound):
        mock_api_client.get_gvc()

    # Verify the session.get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc"
    mock_api_client.session.get.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )


def test_api_client_get_gvc_error(mock_api_client):
    # Create a 500 response for the session get method
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    # Set the mock response for the session.get method
    mock_api_client.session.get.return_value = mock_response

    # Test that APIError exception is raised
    with pytest.raises(APIError):
        mock_api_client.get_gvc()

    # Verify the session.get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc"
    mock_api_client.session.get.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

def test_api_client_get_image(mock_api_client):
    # Create a successful response for the session get method
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    # Set the mock response for the session.get method
    mock_api_client.session.get.return_value = mock_response

    # Call the API method
    result = mock_api_client.get_image()

    # Verify the session.get method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/image"
    mock_api_client.session.get.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == {"data": "test"}

def test_api_client_delete_gvc(mock_api_client):
    # Create a successful response for the session delete method
    mock_response = Mock()
    mock_response.status_code = 204  # Success status code for DELETE

    # Set the mock response for the session.delete method
    mock_api_client.session.delete.return_value = mock_response

    # Call the API method
    result = mock_api_client.delete_gvc("test-gvc")

    # Verify the session.delete method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc/test-gvc"
    mock_api_client.session.delete.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == mock_response


def test_api_client_delete_gvc_not_found(mock_api_client):
    # Create a 404 response for the session delete method
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    # Set the mock response for the session.delete method
    mock_api_client.session.delete.return_value = mock_response

    # Test that NotFound exception is raised
    with pytest.raises(NotFound):
        mock_api_client.delete_gvc("nonexistent-gvc")

    # Verify the session.delete method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc/nonexistent-gvc"
    mock_api_client.session.delete.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

def test_api_client_patch_workload(mock_api_client):
    # Create a successful response for the session patch method
    mock_response = Mock()
    mock_response.status_code = 200

    # Set the mock response for the session.patch method
    mock_api_client.session.patch.return_value = mock_response

    # Test data
    test_data = {"key": "value"}

    # Create a mock workload config
    mock_config = Mock()
    mock_config.gvc = "test-gvc"
    mock_config.workload_id = "test-workload"

    # Call the API method
    result = mock_api_client.patch_workload(
        config=mock_config,
        data=test_data
    )

    # Verify the session.patch method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc/test-gvc/workload/test-workload"
    mock_api_client.session.patch.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == mock_response


def test_api_client_patch_workload_error(mock_api_client):
    # Create an error response for the session patch method
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"

    # Set the mock response for the session.patch method
    mock_api_client.session.patch.return_value = mock_response

    # Test data
    test_data = {"invalid": "data"}

    # Create a mock workload config
    mock_config = Mock()
    mock_config.gvc = "test-gvc"
    mock_config.workload_id = "test-workload"

    # Test that APIError exception is raised
    with pytest.raises(APIError):
        mock_api_client.patch_workload(
            config=mock_config,
            data=test_data
        )

    # Verify the session.patch method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc/test-gvc/workload/test-workload"
    mock_api_client.session.patch.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )


def test_api_client_post(mock_api_client):
    # Create a successful response for the session post method
    mock_response = Mock()
    mock_response.status_code = 201  # Success status code for POST

    # Set the mock response for the session.post method
    mock_api_client.session.post.return_value = mock_response

    # Test data
    test_data = {"name": "test-resource"}

    # Call the internal API method
    result = mock_api_client._post("test-endpoint", test_data)

    # Verify the session.post method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/test-endpoint"
    mock_api_client.session.post.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )

    # Verify the result
    assert result == mock_response


def test_api_client_post_error(mock_api_client):
    # Create an error response for the session post method
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"
    # Provide a json method that will be called in error handling
    mock_response.json.return_value = {"error": "Validation failed"}

    # Set the mock response for the session.post method
    mock_api_client.session.post.return_value = mock_response

    # Test data
    test_data = {"invalid": "data"}

    # Test that APIError exception is raised
    with pytest.raises(APIError):
        mock_api_client._post("test-endpoint", test_data)

    # Verify the session.post method was called with the correct arguments
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/test-endpoint"
    mock_api_client.session.post.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )
