"""Unit tests for Phase 2 advanced container filtering features."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.cpln.filters.enhanced import (
    ContainerTimeInfo,
    CrossWorkloadContainerDiscovery,
    EnhancedContainerFilter,
    EnhancedContainerInfo,
    PaginationOptions,
    SortField,
    SortOptions,
    SortOrder,
)
from src.cpln.filters.query_parser import (
    AdvancedQueryParser,
    LogicalExpression,
    QueryExpression,
    QueryParseError,
    parse_advanced_query,
)


class TestAdvancedQueryParser:
    """Test advanced query parsing functionality."""

    def test_simple_field_value_query(self):
        """Test parsing simple field:value queries."""
        parser = AdvancedQueryParser()

        # Test image pattern
        expr = parser.parse("image:nginx*")
        assert isinstance(expr, QueryExpression)
        assert expr.field == "image"
        assert expr.operator == ":"
        assert expr.value == "nginx*"
        assert not expr.negate

    def test_numeric_comparison_query(self):
        """Test parsing numeric comparison queries."""
        parser = AdvancedQueryParser()

        expr = parser.parse("cpu>50")
        assert isinstance(expr, QueryExpression)
        assert expr.field == "cpu"
        assert expr.operator == ">"
        assert expr.value == 50.0

    def test_logical_and_query(self):
        """Test parsing AND logical expressions."""
        parser = AdvancedQueryParser()

        expr = parser.parse("image:nginx* AND cpu>50")
        assert isinstance(expr, LogicalExpression)
        assert expr.operator == "AND"

        # Check left side
        assert isinstance(expr.left, QueryExpression)
        assert expr.left.field == "image"
        assert expr.left.value == "nginx*"

        # Check right side
        assert isinstance(expr.right, QueryExpression)
        assert expr.right.field == "cpu"
        assert expr.right.value == 50.0

    def test_logical_or_query(self):
        """Test parsing OR logical expressions."""
        parser = AdvancedQueryParser()

        expr = parser.parse("status:healthy OR status:degraded")
        assert isinstance(expr, LogicalExpression)
        assert expr.operator == "OR"

    def test_parentheses_grouping(self):
        """Test parsing expressions with parentheses."""
        parser = AdvancedQueryParser()

        expr = parser.parse("(status:healthy OR status:degraded) AND cpu>50")
        assert isinstance(expr, LogicalExpression)
        assert expr.operator == "AND"

        # Left side should be the OR expression
        assert isinstance(expr.left, LogicalExpression)
        assert expr.left.operator == "OR"

        # Right side should be the cpu comparison
        assert isinstance(expr.right, QueryExpression)
        assert expr.right.field == "cpu"

    def test_not_operator(self):
        """Test parsing NOT expressions."""
        parser = AdvancedQueryParser()

        expr = parser.parse("NOT status:unhealthy")
        assert isinstance(expr, QueryExpression)
        assert expr.field == "status"
        assert expr.value == "unhealthy"
        assert expr.negate

    def test_datetime_parsing(self):
        """Test parsing datetime values."""
        parser = AdvancedQueryParser()

        expr = parser.parse("created_after:2024-01-01")
        assert isinstance(expr, QueryExpression)
        assert expr.field == "created_after"
        assert isinstance(expr.value, datetime)
        assert expr.value.year == 2024
        assert expr.value.month == 1
        assert expr.value.day == 1

    def test_duration_parsing(self):
        """Test parsing duration values."""
        parser = AdvancedQueryParser()

        expr = parser.parse("updated_within:7d")
        assert isinstance(expr, QueryExpression)
        assert expr.field == "updated_within"
        assert isinstance(expr.value, timedelta)
        assert expr.value.days == 7

    def test_quoted_values(self):
        """Test parsing quoted string values."""
        parser = AdvancedQueryParser()

        expr = parser.parse('name:"my container"')
        assert isinstance(expr, QueryExpression)
        assert expr.field == "name"
        assert expr.value == "my container"

    def test_invalid_syntax_errors(self):
        """Test that invalid syntax raises appropriate errors."""
        parser = AdvancedQueryParser()

        with pytest.raises(QueryParseError, match="Empty query string"):
            parser.parse("")

        with pytest.raises(QueryParseError, match="Missing closing parenthesis"):
            parser.parse("(status:healthy")

        with pytest.raises(QueryParseError, match="Unknown field"):
            parser.parse("invalid_field:value")

    def test_parse_advanced_query_function(self):
        """Test the convenience function for parsing queries."""
        expr = parse_advanced_query("image:nginx*")
        assert isinstance(expr, QueryExpression)
        assert expr.field == "image"


class TestEnhancedContainerFilter:
    """Test enhanced container filtering functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = EnhancedContainerFilter()

        # Create test containers
        self.containers = [
            EnhancedContainerInfo(
                name="web-nginx",
                image="nginx:1.21",
                workload_name="web-app",
                gvc="production",
                health_status="healthy",
                resource_usage={
                    "cpu": 45.0,
                    "memory": 60.0,
                    "replica_utilization": 80.0,
                },
                time_info=ContainerTimeInfo(
                    created=datetime(2024, 1, 1, 10, 0, 0),
                    updated=datetime(2024, 1, 2, 10, 0, 0),
                ),
            ),
            EnhancedContainerInfo(
                name="api-python",
                image="python:3.9",
                workload_name="api-service",
                gvc="production",
                health_status="unhealthy",
                resource_usage={
                    "cpu": 75.0,
                    "memory": 85.0,
                    "replica_utilization": 60.0,
                },
                time_info=ContainerTimeInfo(
                    created=datetime(2024, 1, 3, 10, 0, 0),
                    updated=datetime(2024, 1, 4, 10, 0, 0),
                ),
            ),
            EnhancedContainerInfo(
                name="cache-redis",
                image="redis:6.2",
                workload_name="cache-service",
                gvc="staging",
                health_status="healthy",
                resource_usage={
                    "cpu": 30.0,
                    "memory": 40.0,
                    "replica_utilization": 90.0,
                },
                time_info=ContainerTimeInfo(
                    created=datetime(2024, 1, 5, 10, 0, 0),
                    updated=datetime(2024, 1, 6, 10, 0, 0),
                ),
            ),
        ]

    def test_filter_by_simple_query(self):
        """Test filtering containers with simple queries."""
        # Filter by image pattern
        result = self.filter.filter_containers_by_query(self.containers, "image:nginx*")
        assert len(result) == 1
        assert result[0].name == "web-nginx"

        # Filter by health status
        result = self.filter.filter_containers_by_query(
            self.containers, "health:healthy"
        )
        assert len(result) == 2
        assert all(c.health_status == "healthy" for c in result)

        # Filter by GVC
        result = self.filter.filter_containers_by_query(
            self.containers, "gvc:production"
        )
        assert len(result) == 2
        assert all(c.gvc == "production" for c in result)

    def test_filter_by_numeric_query(self):
        """Test filtering containers with numeric queries."""
        # Filter by CPU usage
        result = self.filter.filter_containers_by_query(self.containers, "cpu>50")
        assert len(result) == 1
        assert result[0].name == "api-python"

        # Filter by memory usage
        result = self.filter.filter_containers_by_query(self.containers, "memory<=60")
        assert len(result) == 2

        # Filter by replica utilization
        result = self.filter.filter_containers_by_query(
            self.containers, "replica_utilization>=80"
        )
        assert len(result) == 2

    def test_filter_by_logical_query(self):
        """Test filtering containers with logical expressions."""
        # AND query
        result = self.filter.filter_containers_by_query(
            self.containers, "health:healthy AND cpu<50"
        )
        assert len(result) == 2
        assert all(c.health_status == "healthy" for c in result)
        assert all(c.resource_usage["cpu"] < 50 for c in result)

        # OR query
        result = self.filter.filter_containers_by_query(
            self.containers, "gvc:staging OR health:unhealthy"
        )
        assert len(result) == 2

    def test_sort_containers(self):
        """Test sorting containers by various criteria."""
        # Sort by name ascending
        sort_options = [SortOptions(SortField.NAME, SortOrder.ASC)]
        result = self.filter.sort_containers(self.containers, sort_options)
        names = [c.name for c in result]
        assert names == ["api-python", "cache-redis", "web-nginx"]

        # Sort by CPU usage descending
        sort_options = [SortOptions(SortField.CPU_USAGE, SortOrder.DESC)]
        result = self.filter.sort_containers(self.containers, sort_options)
        cpu_values = [c.resource_usage["cpu"] for c in result]
        assert cpu_values == [75.0, 45.0, 30.0]

        # Sort by health status (healthy first)
        sort_options = [SortOptions(SortField.HEALTH_STATUS, SortOrder.ASC)]
        result = self.filter.sort_containers(self.containers, sort_options)
        health_statuses = [c.health_status for c in result]
        assert health_statuses[:2] == ["healthy", "healthy"]
        assert health_statuses[2] == "unhealthy"

    def test_multi_field_sorting(self):
        """Test sorting by multiple fields."""
        # Sort by health status first, then by CPU usage
        sort_options = [
            SortOptions(SortField.HEALTH_STATUS, SortOrder.ASC),
            SortOptions(SortField.CPU_USAGE, SortOrder.DESC),
        ]
        result = self.filter.sort_containers(self.containers, sort_options)

        # Should have healthy containers first, sorted by CPU descending
        assert result[0].health_status == "healthy"
        assert result[1].health_status == "healthy"
        assert result[0].resource_usage["cpu"] >= result[1].resource_usage["cpu"]
        assert result[2].health_status == "unhealthy"

    def test_paginate_containers(self):
        """Test pagination of container results."""
        pagination = PaginationOptions(page=1, per_page=2)
        result = self.filter.paginate_containers(self.containers, pagination)

        assert len(result["containers"]) == 2
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 2
        assert result["pagination"]["total_count"] == 3
        assert result["pagination"]["total_pages"] == 2
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False
        assert result["pagination"]["next_page"] == 2
        assert result["pagination"]["prev_page"] is None

        # Test second page
        pagination = PaginationOptions(page=2, per_page=2)
        result = self.filter.paginate_containers(self.containers, pagination)

        assert len(result["containers"]) == 1
        assert result["pagination"]["has_next"] is False
        assert result["pagination"]["has_prev"] is True

    def test_pagination_validation(self):
        """Test pagination option validation."""
        with pytest.raises(ValueError, match="Page must be >= 1"):
            PaginationOptions(page=0)

        with pytest.raises(ValueError, match="per_page must be between"):
            PaginationOptions(per_page=0)

        with pytest.raises(ValueError, match="per_page must be between"):
            PaginationOptions(per_page=2000)


