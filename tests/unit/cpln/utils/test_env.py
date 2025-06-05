import os
from unittest.mock import patch

import pytest
from cpln.constants import (
    DEFAULT_CPLN_API_URL,
)
from cpln.utils import kwargs_from_env

CPLN_TOKEN = os.getenv("CPLN_TOKEN")
CPLN_ORG = os.getenv("CPLN_ORG")


def test_kwargs_from_env_default():
    with patch.dict(os.environ, {"CPLN_TOKEN": CPLN_TOKEN, "CPLN_ORG": CPLN_ORG}):
        kwargs = kwargs_from_env()
        assert kwargs["token"] == CPLN_TOKEN
        assert kwargs["org"] == CPLN_ORG
        assert "base_url" in kwargs
        assert "version" not in kwargs
        assert "timeout" not in kwargs


def test_kwargs_from_env_all_variables():
    with patch.dict(
        os.environ,
        {
            "CPLN_TOKEN": CPLN_TOKEN,
            "CPLN_ORG": CPLN_ORG,
            "CPLN_BASE_URL": DEFAULT_CPLN_API_URL,
            "CPLN_VERSION": "2.0.0",
            "CPLN_TIMEOUT": "30",
        },
    ):
        kwargs = kwargs_from_env()
        assert kwargs["token"] == CPLN_TOKEN
        assert kwargs["org"] == CPLN_ORG
        assert kwargs["base_url"] == DEFAULT_CPLN_API_URL


def test_kwargs_from_env_missing_required():
    with (
        patch.dict(os.environ, {"CPLN_TOKEN": "", "CPLN_ORG": ""}),
        pytest.raises(ValueError),
    ):
        kwargs_from_env()

    with (
        patch.dict(os.environ, {"CPLN_TOKEN": "test-token", "CPLN_ORG": ""}),
        pytest.raises(ValueError),
    ):
        kwargs_from_env()

    with (
        patch.dict(os.environ, {"CPLN_ORG": "test-org", "CPLN_TOKEN": ""}),
        pytest.raises(ValueError),
    ):
        kwargs_from_env()


def test_kwargs_from_env_custom_environment():
    custom_env = {"CPLN_TOKEN": "test-token", "CPLN_ORG": "test-org"}
    kwargs = kwargs_from_env(environment=custom_env)
    assert kwargs["token"] == "test-token"
    assert kwargs["org"] == "test-org"
