import os

import pytest
from cpln.api.config import APIConfig
from cpln.constants import (
    DEFAULT_CPLN_API_URL,
    DEFAULT_CPLN_API_VERSION,
    DEFAULT_TIMEOUT_SECONDS,
)


def test_api_config_default_values():
    config = APIConfig(
        base_url=os.getenv("CPLN_BASE_URL"),
        org=os.getenv("CPLN_ORG"),
        token=os.getenv("CPLN_TOKEN"),
    )
    assert config.base_url == DEFAULT_CPLN_API_URL
    assert config.org == os.getenv("CPLN_ORG")
    assert config.token == os.getenv("CPLN_TOKEN")
    assert config.version == DEFAULT_CPLN_API_VERSION
    assert config.timeout is DEFAULT_TIMEOUT_SECONDS


def test_api_config_custom_values():
    config = APIConfig(
        base_url=os.getenv("CPLN_BASE_URL"),
        org=os.getenv("CPLN_ORG"),
        token=os.getenv("CPLN_TOKEN"),
        version="2.0.0",
        timeout=30,
    )
    assert config.version == "2.0.0"
    assert config.timeout == 30


def test_api_config_org_url():
    config = APIConfig(
        base_url=os.getenv("CPLN_BASE_URL"),
        org=os.getenv("CPLN_ORG"),
        token=os.getenv("CPLN_TOKEN"),
    )
    expected_url = f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}"
    assert config.org_url == expected_url


def test_api_config_missing_required_fields():
    with pytest.raises(TypeError):
        APIConfig()  # Missing required fields

    with pytest.raises(TypeError):
        APIConfig(base_url=os.getenv("CPLN_BASE_URL"))  # Missing org and token

    with pytest.raises(TypeError):
        APIConfig(
            base_url=os.getenv("CPLN_BASE_URL"), org=os.getenv("CPLN_ORG")
        )  # Missing token


def test_api_config_asdict():
    config = APIConfig(
        base_url=os.getenv("CPLN_BASE_URL"),
        org=os.getenv("CPLN_ORG"),
        token=os.getenv("CPLN_TOKEN"),
    )
    config_dict = {
        "base_url": os.getenv("CPLN_BASE_URL"),
        "org": os.getenv("CPLN_ORG"),
        "token": os.getenv("CPLN_TOKEN"),
        "version": DEFAULT_CPLN_API_VERSION,
        "timeout": DEFAULT_TIMEOUT_SECONDS,
        "org_url": f"{os.getenv('CPLN_BASE_URL')}/org/{os.getenv('CPLN_ORG')}",
    }
    assert config.asdict() == config_dict
