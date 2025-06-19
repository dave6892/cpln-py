"""Container filtering utilities for cpln-py.

This module provides comprehensive container filtering capabilities:
- Phase 1: Basic filtering with standard options
- Phase 2: Advanced filtering with query parsing and enhanced features
- Phase 3: Integration features with caching, monitoring, and CLI support
"""

from .container import ContainerFilterOptions
from .enhanced import (
    ContainerTimeInfo,
    CrossWorkloadContainerDiscovery,
    EnhancedContainerFilter,
    EnhancedContainerInfo,
    PaginationOptions,
    SortField,
    SortOptions,
    SortOrder,
    create_advanced_filter,
    create_cross_workload_discovery,
)
from .integration import (
    CLIIntegration,
    FilterCache,
    FilterMetrics,
    IntegratedContainerFilter,
    create_production_filter,
    quick_filter,
)
from .query_parser import (
    AdvancedQueryParser,
    LogicalExpression,
    QueryExpression,
    QueryParseError,
    parse_advanced_query,
)

__all__ = [
    # Phase 1 - Basic filtering
    "ContainerFilterOptions",
    # Phase 2 - Advanced query parsing
    "AdvancedQueryParser",
    "QueryExpression",
    "LogicalExpression",
    "QueryParseError",
    "parse_advanced_query",
    # Phase 2 - Enhanced filtering
    "EnhancedContainerFilter",
    "EnhancedContainerInfo",
    "ContainerTimeInfo",
    "SortField",
    "SortOrder",
    "SortOptions",
    "PaginationOptions",
    "CrossWorkloadContainerDiscovery",
    "create_advanced_filter",
    "create_cross_workload_discovery",
    # Phase 3 - Integration features
    "IntegratedContainerFilter",
    "CLIIntegration",
    "FilterMetrics",
    "FilterCache",
    "quick_filter",
    "create_production_filter",
]
