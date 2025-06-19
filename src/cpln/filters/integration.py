"""
Phase 3: Integration and production-ready features for container filtering.

This module provides:
- CLI integration for container filtering commands
- Caching and performance optimizations
- Monitoring and metrics collection
- Production-ready error handling and logging
- Integration with existing cpln-py workflows
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional

from .container import ContainerFilterOptions
from .enhanced import CrossWorkloadContainerDiscovery, EnhancedContainerFilter
from .query_parser import AdvancedQueryParser

logger = logging.getLogger(__name__)


@dataclass
class FilterMetrics:
    """Metrics for filter operations."""

    operation_count: int = 0
    total_duration: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0
    last_operation_time: Optional[datetime] = None

    @property
    def average_duration(self) -> float:
        """Calculate average operation duration."""
        return self.total_duration / max(1, self.operation_count)

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_requests = self.cache_hits + self.cache_misses
        return self.cache_hits / max(1, total_requests)


@dataclass
class CacheEntry:
    """Cache entry for filter results."""

    data: Any
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minutes default
    access_count: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)

    def access(self) -> Any:
        """Access cached data and increment counter."""
        self.access_count += 1
        return self.data


class FilterCache:
    """Cache for filter operations with TTL and LRU eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []

    def _generate_key(
        self, filter_options: ContainerFilterOptions, query: str = ""
    ) -> str:
        """Generate a cache key from filter options and query."""
        key_data = {
            "gvc": filter_options.gvc,
            "workload": filter_options.workload,
            "image": filter_options.image,
            "status": filter_options.status,
            "labels": dict(filter_options.labels) if filter_options.labels else {},
            "query": query,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached data if available and not expired."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            self._remove(key)
            return None

        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return entry.access()

    def put(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Store data in cache with optional TTL."""
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(
            data=data, timestamp=datetime.now(), ttl_seconds=ttl
        )

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _remove(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            lru_key = self._access_order[0]
            self._remove(lru_key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]

        for key in expired_keys:
            self._remove(key)

        return len(expired_keys)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_access = sum(entry.access_count for entry in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_accesses": total_access,
            "expired_entries": sum(
                1 for entry in self._cache.values() if entry.is_expired()
            ),
        }


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor performance of filter operations."""

    @wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = await func(self, *args, **kwargs)
            duration = time.time() - start_time
            self.metrics.operation_count += 1
            self.metrics.total_duration += duration
            self.metrics.last_operation_time = datetime.now()

            logger.debug(
                f"Filter operation {func.__name__} completed in {duration:.3f}s"
            )
            return result
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Filter operation {func.__name__} failed: {e}")
            raise

    @wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            duration = time.time() - start_time
            self.metrics.operation_count += 1
            self.metrics.total_duration += duration
            self.metrics.last_operation_time = datetime.now()

            logger.debug(
                f"Filter operation {func.__name__} completed in {duration:.3f}s"
            )
            return result
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Filter operation {func.__name__} failed: {e}")
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class IntegratedContainerFilter:
    """
    Production-ready container filter with caching, monitoring, and CLI integration.
    """

    def __init__(
        self,
        cpln_client=None,
        cache_size: int = 1000,
        cache_ttl: int = 300,
        enable_metrics: bool = True,
    ):
        self.cpln_client = cpln_client
        self.cache = FilterCache(max_size=cache_size, default_ttl=cache_ttl)
        self.metrics = FilterMetrics() if enable_metrics else None
        self.query_parser = AdvancedQueryParser()

        # Initialize component filters
        self.enhanced_filter = EnhancedContainerFilter(cpln_client)
        self.discovery = CrossWorkloadContainerDiscovery(cpln_client)

        logger.info("IntegratedContainerFilter initialized with caching and monitoring")

    @performance_monitor
    async def filter_containers(
        self,
        filter_options: ContainerFilterOptions,
        query: str = "",
        use_cache: bool = True,
        sort_by: Optional[list[str]] = None,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Filter containers with caching and performance monitoring.

        Args:
            filter_options: Basic filter options
            query: Advanced query string (Phase 2 feature)
            use_cache: Whether to use caching
            sort_by: Sort fields
            page_size: Pagination size
            page_token: Pagination token

        Returns:
            Filtered container results with metadata
        """
        # Generate cache key
        cache_key = None
        if use_cache:
            cache_key = self.cache._generate_key(filter_options, query)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                if self.metrics:
                    self.metrics.cache_hits += 1
                logger.debug("Cache hit for filter operation")
                return cached_result
            elif self.metrics:
                self.metrics.cache_misses += 1

        # Use enhanced filtering for all queries (handles both basic and advanced)
        result = await self.enhanced_filter.filter_containers_advanced(
            filter_options=filter_options,
            query=query,
            sort_by=sort_by,
            page_size=page_size,
            page_token=page_token,
        )

        # Cache the result
        if use_cache and cache_key:
            self.cache.put(cache_key, result)

        return result

    @performance_monitor
    async def discover_containers(
        self, discovery_options: dict[str, Any], use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Discover containers across workloads with caching.

        Args:
            discovery_options: Discovery configuration
            use_cache: Whether to use caching

        Returns:
            Discovery results with metadata
        """
        if use_cache:
            cache_key = f"discovery_{hashlib.md5(json.dumps(discovery_options, sort_keys=True).encode()).hexdigest()}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                if self.metrics:
                    self.metrics.cache_hits += 1
                return cached_result
            elif self.metrics:
                self.metrics.cache_misses += 1

        # Perform discovery
        result = await self.discovery.discover_containers(discovery_options)

        # Cache the result
        if use_cache:
            self.cache.put(cache_key, result)

        return result

    def get_metrics(self) -> Optional[dict[str, Any]]:
        """Get performance metrics."""
        if not self.metrics:
            return None

        cache_stats = self.cache.stats()

        return {
            "operations": {
                "count": self.metrics.operation_count,
                "total_duration": self.metrics.total_duration,
                "average_duration": self.metrics.average_duration,
                "error_count": self.metrics.error_count,
                "last_operation": self.metrics.last_operation_time.isoformat()
                if self.metrics.last_operation_time
                else None,
            },
            "cache": {
                **cache_stats,
                "hit_rate": self.metrics.cache_hit_rate,
                "hits": self.metrics.cache_hits,
                "misses": self.metrics.cache_misses,
            },
        }

    def cleanup_cache(self) -> dict[str, int]:
        """Clean up expired cache entries."""
        expired_count = self.cache.cleanup_expired()
        return {
            "expired_entries_removed": expired_count,
            "current_cache_size": len(self.cache._cache),
        }

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        if self.metrics:
            self.metrics = FilterMetrics()

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()


class CLIIntegration:
    """CLI integration for container filtering commands."""

    def __init__(self, integrated_filter: IntegratedContainerFilter):
        self.filter = integrated_filter

    async def execute_filter_command(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a filter command with CLI arguments.

        Args:
            args: CLI arguments dictionary

        Returns:
            Command execution results
        """
        try:
            # Parse CLI arguments into filter options
            filter_options = self._parse_filter_args(args)

            # Extract additional options
            query = args.get("query", "")
            sort_by = args.get("sort_by", [])
            page_size = args.get("page_size")
            output_format = args.get("format", "json")
            use_cache = args.get("cache", True)

            # Execute filter
            result = await self.filter.filter_containers(
                filter_options=filter_options,
                query=query,
                sort_by=sort_by,
                page_size=page_size,
                use_cache=use_cache,
            )

            # Format output
            formatted_result = self._format_output(result, output_format)

            return {
                "success": True,
                "data": formatted_result,
                "metrics": self.filter.get_metrics()
                if args.get("show_metrics")
                else None,
            }

        except Exception as e:
            logger.error(f"CLI filter command failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "metrics": self.filter.get_metrics()
                if args.get("show_metrics")
                else None,
            }

    def _parse_filter_args(self, args: dict[str, Any]) -> ContainerFilterOptions:
        """Parse CLI arguments into ContainerFilterOptions."""
        return ContainerFilterOptions(
            gvc=args.get("gvc"),
            workload=args.get("workload"),
            image=args.get("image"),
            status=args.get("status"),
            labels=dict(args.get("labels", {})),
        )

    def _format_output(self, result: dict[str, Any], format_type: str) -> Any:
        """Format output according to specified format."""
        if format_type == "json":
            return result
        elif format_type == "table":
            return self._format_as_table(result)
        elif format_type == "csv":
            return self._format_as_csv(result)
        else:
            return result

    def _format_as_table(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        """Format results as table data."""
        containers = result.get("containers", [])
        table_data = []

        for container in containers:
            table_data.append(
                {
                    "Name": container.get("name", "N/A"),
                    "Image": container.get("image", "N/A"),
                    "Status": container.get("status", "N/A"),
                    "GVC": container.get("gvc", "N/A"),
                    "Workload": container.get("workload", "N/A"),
                    "CPU": container.get("resources", {}).get("cpu", "N/A"),
                    "Memory": container.get("resources", {}).get("memory", "N/A"),
                }
            )

        return table_data

    def _format_as_csv(self, result: dict[str, Any]) -> str:
        """Format results as CSV string."""
        containers = result.get("containers", [])
        if not containers:
            return ""

        # CSV headers
        headers = ["Name", "Image", "Status", "GVC", "Workload", "CPU", "Memory"]
        csv_lines = [",".join(headers)]

        # CSV data rows
        for container in containers:
            row = [
                container.get("name", ""),
                container.get("image", ""),
                container.get("status", ""),
                container.get("gvc", ""),
                container.get("workload", ""),
                str(container.get("resources", {}).get("cpu", "")),
                str(container.get("resources", {}).get("memory", "")),
            ]
            csv_lines.append(",".join(row))

        return "\n".join(csv_lines)


# Convenience functions for easy integration
async def quick_filter(
    cpln_client,
    gvc: str = None,
    workload: str = None,
    query: str = "",
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Quick container filtering function for simple use cases."""
    filter_options = ContainerFilterOptions(gvc=gvc, workload=workload)
    integrated_filter = IntegratedContainerFilter(cpln_client)

    result = await integrated_filter.filter_containers(
        filter_options=filter_options, query=query, use_cache=use_cache
    )

    return result.get("containers", [])


def create_production_filter(
    cpln_client, cache_size: int = 2000, cache_ttl: int = 600
) -> IntegratedContainerFilter:
    """Create a production-ready filter with optimized settings."""
    return IntegratedContainerFilter(
        cpln_client=cpln_client,
        cache_size=cache_size,
        cache_ttl=cache_ttl,
        enable_metrics=True,
    )