class TestContainerTimeInfo:
    """Test time-based filtering functionality."""

    def test_matches_time_filter_created_after(self):
        """Test created_after time filtering."""
        time_info = ContainerTimeInfo(
            created=datetime(2024, 1, 15), updated=datetime(2024, 1, 20)
        )
        container = EnhancedContainerInfo(
            name="test",
            image="test:latest",
            workload_name="test",
            gvc="test",
            time_info=time_info,
        )

        # Should match (created after Jan 1)
        assert container.matches_time_filter(
            "created_after", ">=", datetime(2024, 1, 1)
        )

        # Should not match (created before Jan 20)
        assert not container.matches_time_filter(
            "created_after", ">=", datetime(2024, 1, 20)
        )

    def test_matches_time_filter_updated_within(self):
        """Test updated_within time filtering."""
        # Container updated 5 days ago
        time_info = ContainerTimeInfo(updated=datetime.now() - timedelta(days=5))
        container = EnhancedContainerInfo(
            name="test",
            image="test:latest",
            workload_name="test",
            gvc="test",
            time_info=time_info,
        )

        # Should match (updated within 7 days)
        assert container.matches_time_filter("updated_within", "<=", timedelta(days=7))

        # Should not match (updated within 3 days)
        assert not container.matches_time_filter(
            "updated_within", "<=", timedelta(days=3)
        )

    def test_matches_time_filter_no_time_info(self):
        """Test time filtering with no time info."""
        container = EnhancedContainerInfo(
            name="test",
            image="test:latest",
            workload_name="test",
            gvc="test",
            time_info=None,
        )

        # Should not match when no time info available
        assert not container.matches_time_filter(
            "created_after", ">=", datetime(2024, 1, 1)
        )


