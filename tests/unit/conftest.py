import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import Mock, patch, MagicMock
import requests
from cpln.api.config import APIConfig
from cpln.api.client import APIClient
from cpln import CPLNClient

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

@pytest.fixture(autouse=True)
def mock_env_vars():
    # Only override if not set in .env
    env_vars = {
        'CPLN_TOKEN': os.getenv('CPLN_TOKEN', 'test-token'),
        'CPLN_ORG': os.getenv('CPLN_ORG', 'test-org'),
        'CPLN_BASE_URL': os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')
    }
    with patch.dict(os.environ, env_vars):
        yield

@pytest.fixture
def mock_config():
    return APIConfig(
        base_url=os.getenv('CPLN_BASE_URL'),
        org=os.getenv('CPLN_ORG'),
        token=os.getenv('CPLN_TOKEN')
    )

@pytest.fixture
def mock_session():
    """
    Create a mock session with appropriate response behaviors.
    """
    mock_session = MagicMock(spec=requests.Session)
    
    # Set up default responses for HTTP methods
    get_response = Mock()
    get_response.status_code = 200
    get_response.json.return_value = {}
    mock_session.get.return_value = get_response
    
    post_response = Mock()
    post_response.status_code = 201
    post_response.json.return_value = {}
    post_response.text = "Created"
    mock_session.post.return_value = post_response
    
    patch_response = Mock()
    patch_response.status_code = 200
    patch_response.json.return_value = {}
    patch_response.text = "OK"
    mock_session.patch.return_value = patch_response
    
    delete_response = Mock()
    delete_response.status_code = 204
    delete_response.text = ""
    mock_session.delete.return_value = delete_response
    
    return mock_session


@pytest.fixture
def mock_api_client(mock_config, mock_session):
    """
    Create a properly mocked APIClient instance.
    
    This fixture creates an APIClient with a patched requests.Session constructor
    to avoid initialization issues.
    """
    # Create a patcher for the requests.Session constructor
    with patch('requests.Session', return_value=mock_session):
        # Create an instance of APIClient with the mock config
        client = APIClient(config=mock_config)
        
        # Make sure our session was properly set
        client.session = mock_session
        
        yield client

@pytest.fixture
def mock_cpln_client(mock_api_client):
    """
    Create a properly mocked CPLNClient instance.
    
    This fixture patches the APIClient constructor to return our mock_api_client
    when CPLNClient creates it.
    """
    # Create a patch for the APIClient constructor
    with patch('cpln.client.APIClient', return_value=mock_api_client):
        # Mock the CPLNClient.__init__ method to avoid initialization issues
        with patch.object(CPLNClient, '__init__', return_value=None):
            # Create a CPLNClient instance
            client = CPLNClient.__new__(CPLNClient)
            
            # Manually set the api attribute
            client.api = mock_api_client
            
            yield client
