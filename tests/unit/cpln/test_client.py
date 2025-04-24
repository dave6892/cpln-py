import pytest
import os
from unittest.mock import Mock, patch
from cpln import CPLNClient

def test_cpln_client_initialization(mock_cpln_client):
    assert mock_cpln_client.api.config.base_url == os.getenv('CPLN_BASE_URL')
    assert mock_cpln_client.api.config.org == os.getenv('CPLN_ORG')
    assert mock_cpln_client.api.config.token == os.getenv('CPLN_TOKEN')

def test_cpln_client_from_env():
    with patch('cpln.utils.kwargs_from_env') as mock_kwargs:
        mock_kwargs.return_value = {
            'base_url': os.getenv('CPLN_BASE_URL'),
            'org': os.getenv('CPLN_ORG'),
            'token': os.getenv('CPLN_TOKEN')
        }
        client = CPLNClient.from_env()
        assert client.api.config.base_url == os.getenv('CPLN_BASE_URL')
        assert client.api.config.org == os.getenv('CPLN_ORG')
        assert client.api.config.token == os.getenv('CPLN_TOKEN')

def test_cpln_client_gvcs_property(mock_cpln_client):
    gvcs = mock_cpln_client.gvcs
    assert gvcs.client == mock_cpln_client

def test_cpln_client_images_property(mock_cpln_client):
    images = mock_cpln_client.images
    assert images.client == mock_cpln_client

def test_cpln_client_workloads_property(mock_cpln_client):
    workloads = mock_cpln_client.workloads
    assert workloads.client == mock_cpln_client
