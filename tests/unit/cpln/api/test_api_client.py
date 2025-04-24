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
    mock_response = Mock()
    mock_response.json.return_value = {"data": "test"}
    mock_api_client.get.return_value = mock_response

    result = mock_api_client.get_gvc()

    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc"
    mock_api_client.get.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )
    assert result == {"data": "test"}

def test_api_client_get_image(mock_api_client):
    mock_response = Mock()
    mock_response.json.return_value = {"data": "test"}
    mock_api_client.get.return_value = mock_response

    result = mock_api_client.get_image()

    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/image"
    mock_api_client.get.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )
    assert result == {"data": "test"}

def test_api_client_delete_gvc(mock_api_client):
    mock_response = Mock()
    mock_api_client.delete.return_value = mock_response

    result = mock_api_client.delete_gvc("test-gvc")

    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc/test-gvc"
    mock_api_client.delete.assert_called_once_with(
        expected_url,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )
    assert result == mock_response

def test_api_client_patch_workload(mock_api_client):
    mock_response = Mock()
    mock_api_client.patch.return_value = mock_response
    test_data = {"key": "value"}

    result = mock_api_client.patch_workload(
        config=Mock(gvc="test-gvc", workload_id="test-workload"),
        data=test_data
    )

    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}/gvc/test-gvc/workload/test-workload"
    mock_api_client.patch.assert_called_once_with(
        expected_url,
        json=test_data,
        headers={"Authorization": f"Bearer {os.getenv('CPLN_TOKEN')}"}
    )
    assert result == mock_response
