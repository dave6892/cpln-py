import os
from unittest.mock import Mock

import pytest
import requests
from cpln.api.client import APIClient
from cpln.api.config import APIConfig


@pytest.fixture
def mock_config() -> Mock:
    """
    Return a mock APIConfig object for testing with properly configured properties.

    This provides a mock configuration object with default values for the base URL,
    organization name, and API token that can be used in tests.
    """
    mock = Mock(spec=APIConfig)
    mock.base_url = os.getenv("CPLN_BASE_URL", "https://api.cpln.io")
    mock.org = os.getenv("CPLN_ORG", "ledgestone")
    mock.token = (
        os.getenv("CPLN_TOKEN") or "mock-token"
    )  # default mock token if not set

    # Generate the org_url property
    mock.org_url = f"{mock.base_url}/org/{mock.org}"

    return mock


@pytest.fixture
def mock_api_client(mock_config: Mock) -> APIClient:
    """
    Create a properly mocked APIClient for testing.

    This fixture:
    1. Creates mock response objects for each HTTP method
    2. Sets up default successful responses
    3. Creates mock HTTP methods that return the mock responses
    4. Replaces the requests.Session HTTP methods with our mocks
    5. Stores both the mock methods and responses on the client for easy access in tests
    """
    # Create the mock response objects
    mock_get_response = Mock(spec=requests.Response)
    mock_post_response = Mock(spec=requests.Response)
    mock_patch_response = Mock(spec=requests.Response)
    mock_delete_response = Mock(spec=requests.Response)

    # Set up default successful responses
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {"data": "test"}

    mock_post_response.status_code = 201
    mock_post_response.json.return_value = {"data": "test"}

    mock_patch_response.status_code = 200
    mock_patch_response.json.return_value = {"data": "test"}

    mock_delete_response.status_code = 204

    # Create mock methods
    mock_get = Mock(return_value=mock_get_response)
    mock_post = Mock(return_value=mock_post_response)
    mock_patch = Mock(return_value=mock_patch_response)
    mock_delete = Mock(return_value=mock_delete_response)

    # Create the client with the mock config
    client = APIClient(config=mock_config)

    # Replace the requests.Session methods with our mocks
    client.get = mock_get  # type: ignore
    client.post = mock_post  # type: ignore
    client.patch = mock_patch  # type: ignore
    client.delete = mock_delete  # type: ignore

    # Store mocks on the client for access in tests
    client._mock_get = mock_get
    client._mock_post = mock_post
    client._mock_patch = mock_patch
    client._mock_delete = mock_delete

    # Store responses for direct access in tests
    client._mock_get_response = mock_get_response
    client._mock_post_response = mock_post_response
    client._mock_patch_response = mock_patch_response
    client._mock_delete_response = mock_delete_response

    return client
