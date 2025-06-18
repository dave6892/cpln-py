"""Tests for workload config module."""

from cpln.config.workload import JSON, WorkloadConfig


def test_workload_config_creation():
    """Test WorkloadConfig dataclass creation."""
    specs = {"kind": "workload", "spec": {"containers": []}}
    config = WorkloadConfig(
        gvc="test-gvc", workload_id="test-workload", location="us-east", specs=specs
    )

    assert config.gvc == "test-gvc"
    assert config.workload_id == "test-workload"
    assert config.location == "us-east"
    assert config.specs == specs


def test_workload_config_optional_params():
    """Test WorkloadConfig with optional parameters."""
    config = WorkloadConfig(gvc="test-gvc", workload_id="test-workload")

    assert config.gvc == "test-gvc"
    assert config.workload_id == "test-workload"
    assert config.location is None
    assert config.specs is None


def test_json_typed_dict():
    """Test JSON TypedDict can accept various types."""
    # This test ensures JSON is properly defined as a TypedDict
    json_data: JSON = {}
    assert isinstance(json_data, dict)

    json_data_with_content: JSON = {"test": "value", "number": 123, "list": [1, 2, 3]}
    assert isinstance(json_data_with_content, dict)
