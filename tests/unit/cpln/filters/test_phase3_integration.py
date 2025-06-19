"""
Unit tests for Phase 3 container filtering integration features.

Tests cover:
- Caching functionality with TTL and LRU eviction
- Performance monitoring and metrics collection
- CLI integration and output formatting
- Production-ready error handling
- Integration with existing filtering phases
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from cpln.filters.container import ContainerFilterOptions
from cpln.filters.integration import (
    CacheEntry,
    CLIIntegration,
    FilterCache,
    FilterMetrics,
    IntegratedContainerFilter,
    create_production_filter,
    performance_monitor,
    quick_filter,
)


class TestFilterMetrics:
    """Test FilterMetrics functionality."""

    def test_initial_state(self):
        """Test initial metrics state."""
        metrics = FilterMetrics()
        assert metrics.operation_count == 0
        assert metrics.total_duration == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.error_count == 0
        assert metrics.last_operation_time is None

    def test_average_duration_calculation(self):
        """Test average duration calculation."""
        metrics = FilterMetrics()
        metrics.operation_count = 4
        metrics.total_duration = 2.0

        assert metrics.average_duration == 0.5

    def test_average_duration_zero_operations(self):
        """Test average duration with zero operations."""
        metrics = FilterMetrics()
        assert metrics.average_duration == 0.0

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        metrics = FilterMetrics()
        metrics.cache_hits = 8
        metrics.cache_misses = 2

        assert metrics.cache_hit_rate == 0.8

    def test_cache_hit_rate_no_requests(self):
        """Test cache hit rate with no requests."""
        metrics = FilterMetrics()
        assert metrics.cache_hit_rate == 0.0


class TestCacheEntry:
    """Test CacheEntry functionality."""

    def test_initial_state(self):
        """Test initial cache entry state."""
        data = {"test": "data"}
        entry = CacheEntry(data=data, timestamp=datetime.now())

        assert entry.data == data
        assert entry.ttl_seconds == 300
        assert entry.access_count == 0

    def test_expiration_check(self):
        """Test expiration checking."""
        # Non-expired entry
        entry = CacheEntry(data="test", timestamp=datetime.now(), ttl_seconds=300)
        assert not entry.is_expired()

        # Expired entry
        old_timestamp = datetime.now() - timedelta(seconds=400)
        expired_entry = CacheEntry(
            data="test", timestamp=old_timestamp, ttl_seconds=300
        )
        assert expired_entry.is_expired()

    def test_access_tracking(self):
        """Test access count tracking."""
        entry = CacheEntry(data="test", timestamp=datetime.now())

        # Initial access
        result = entry.access()
        assert result == "test"
        assert entry.access_count == 1

        # Second access
        entry.access()
        assert entry.access_count == 2


class TestFilterCache:
    """Test FilterCache functionality."""

    def test_initialization(self):
        """Test cache initialization."""
        cache = FilterCache(max_size=100, default_ttl=600)

        assert cache.max_size == 100
        assert cache.default_ttl == 600
        assert len(cache._cache) == 0
        assert len(cache._access_order) == 0

    def test_key_generation(self):
        """Test cache key generation."""
        cache = FilterCache()
        filter_options = ContainerFilterOptions(
            gvc="test-gvc", workload="test-workload"
        )

        key1 = cache._generate_key(filter_options, "query1")
        key2 = cache._generate_key(filter_options, "query1")
        key3 = cache._generate_key(filter_options, "query2")

        # Same inputs should generate same key
        assert key1 == key2

        # Different inputs should generate different keys
        assert key1 != key3

    def test_put_and_get(self):
        """Test basic put and get operations."""
        cache = FilterCache(max_size=10)

        # Put data
        cache.put("test_key", {"data": "test"})

        # Get data
        result = cache.get("test_key")
        assert result == {"data": "test"}

        # Non-existent key
        assert cache.get("non_existent") is None

    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = FilterCache(default_ttl=1)

        # Put data with short TTL
        cache.put("test_key", "test_data", ttl=1)

        # Should be available immediately
        assert cache.get("test_key") == "test_data"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("test_key") is None

    def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = FilterCache(max_size=2)

        # Fill cache to capacity
        cache.put("key1", "data1")
        cache.put("key2", "data2")

        # Access key1 to make it more recently used
        cache.get("key1")

        # Add third item, should evict key2 (least recently used)
        cache.put("key3", "data3")

        assert cache.get("key1") == "data1"  # Should still exist
        assert cache.get("key2") is None  # Should be evicted
        assert cache.get("key3") == "data3"  # Should exist

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = FilterCache(default_ttl=1)

        # Add entries with short TTL
        cache.put("key1", "data1", ttl=1)
        cache.put("key2", "data2", ttl=1)
        cache.put("key3", "data3", ttl=10)  # Longer TTL

        # Wait for expiration
        time.sleep(1.1)

        # Cleanup expired entries
        removed_count = cache.cleanup_expired()

        assert removed_count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "data3"

    def test_clear(self):
        """Test cache clearing."""
        cache = FilterCache()

        # Add data
        cache.put("key1", "data1")
        cache.put("key2", "data2")

        # Clear cache
        cache.clear()

        assert len(cache._cache) == 0
        assert len(cache._access_order) == 0
        assert cache.get("key1") is None

    def test_stats(self):
        """Test cache statistics."""
        cache = FilterCache()

        # Add some data and access it
        cache.put("key1", "data1")
        cache.get("key1")
        cache.get("key1")

        stats = cache.stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 1000
        assert stats["total_accesses"] == 2
        assert stats["expired_entries"] == 0


class TestPerformanceMonitor:
    """Test performance monitoring decorator."""

    @pytest.mark.asyncio
    async def test_async_function_monitoring(self):
        """Test monitoring of async functions."""
        mock_metrics = Mock()
        mock_metrics.operation_count = 0
        mock_metrics.total_duration = 0.0
        mock_metrics.error_count = 0

        class TestClass:
            def __init__(self):
                self.metrics = mock_metrics

            @performance_monitor
            async def test_method(self, value):
                await asyncio.sleep(0.1)  # Simulate work
                return value * 2

        obj = TestClass()
        result = await obj.test_method(5)

        assert result == 10
        assert mock_metrics.operation_count == 1
        assert mock_metrics.total_duration > 0.1
        assert mock_metrics.error_count == 0

    def test_sync_function_monitoring(self):
        """Test monitoring of sync functions."""
        mock_metrics = Mock()
        mock_metrics.operation_count = 0
        mock_metrics.total_duration = 0.0
        mock_metrics.error_count = 0

        class TestClass:
            def __init__(self):
                self.metrics = mock_metrics

            @performance_monitor
            def test_method(self, value):
                time.sleep(0.05)  # Simulate work
                return value * 2

        obj = TestClass()
        result = obj.test_method(5)

        assert result == 10
        assert mock_metrics.operation_count == 1
        assert mock_metrics.total_duration > 0.05
        assert mock_metrics.error_count == 0

    @pytest.mark.asyncio
    async def test_error_monitoring(self):
        """Test error monitoring."""
        mock_metrics = Mock()
        mock_metrics.operation_count = 0
        mock_metrics.error_count = 0

        class TestClass:
            def __init__(self):
                self.metrics = mock_metrics

            @performance_monitor
            async def test_method(self):
                raise ValueError("Test error")

        obj = TestClass()

        with pytest.raises(ValueError):
            await obj.test_method()

        assert mock_metrics.error_count == 1


class TestIntegratedContainerFilter:
    """Test IntegratedContainerFilter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_client = Mock()
        self.filter = IntegratedContainerFilter(
            cpln_client=self.mock_client, cache_size=10, cache_ttl=300
        )

    def test_initialization(self):
        """Test filter initialization."""
        assert self.filter.cpln_client == self.mock_client
        assert self.filter.cache.max_size == 10
        assert self.filter.cache.default_ttl == 300
        assert self.filter.metrics is not None

    @pytest.mark.asyncio
    async def test_filter_containers_basic(self):
        """Test basic container filtering."""
        # Mock enhanced filter
        expected_result = {
            "containers": [
                {"name": "container1", "image": "nginx:latest"},
                {"name": "container2", "image": "redis:alpine"},
            ],
            "total_count": 2,
            "page_info": {"has_next_page": False},
        }
        self.filter.enhanced_filter.filter_containers_advanced = AsyncMock(
            return_value=expected_result
        )

        filter_options = ContainerFilterOptions(gvc="test-gvc")
        result = await self.filter.filter_containers(filter_options)

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_filter_containers_advanced(self):
        """Test advanced container filtering with query."""
        # Mock enhanced filter
        expected_result = {
            "containers": [{"name": "container1"}],
            "total_count": 1,
            "page_info": {"has_next_page": False},
        }
        self.filter.enhanced_filter.filter_containers_advanced = AsyncMock(
            return_value=expected_result
        )

        filter_options = ContainerFilterOptions(gvc="test-gvc")
        result = await self.filter.filter_containers(
            filter_options, query="status=running AND cpu>100m"
        )

        assert result == expected_result
        self.filter.enhanced_filter.filter_containers_advanced.assert_called_once()

    @pytest.mark.asyncio
    async def test_caching_functionality(self):
        """Test caching functionality."""
        # Mock enhanced filter
        expected_result = {"containers": [{"name": "container1"}], "total_count": 1}
        self.filter.enhanced_filter.filter_containers_advanced = AsyncMock(
            return_value=expected_result
        )

        filter_options = ContainerFilterOptions(gvc="test-gvc")

        # First call - should hit the mock
        result1 = await self.filter.filter_containers(filter_options, use_cache=True)
        assert self.filter.enhanced_filter.filter_containers_advanced.call_count == 1

        # Second call - should use cache
        result2 = await self.filter.filter_containers(filter_options, use_cache=True)
        assert (
            self.filter.enhanced_filter.filter_containers_advanced.call_count == 1
        )  # No additional call
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test behavior when caching is disabled."""
        # Mock enhanced filter
        expected_result = {"containers": [{"name": "container1"}], "total_count": 1}
        self.filter.enhanced_filter.filter_containers_advanced = AsyncMock(
            return_value=expected_result
        )

        filter_options = ContainerFilterOptions(gvc="test-gvc")

        # Two calls with caching disabled
        await self.filter.filter_containers(filter_options, use_cache=False)
        await self.filter.filter_containers(filter_options, use_cache=False)

        # Should call mock twice
        assert self.filter.enhanced_filter.filter_containers_advanced.call_count == 2

    def test_get_metrics(self):
        """Test metrics retrieval."""
        # Simulate some operations
        self.filter.metrics.operation_count = 5
        self.filter.metrics.total_duration = 2.5
        self.filter.metrics.cache_hits = 3
        self.filter.metrics.cache_misses = 2

        metrics = self.filter.get_metrics()

        assert metrics["operations"]["count"] == 5
        assert metrics["operations"]["average_duration"] == 0.5
        assert metrics["cache"]["hits"] == 3
        assert metrics["cache"]["misses"] == 2
        assert metrics["cache"]["hit_rate"] == 0.6

    def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        # Add some test data to cache
        self.filter.cache.put("key1", "data1", ttl=1)
        self.filter.cache.put("key2", "data2", ttl=10)

        # Wait for first entry to expire
        time.sleep(1.1)

        # Cleanup
        result = self.filter.cleanup_cache()

        assert result["expired_entries_removed"] == 1
        assert result["current_cache_size"] == 1

    def test_reset_metrics(self):
        """Test metrics reset."""
        # Set some metrics
        self.filter.metrics.operation_count = 10
        self.filter.metrics.error_count = 2

        # Reset
        self.filter.reset_metrics()

        assert self.filter.metrics.operation_count == 0
        assert self.filter.metrics.error_count == 0

    def test_clear_cache(self):
        """Test cache clearing."""
        # Add data to cache
        self.filter.cache.put("key1", "data1")

        # Clear cache
        self.filter.clear_cache()

        assert len(self.filter.cache._cache) == 0


class TestCLIIntegration:
    """Test CLI integration functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_filter = Mock()
        self.cli = CLIIntegration(self.mock_filter)

    @pytest.mark.asyncio
    async def test_execute_filter_command_success(self):
        """Test successful filter command execution."""
        # Mock filter response
        filter_result = {"containers": [{"name": "container1"}], "total_count": 1}
        self.mock_filter.filter_containers = AsyncMock(return_value=filter_result)
        self.mock_filter.get_metrics = Mock(return_value={"operations": {"count": 1}})

        # CLI arguments
        args = {
            "gvc": "test-gvc",
            "workload": "test-workload",
            "query": "status=running",
            "format": "json",
            "show_metrics": True,
        }

        result = await self.cli.execute_filter_command(args)

        assert result["success"] is True
        assert result["data"] == filter_result
        assert result["metrics"] is not None

    @pytest.mark.asyncio
    async def test_execute_filter_command_error(self):
        """Test filter command execution with error."""
        # Mock filter to raise exception
        self.mock_filter.filter_containers = AsyncMock(
            side_effect=Exception("Test error")
        )
        self.mock_filter.get_metrics = Mock(return_value=None)

        args = {"gvc": "test-gvc"}
        result = await self.cli.execute_filter_command(args)

        assert result["success"] is False
        assert "Test error" in result["error"]

    def test_parse_filter_args(self):
        """Test CLI argument parsing."""
        args = {
            "gvc": "test-gvc",
            "workload": "test-workload",
            "image": "nginx:*",
            "status": "running",
            "labels": {"env": "prod", "team": "backend"},
        }

        filter_options = self.cli._parse_filter_args(args)

        assert filter_options.gvc == "test-gvc"
        assert filter_options.workload == "test-workload"
        assert filter_options.image == "nginx:*"
        assert filter_options.status == "running"
        assert filter_options.labels == {"env": "prod", "team": "backend"}

    def test_format_as_table(self):
        """Test table formatting."""
        result = {
            "containers": [
                {
                    "name": "container1",
                    "image": "nginx:latest",
                    "status": "running",
                    "gvc": "test-gvc",
                    "workload": "web",
                    "resources": {"cpu": "100m", "memory": "128Mi"},
                }
            ]
        }

        table_data = self.cli._format_as_table(result)

        assert len(table_data) == 1
        assert table_data[0]["Name"] == "container1"
        assert table_data[0]["Image"] == "nginx:latest"
        assert table_data[0]["Status"] == "running"
        assert table_data[0]["CPU"] == "100m"
        assert table_data[0]["Memory"] == "128Mi"

    def test_format_as_csv(self):
        """Test CSV formatting."""
        result = {
            "containers": [
                {
                    "name": "container1",
                    "image": "nginx:latest",
                    "status": "running",
                    "gvc": "test-gvc",
                    "workload": "web",
                    "resources": {"cpu": "100m", "memory": "128Mi"},
                },
                {
                    "name": "container2",
                    "image": "redis:alpine",
                    "status": "running",
                    "gvc": "test-gvc",
                    "workload": "cache",
                    "resources": {"cpu": "50m", "memory": "64Mi"},
                },
            ]
        }

        csv_output = self.cli._format_as_csv(result)
        lines = csv_output.split("\n")

        assert len(lines) == 3  # Header + 2 data rows
        assert lines[0] == "Name,Image,Status,GVC,Workload,CPU,Memory"
        assert "container1" in lines[1]
        assert "container2" in lines[2]

    def test_format_empty_csv(self):
        """Test CSV formatting with empty results."""
        result = {"containers": []}
        csv_output = self.cli._format_as_csv(result)
        assert csv_output == ""


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_quick_filter(self):
        """Test quick filter function."""
        mock_client = Mock()

        with patch("cpln.filters.integration.IntegratedContainerFilter") as MockFilter:
            mock_filter_instance = Mock()
            mock_filter_instance.filter_containers = AsyncMock(
                return_value={"containers": [{"name": "test"}]}
            )
            MockFilter.return_value = mock_filter_instance

            result = await quick_filter(
                cpln_client=mock_client, gvc="test-gvc", query="status=running"
            )

            assert result == [{"name": "test"}]
            MockFilter.assert_called_once_with(mock_client)

    def test_create_production_filter(self):
        """Test production filter creation."""
        mock_client = Mock()

        with patch("cpln.filters.integration.IntegratedContainerFilter") as MockFilter:
            create_production_filter(mock_client, cache_size=5000, cache_ttl=900)

            MockFilter.assert_called_once_with(
                cpln_client=mock_client,
                cache_size=5000,
                cache_ttl=900,
                enable_metrics=True,
            )


if __name__ == "__main__":
    pytest.main([__file__])
