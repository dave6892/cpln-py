"""Tests for utils module."""

import json
import os
import tempfile
import unittest.mock as mock

import pytest
from cpln.utils.utils import (
    get_default_workload_template,
    load_template,
)


def test_load_template():
    """Test loading JSON template from file."""
    test_data = {"key": "value", "number": 123}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name

    try:
        result = load_template(temp_file)
        assert result == test_data
    finally:
        os.unlink(temp_file)


def test_load_template_file_not_found():
    """Test load_template with non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_template("non_existent_file.json")


def test_get_default_workload_template_serverless():
    """Test getting default serverless workload template."""
    with mock.patch("cpln.utils.utils.load_template") as mock_load:
        mock_load.return_value = {"kind": "workload", "type": "serverless"}
        result = get_default_workload_template("serverless")
        assert result == {"kind": "workload", "type": "serverless"}
        mock_load.assert_called_once()


def test_get_default_workload_template_standard():
    """Test getting default standard workload template."""
    with mock.patch("cpln.utils.utils.load_template") as mock_load:
        mock_load.return_value = {"kind": "workload", "type": "standard"}
        result = get_default_workload_template("standard")
        assert result == {"kind": "workload", "type": "standard"}
        mock_load.assert_called_once()


def test_get_default_workload_template_invalid_type():
    """Test getting default workload template with invalid type."""
    with pytest.raises(ValueError, match="Invalid workload type: invalid"):
        get_default_workload_template("invalid")
