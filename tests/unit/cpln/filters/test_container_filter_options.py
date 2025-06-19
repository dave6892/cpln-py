"""Tests for ContainerFilterOptions and filtering utilities."""

import pytest
from cpln.filters.container import (
    ContainerFilterOptions,
    _match_patterns,
    _match_resource_thresholds,
)


class TestContainerFilterOptions:
    """Test the ContainerFilterOptions dataclass."""

    def test_empty_filter_options(self):
        """Test that empty filter options are valid."""
        filters = ContainerFilterOptions()
        assert not filters.has_filters()

    def test_health_status_validation(self):
        """Test health status validation."""
        # Valid health statuses
        filters = ContainerFilterOptions(health_status=["healthy", "unhealthy"])
        assert filters.health_status == ["healthy", "unhealthy"]

        # Invalid health status should raise ValueError
        with pytest.raises(ValueError, match="Invalid health status"):
            ContainerFilterOptions(health_status=["invalid_status"])

    def test_pattern_validation(self):
        """Test pattern validation for image and name patterns."""
        # Valid patterns
        filters = ContainerFilterOptions(
            image_patterns=["nginx*", "redis.*"], name_patterns=["web-*", "api-.*"]
        )
        assert filters.image_patterns == ["nginx*", "redis.*"]

        # Invalid regex pattern should raise ValueError
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            ContainerFilterOptions(image_patterns=["[invalid"])

    def test_resource_threshold_validation(self):
        """Test resource threshold validation."""
        # Valid thresholds
        filters = ContainerFilterOptions(
            resource_thresholds={"memory": 80.0, "cpu": 50.0}
        )
        assert filters.resource_thresholds == {"memory": 80.0, "cpu": 50.0}

        # Invalid resource type
        with pytest.raises(ValueError, match="Invalid resource type"):
            ContainerFilterOptions(resource_thresholds={"invalid_resource": 50.0})

        # Invalid threshold value (negative)
        with pytest.raises(ValueError, match="Resource threshold must be a number"):
            ContainerFilterOptions(resource_thresholds={"memory": -10.0})

        # Invalid threshold value (over 100)
        with pytest.raises(ValueError, match="Resource threshold must be a number"):
            ContainerFilterOptions(resource_thresholds={"cpu": 150.0})

    def test_has_filters(self):
        """Test the has_filters method."""
        # No filters
        filters = ContainerFilterOptions()
        assert not filters.has_filters()

        # With health status filter
        filters = ContainerFilterOptions(health_status=["healthy"])
        assert filters.has_filters()

        # With image pattern filter
        filters = ContainerFilterOptions(image_patterns=["nginx*"])
        assert filters.has_filters()

        # With multiple filters
        filters = ContainerFilterOptions(
            health_status=["healthy"],
            image_patterns=["nginx*"],
            resource_thresholds={"memory": 80.0},
        )
        assert filters.has_filters()


class TestMatchPatterns:
    """Test the pattern matching utility function."""

    def test_match_patterns_no_patterns(self):
        """Test that empty patterns list returns True."""
        assert _match_patterns("nginx", [])
        assert _match_patterns("anything", None)

    def test_match_patterns_glob_style(self):
        """Test glob-style pattern matching."""
        # Wildcard patterns
        assert _match_patterns("nginx:latest", ["nginx*"])
        assert _match_patterns("nginx-proxy", ["nginx*"])
        assert not _match_patterns("redis", ["nginx*"])

        # Question mark patterns
        assert _match_patterns("nginx1", ["nginx?"])
        assert _match_patterns("nginxA", ["nginx?"])
        assert not _match_patterns("nginx", ["nginx?"])
        assert not _match_patterns("nginx12", ["nginx?"])

    def test_match_patterns_regex_style(self):
        """Test regex pattern matching."""
        # Regex patterns
        assert _match_patterns("nginx", ["^nginx$"])
        assert _match_patterns("nginx:latest", ["nginx:.*"])
        assert not _match_patterns("redis", ["^nginx$"])

    def test_match_patterns_case_insensitive(self):
        """Test case-insensitive matching."""
        assert _match_patterns("NGINX", ["nginx*"])
        assert _match_patterns("nginx", ["NGINX*"])

    def test_match_patterns_fallback_substring(self):
        """Test fallback to substring matching on regex errors."""
        # Invalid regex should fall back to substring matching
        assert _match_patterns("nginx-container", ["nginx"])
        assert not _match_patterns("redis-container", ["nginx"])


class TestMatchResourceThresholds:
    """Test the resource threshold matching utility function."""

    def test_match_resource_thresholds_no_thresholds(self):
        """Test that empty thresholds return True."""
        container_resources = {"memory": 50.0, "cpu": 30.0}
        assert _match_resource_thresholds(container_resources, {})
        assert _match_resource_thresholds(container_resources, None)

    def test_match_resource_thresholds_above_threshold(self):
        """Test matching when resources are above thresholds."""
        container_resources = {
            "memory": 90.0,
            "cpu": 60.0,
            "replica_utilization": 100.0,
        }
        thresholds = {"memory": 80.0, "cpu": 50.0}

        assert _match_resource_thresholds(container_resources, thresholds)

    def test_match_resource_thresholds_below_threshold(self):
        """Test not matching when resources are below thresholds."""
        container_resources = {"memory": 70.0, "cpu": 40.0, "replica_utilization": 50.0}
        thresholds = {"memory": 80.0, "cpu": 50.0}

        assert not _match_resource_thresholds(container_resources, thresholds)

    def test_match_resource_thresholds_missing_data(self):
        """Test handling of missing resource data."""
        container_resources = {"memory": 90.0}  # Missing CPU data
        thresholds = {"memory": 80.0, "cpu": 50.0}

        # Should return False if any required threshold data is missing
        assert not _match_resource_thresholds(container_resources, thresholds)

    def test_match_resource_thresholds_single_threshold(self):
        """Test matching with single threshold."""
        container_resources = {"memory": 90.0, "cpu": 40.0}
        thresholds = {"memory": 80.0}

        assert _match_resource_thresholds(container_resources, thresholds)

        thresholds = {"cpu": 50.0}
        assert not _match_resource_thresholds(container_resources, thresholds)