class TestCrossWorkloadContainerDiscovery:
    """Test cross-workload container discovery functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.discovery = CrossWorkloadContainerDiscovery(self.mock_client)

    @patch("src.cpln.filters.enhanced.EnhancedContainerFilter")
    def test_discover_containers_in_gvc(self, mock_filter):
        """Test discovering containers within a single GVC."""
        # Mock workload with containers
        mock_workload = Mock()
        mock_workload.name = "test-workload"
        mock_workload.state = {"gvc": "test-gvc"}

        # Mock spec container
        mock_spec = Mock()
        mock_container = Mock()
        mock_container.name = "test-container"
        mock_container.image = "test:latest"
        mock_spec.containers = [mock_container]
        mock_workload.get_spec.return_value = mock_spec

        # Mock deployment
        mock_workload.get_deployment.side_effect = Exception("No deployment")

        self.mock_client.workload.list.return_value = [mock_workload]

        # Mock filter
        mock_filter_instance = Mock()
        mock_filter_instance.filter_containers_by_query.return_value = []
        mock_filter.return_value = mock_filter_instance

        containers = self.discovery.discover_containers_in_gvc(
            "test-gvc", include_deployment=False
        )

        # Should call workload.list with correct GVC
        self.mock_client.workload.list.assert_called_once_with(gvc="test-gvc")

        # Should extract containers from spec
        mock_workload.get_spec.assert_called_once()

        # Should return containers
        assert isinstance(containers, list)

    def test_discover_containers_across_gvcs(self):
        """Test discovering containers across multiple GVCs."""
        # Mock the discover_containers_in_gvc method
        self.discovery.discover_containers_in_gvc = Mock()
        self.discovery.discover_containers_in_gvc.side_effect = [
            [Mock()],  # GVC 1 has 1 container
            [Mock(), Mock()],  # GVC 2 has 2 containers
        ]

        gvcs = ["gvc1", "gvc2"]
        result = self.discovery.discover_containers_across_gvcs(gvcs)

        assert "gvc1" in result
        assert "gvc2" in result
        assert len(result["gvc1"]) == 1
        assert len(result["gvc2"]) == 2

    def test_discover_containers_with_error_handling(self):
        """Test error handling during container discovery."""
        # Mock workload that raises an exception
        self.discovery.discover_containers_in_gvc = Mock()
        self.discovery.discover_containers_in_gvc.side_effect = Exception("API Error")

        # Should handle the error gracefully
        result = self.discovery.discover_containers_across_gvcs(["failing-gvc"])

        assert "failing-gvc" in result
        assert result["failing-gvc"] == []  # Empty list on error
