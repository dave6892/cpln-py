import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import Mock, patch
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
def mock_api_client(mock_config):
    with patch('requests.Session') as mock_session:
        client = APIClient(config=mock_config)
        client.get = Mock()
        client.post = Mock()
        client.patch = Mock()
        client.delete = Mock()
        yield client

@pytest.fixture
def mock_cpln_client(mock_api_client):
    with patch('cpln.client.APIClient', return_value=mock_api_client):
        client = CPLNClient(
            base_url=os.getenv('CPLN_BASE_URL'),
            org=os.getenv('CPLN_ORG'),
            token=os.getenv('CPLN_TOKEN')
        )
        yield client
