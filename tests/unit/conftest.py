import os
from pathlib import Path
from typing import Dict, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from cpln import CPLNClient
from cpln.api.client import APIClient
from cpln.api.config import APIConfig
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)


@pytest.fixture(autouse=True)
def mock_env_vars() -> Generator[None, None, None]:
    # Only override if not set in .env
    env_vars: Dict[str, str] = {
        "CPLN_TOKEN": os.getenv("CPLN_TOKEN", "test-token"),
        "CPLN_ORG": os.getenv("CPLN_ORG", "test-org"),
        "CPLN_BASE_URL": os.getenv("CPLN_BASE_URL", "https://api.cpln.io"),
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_config() -> APIConfig:
    return APIConfig(
        base_url=os.getenv("CPLN_BASE_URL"),
        org=os.getenv("CPLN_ORG"),
        token=os.getenv("CPLN_TOKEN"),
    )


@pytest.fixture
def mock_session() -> MagicMock:
    """
    Create a mock session with appropriate response behaviors.
    """
    mock_session: MagicMock = MagicMock(spec=requests.Session)

    # Set up default responses for HTTP methods
    get_response: Mock = Mock()
    get_response.status_code = 200
    get_response.json.return_value = {}
    mock_session.get.return_value = get_response

    post_response: Mock = Mock()
    post_response.status_code = 201
    post_response.json.return_value = {}
    post_response.text = "Created"
    mock_session.post.return_value = post_response

    patch_response: Mock = Mock()
    patch_response.status_code = 200
    patch_response.json.return_value = {}
    patch_response.text = "OK"
    mock_session.patch.return_value = patch_response

    delete_response: Mock = Mock()
    delete_response.status_code = 204
    delete_response.text = ""
    mock_session.delete.return_value = delete_response

    return mock_session


@pytest.fixture
def mock_api_client(
    mock_config: APIConfig, mock_session: MagicMock
) -> Generator[APIClient, None, None]:
    """
    Create a properly mocked APIClient instance.

    This fixture creates an APIClient with a patched requests.Session constructor
    to avoid initialization issues.
    """
    # Create a patcher for the requests.Session constructor
    with patch("requests.Session", return_value=mock_session):
        # Create an instance of APIClient with the mock config
        client: APIClient = APIClient.__new__(APIClient, **mock_config.asdict())

        # Make sure our session was properly set
        client.session = mock_session

        yield client


@pytest.fixture
def mock_cpln_client(mock_api_client: APIClient) -> Generator[CPLNClient, None, None]:
    """
    Create a properly mocked CPLNClient instance.

    This fixture patches the APIClient constructor to return our mock_api_client
    when CPLNClient creates it.
    """
    # Create a patch for the APIClient constructor
    with (
        patch("cpln.client.APIClient", return_value=mock_api_client),
        patch.object(CPLNClient, "__init__", return_value=None),
    ):
        # Create a CPLNClient instance
        client: CPLNClient = CPLNClient.__new__(CPLNClient)

        # Manually set the api attribute
        client.api = mock_api_client

        yield client
