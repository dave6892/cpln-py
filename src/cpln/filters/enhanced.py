"""Enhanced container filtering with advanced capabilities.

This module provides enhanced filtering capabilities including:
- Time-based filtering (created/updated timestamps)
- Cross-workload container discovery
- Advanced sorting and pagination
- Query expression evaluation
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Union

from .container import (
    _match_patterns,
)
from .query_parser import (
    AdvancedQueryParser,
    LogicalExpression,
    QueryExpression,
    QueryParseError,
)


class SortField(Enum):
    """Available fields for sorting containers."""

    NAME = "name"
    IMAGE = "image"
    CREATED = "created"
    UPDATED = "updated"
    CPU_USAGE = "cpu"
    MEMORY_USAGE = "memory"
    REPLICA_COUNT = "replicas"
    HEALTH_STATUS = "health"


class SortOrder(Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class SortOptions:
    """Options for sorting container results."""

    field: SortField
    order: SortOrder = SortOrder.ASC


@dataclass
class PaginationOptions:
    """Options for paginating container results."""

    page: int = 1
    per_page: int = 50
    max_per_page: int = 1000

    def __post_init__(self):
        if self.page < 1:
            raise ValueError("Page must be >= 1")
        if self.per_page < 1 or self.per_page > self.max_per_page:
            raise ValueError(f"per_page must be between 1 and {self.max_per_page}")


@dataclass
class ContainerTimeInfo:
    """Time-related information for a container."""

    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    last_restart: Optional[datetime] = None


@dataclass
class EnhancedContainerInfo:
    """Enhanced container information with additional metadata."""

    name: str
    image: str
    workload_name: str
    gvc: str
    location: Optional[str] = None
    health_status: str = "unknown"
    resource_usage: Optional[dict[str, float]] = None
    time_info: Optional[ContainerTimeInfo] = None
    labels: Optional[dict[str, str]] = None
    annotations: Optional[dict[str, str]] = None

    def matches_time_filter(
        self, field: str, operator: str, value: Union[datetime, timedelta]
    ) -> bool:
        """Check if container matches time-based filter criteria."""
        if not self.time_info:
            return False

        container_time = None
        if field in ["created_after", "created_before"]:
            container_time = self.time_info.created
        elif field in ["updated_after", "updated_before"]:
            container_time = self.time_info.updated
        elif field == "updated_within":
            if self.time_info.updated:
                time_diff = datetime.now() - self.time_info.updated
                return time_diff <= value
            return False

        if not container_time:
            return False

        if "after" in field:
            return container_time >= value
        elif "before" in field:
            return container_time <= value

        return False


class EnhancedContainerFilter:
    """Enhanced container filtering with advanced capabilities."""

    def __init__(self):
        self.query_parser = AdvancedQueryParser()

    def evaluate_query_expression(
        self,
        expression: Union[QueryExpression, LogicalExpression],
        container: EnhancedContainerInfo,
    ) -> bool:
        """Evaluate a parsed query expression against a container.

        Args:
            expression: Parsed query expression
            container: Container to evaluate against

        Returns:
            True if container matches the expression
        """
        if isinstance(expression, QueryExpression):
            return self._evaluate_single_expression(expression, container)
        elif isinstance(expression, LogicalExpression):
            return self._evaluate_logical_expression(expression, container)
        else:
            return False

    def _evaluate_single_expression(
        self, expr: QueryExpression, container: EnhancedContainerInfo
    ) -> bool:
        """Evaluate a single query expression."""
        result = False

        if expr.field == "name":
            result = _match_patterns(container.name, [str(expr.value)])
        elif expr.field == "image":
            result = _match_patterns(container.image, [str(expr.value)])
        elif expr.field in ["status", "health"]:
            result = container.health_status == str(expr.value)
        elif expr.field == "workload":
            result = _match_patterns(container.workload_name, [str(expr.value)])
        elif expr.field == "gvc":
            result = _match_patterns(container.gvc, [str(expr.value)])
        elif expr.field == "location":
            result = _match_patterns(container.location, [str(expr.value)])
        elif expr.field in ["cpu", "memory", "replica_utilization"]:
            if container.resource_usage:
                container_value = container.resource_usage.get(expr.field, 0)
                result = self._compare_numeric(
                    container_value, expr.operator, expr.value
                )
        elif expr.field.endswith(("_after", "_before", "_within")):
            result = container.matches_time_filter(
                expr.field, expr.operator, expr.value
            )
        elif expr.field == "env":
            # Handle environment variable queries like env.DATABASE_URL=postgres://...
            # This would require additional parsing of the field
            result = False  # Placeholder

        return not result if expr.negate else result

    def _evaluate_logical_expression(
        self, expr: LogicalExpression, container: EnhancedContainerInfo
    ) -> bool:
        """Evaluate a logical expression (AND/OR)."""
        left_result = self.evaluate_query_expression(expr.left, container)
        right_result = self.evaluate_query_expression(expr.right, container)

        if expr.operator == "AND":
            return left_result and right_result
        elif expr.operator == "OR":
            return left_result or right_result
        else:
            return False

    def _compare_numeric(
        self, container_value: float, operator: str, threshold: Union[int, float]
    ) -> bool:
        """Compare numeric values using the specified operator."""
        if operator == ">":
            return container_value > threshold
        elif operator == ">=":
            return container_value >= threshold
        elif operator == "<":
            return container_value < threshold
        elif operator == "<=":
            return container_value <= threshold
        elif operator in ["=", "=="]:
            return container_value == threshold
        elif operator == "!=":
            return container_value != threshold
        else:
            return False

    def filter_containers_by_query(
        self, containers: list[EnhancedContainerInfo], query: str
    ) -> list[EnhancedContainerInfo]:
        """Filter containers using a query string.

        Args:
            containers: List of containers to filter
            query: Query string to apply

        Returns:
            Filtered list of containers
        """
        try:
            expression = self.query_parser.parse(query)
            return [
                container
                for container in containers
                if self.evaluate_query_expression(expression, container)
            ]
        except QueryParseError as e:
            raise ValueError(f"Invalid query: {e}") from e

    def sort_containers(
        self, containers: list[EnhancedContainerInfo], sort_options: list[SortOptions]
    ) -> list[EnhancedContainerInfo]:
        """Sort containers by multiple criteria.

        Args:
            containers: List of containers to sort
            sort_options: List of sort criteria (applied in order)

        Returns:
            Sorted list of containers
        """

        def sort_key(container: EnhancedContainerInfo) -> tuple:
            """Generate sort key for a container."""
            key_values = []

            for sort_option in sort_options:
                field = sort_option.field

                if field == SortField.NAME:
                    value = container.name
                elif field == SortField.IMAGE:
                    value = container.image
                elif field == SortField.CREATED:
                    value = (
                        container.time_info.created
                        if container.time_info
                        else datetime.min
                    )
                elif field == SortField.UPDATED:
                    value = (
                        container.time_info.updated
                        if container.time_info
                        else datetime.min
                    )
                elif field == SortField.CPU_USAGE:
                    value = (
                        container.resource_usage.get("cpu", 0)
                        if container.resource_usage
                        else 0
                    )
                elif field == SortField.MEMORY_USAGE:
                    value = (
                        container.resource_usage.get("memory", 0)
                        if container.resource_usage
                        else 0
                    )
                elif field == SortField.REPLICA_COUNT:
                    value = (
                        container.resource_usage.get("replicas", 0)
                        if container.resource_usage
                        else 0
                    )
                elif field == SortField.HEALTH_STATUS:
                    # Sort by health priority: healthy, degraded, unknown, unhealthy
                    health_priority = {
                        "healthy": 0,
                        "degraded": 1,
                        "unknown": 2,
                        "unhealthy": 3,
                    }
                    value = health_priority.get(container.health_status, 4)
                else:
                    value = ""

                # Reverse for descending order
                if sort_option.order == SortOrder.DESC:
                    if isinstance(value, str):
                        # For strings, we need to reverse the comparison
                        value = tuple(
                            -ord(c) for c in value[:50]
                        )  # Limit to prevent huge tuples
                    elif isinstance(value, (int, float)):
                        value = -value
                    elif isinstance(value, datetime):
                        value = -value.timestamp()

                key_values.append(value)

            return tuple(key_values)

        return sorted(containers, key=sort_key)

    def paginate_containers(
        self, containers: list[EnhancedContainerInfo], pagination: PaginationOptions
    ) -> dict[str, Any]:
        """Paginate container results.

        Args:
            containers: List of containers to paginate
            pagination: Pagination options

        Returns:
            Dictionary with paginated results and metadata
        """
        total_count = len(containers)
        total_pages = (total_count + pagination.per_page - 1) // pagination.per_page

        start_index = (pagination.page - 1) * pagination.per_page
        end_index = start_index + pagination.per_page

        page_containers = containers[start_index:end_index]

        return {
            "containers": page_containers,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": pagination.page < total_pages,
                "has_prev": pagination.page > 1,
                "next_page": pagination.page + 1
                if pagination.page < total_pages
                else None,
                "prev_page": pagination.page - 1 if pagination.page > 1 else None,
            },
        }


class CrossWorkloadContainerDiscovery:
    """Discover containers across multiple workloads and GVCs."""

    def __init__(self, client):
        """Initialize with CPLN client."""
        self.client = client
        self.filter = EnhancedContainerFilter()

    def discover_containers_in_gvc(
        self,
        gvc: str,
        query: Optional[str] = None,
        include_spec: bool = True,
        include_deployment: bool = True,
    ) -> list[EnhancedContainerInfo]:
        """Discover all containers in a GVC.

        Args:
            gvc: GVC name to search in
            query: Optional query string to filter results
            include_spec: Include containers from workload specifications
            include_deployment: Include containers from live deployments

        Returns:
            List of discovered containers
        """
        containers = []

        # Get all workloads in the GVC
        workloads = self.client.workload.list(gvc=gvc)

        for workload in workloads:
            workload_containers = self._extract_containers_from_workload(
                workload, include_spec, include_deployment
            )
            containers.extend(workload_containers)

        # Apply query filter if provided
        if query:
            containers = self.filter.filter_containers_by_query(containers, query)

        return containers

    def discover_containers_across_gvcs(
        self,
        gvcs: list[str],
        query: Optional[str] = None,
        include_spec: bool = True,
        include_deployment: bool = True,
    ) -> dict[str, list[EnhancedContainerInfo]]:
        """Discover containers across multiple GVCs.

        Args:
            gvcs: List of GVC names to search in
            query: Optional query string to filter results
            include_spec: Include containers from workload specifications
            include_deployment: Include containers from live deployments

        Returns:
            Dictionary mapping GVC name to list of containers
        """
        results = {}

        for gvc in gvcs:
            try:
                containers = self.discover_containers_in_gvc(
                    gvc, query, include_spec, include_deployment
                )
                results[gvc] = containers
            except Exception as e:
                # Log error but continue with other GVCs
                print(f"Error discovering containers in GVC {gvc}: {e}")
                results[gvc] = []

        return results

    def _extract_containers_from_workload(
        self, workload, include_spec: bool, include_deployment: bool
    ) -> list[EnhancedContainerInfo]:
        """Extract container information from a workload."""
        containers = []

        # Extract from workload specification
        if include_spec:
            spec_containers = self._extract_from_spec(workload)
            containers.extend(spec_containers)

        # Extract from live deployment
        if include_deployment:
            try:
                deployment_containers = self._extract_from_deployment(workload)
                containers.extend(deployment_containers)
            except Exception as e:
                # Deployment may not exist or be accessible
                print(f"Could not get deployment for workload {workload.name}: {e}")

        return containers

    def _extract_from_spec(self, workload) -> list[EnhancedContainerInfo]:
        """Extract containers from workload specification."""
        containers = []
        spec = workload.get_spec()

        for container in spec.containers:
            container_info = EnhancedContainerInfo(
                name=container.name,
                image=container.image,
                workload_name=workload.name,
                gvc=workload.state.get("gvc", "unknown"),
                health_status="unknown",  # Not available in spec
                time_info=ContainerTimeInfo(
                    # These would need to be extracted from workload metadata
                    created=None,
                    updated=None,
                ),
            )
            containers.append(container_info)

        return containers

    def _extract_from_deployment(self, workload) -> list[EnhancedContainerInfo]:
        """Extract containers from live deployment."""
        containers = []

        try:
            deployment = workload.get_deployment()
            deployment_containers = deployment.get_containers()

            for container in deployment_containers.values():
                resource_usage = container.get_resource_utilization()
                health_status = "healthy" if container.is_healthy() else "unhealthy"

                container_info = EnhancedContainerInfo(
                    name=container.name,
                    image=container.image,
                    workload_name=workload.name,
                    gvc=workload.state.get("gvc", "unknown"),
                    health_status=health_status,
                    resource_usage=resource_usage,
                    time_info=ContainerTimeInfo(
                        # These would need to be extracted from deployment metadata
                        created=None,
                        updated=None,
                    ),
                )
                containers.append(container_info)

        except Exception:
            # Handle cases where deployment is not available
            pass

        return containers


def create_advanced_filter() -> EnhancedContainerFilter:
    """Create an enhanced container filter instance."""
    return EnhancedContainerFilter()


def create_cross_workload_discovery(client) -> CrossWorkloadContainerDiscovery:
    """Create a cross-workload container discovery instance."""
    return CrossWorkloadContainerDiscovery(client)
