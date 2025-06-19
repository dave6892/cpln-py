"""Container filtering options and utilities."""

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ContainerFilterOptions:
    """Filter options for container discovery within workloads.

    This class defines the criteria that can be used to filter containers
    when searching within workloads or across multiple workloads.

    Attributes:
        health_status: List of health statuses to match (e.g., ["healthy", "unhealthy"])
        image_patterns: List of image name patterns (supports glob and regex)
        name_patterns: List of container name patterns (supports glob and regex)
        resource_thresholds: Dict of resource thresholds (e.g., {"memory": 80.0, "cpu": 50.0})
        replica_states: List of replica states to match (e.g., ["ready", "pending", "failed"])
        port_filters: List of port numbers that containers must expose
        environment_filters: Dict of environment variable filters (key: value pairs)
    """

    health_status: Optional[list[str]] = None
    image_patterns: Optional[list[str]] = None
    name_patterns: Optional[list[str]] = None
    resource_thresholds: Optional[dict[str, float]] = None
    replica_states: Optional[list[str]] = None
    port_filters: Optional[list[int]] = None
    environment_filters: Optional[dict[str, str]] = None

    def __post_init__(self) -> None:
        """Validate filter options after initialization."""
        self._validate_health_status()
        self._validate_patterns()
        self._validate_resource_thresholds()

    def _validate_health_status(self) -> None:
        """Validate health status values."""
        if self.health_status:
            valid_statuses = {"healthy", "unhealthy", "degraded", "unknown"}
            for status in self.health_status:
                if status not in valid_statuses:
                    raise ValueError(
                        f"Invalid health status: {status}. Must be one of {valid_statuses}"
                    )

    def _validate_patterns(self) -> None:
        """Validate regex patterns for safety."""
        patterns_to_check = []
        if self.image_patterns:
            patterns_to_check.extend(self.image_patterns)
        if self.name_patterns:
            patterns_to_check.extend(self.name_patterns)

        for pattern in patterns_to_check:
            try:
                # Test if pattern is valid regex
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e

    def _validate_resource_thresholds(self) -> None:
        """Validate resource threshold values."""
        if self.resource_thresholds:
            valid_resources = {"memory", "cpu", "replica_utilization"}
            for resource, threshold in self.resource_thresholds.items():
                if resource not in valid_resources:
                    raise ValueError(
                        f"Invalid resource type: {resource}. Must be one of {valid_resources}"
                    )
                if (
                    not isinstance(threshold, (int, float))
                    or threshold < 0
                    or threshold > 100
                ):
                    raise ValueError(
                        f"Resource threshold must be a number between 0 and 100, got: {threshold}"
                    )

    def has_filters(self) -> bool:
        """Check if any filters are actually set."""
        return any(
            [
                self.health_status,
                self.image_patterns,
                self.name_patterns,
                self.resource_thresholds,
                self.replica_states,
                self.port_filters,
                self.environment_filters,
            ]
        )


def _match_patterns(value: Optional[str], patterns: list[str]) -> bool:
    """Check if a value matches any of the given patterns.

    Supports both glob-style patterns (with * and ?) and regex patterns.

    Args:
        value: The string value to match against
        patterns: List of patterns to check

    Returns:
        True if value matches any pattern, False otherwise
    """
    if not patterns:
        return True

    # If value is None, no pattern can match
    if value is None:
        return False

    for pattern in patterns:
        # Convert glob patterns to regex
        if "*" in pattern or "?" in pattern:
            # Simple glob to regex conversion
            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            regex_pattern = f"^{regex_pattern}$"
        else:
            # Treat as regex pattern
            regex_pattern = pattern

        try:
            if re.match(regex_pattern, value, re.IGNORECASE):
                return True
        except re.error:
            # If regex fails, fall back to simple string matching
            if pattern.lower() in value.lower():
                return True

    return False


def _match_resource_thresholds(
    container_resources: dict[str, Any], thresholds: dict[str, float]
) -> bool:
    """Check if container resources meet the threshold criteria.

    Args:
        container_resources: Resource utilization data from container
        thresholds: Thresholds to check against

    Returns:
        True if all thresholds are met, False otherwise
    """
    if not thresholds:
        return True

    for resource, threshold in thresholds.items():
        container_value = container_resources.get(resource)
        if container_value is None:
            # If resource data is not available, consider it as not meeting threshold
            return False

        # Check if container value exceeds threshold
        if container_value < threshold:
            return False

    return True
