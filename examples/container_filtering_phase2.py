#!/usr/bin/env python3
"""
Example script demonstrating Phase 2 advanced container filtering capabilities.

This script showcases:
- Complex query syntax with logical operators
- Time-based filtering
- Cross-workload container discovery
- Advanced sorting and pagination
- Query expression evaluation

Usage:
    python examples/container_filtering_phase2.py
"""

import importlib.util
import os
import sys
from datetime import datetime, timedelta

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, src_path)
sys.path.insert(0, os.path.join(src_path, "cpln", "filters"))

# Import Phase 2 modules directly to avoid dependency issues

# Load container module first
spec = importlib.util.spec_from_file_location(
    "container", os.path.join(src_path, "cpln", "filters", "container.py")
)
container_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(container_module)

# Load query parser
spec = importlib.util.spec_from_file_location(
    "query_parser", os.path.join(src_path, "cpln", "filters", "query_parser.py")
)
query_parser_module = importlib.util.module_from_spec(spec)
# Set up the container module for relative import
query_parser_module.ContainerFilterOptions = container_module.ContainerFilterOptions
spec.loader.exec_module(query_parser_module)

# Load enhanced module
spec = importlib.util.spec_from_file_location(
    "enhanced", os.path.join(src_path, "cpln", "filters", "enhanced.py")
)
enhanced_module = importlib.util.module_from_spec(spec)
# Set up dependencies
enhanced_module._match_patterns = container_module._match_patterns
enhanced_module._match_resource_thresholds = container_module._match_resource_thresholds
enhanced_module.ContainerFilterOptions = container_module.ContainerFilterOptions
enhanced_module.AdvancedQueryParser = query_parser_module.AdvancedQueryParser
enhanced_module.QueryExpression = query_parser_module.QueryExpression
enhanced_module.LogicalExpression = query_parser_module.LogicalExpression
enhanced_module.QueryParseError = query_parser_module.QueryParseError
spec.loader.exec_module(enhanced_module)

# Extract classes
AdvancedQueryParser = query_parser_module.AdvancedQueryParser
parse_advanced_query = query_parser_module.parse_advanced_query
QueryParseError = query_parser_module.QueryParseError

EnhancedContainerFilter = enhanced_module.EnhancedContainerFilter
EnhancedContainerInfo = enhanced_module.EnhancedContainerInfo
ContainerTimeInfo = enhanced_module.ContainerTimeInfo
SortField = enhanced_module.SortField
SortOrder = enhanced_module.SortOrder
SortOptions = enhanced_module.SortOptions
PaginationOptions = enhanced_module.PaginationOptions
CrossWorkloadContainerDiscovery = enhanced_module.CrossWorkloadContainerDiscovery


def create_sample_containers():
    """Create sample container data for demonstration."""
    now = datetime.now()

    containers = [
        EnhancedContainerInfo(
            name="web-nginx-1",
            image="nginx:1.21",
            workload_name="web-frontend",
            gvc="production",
            location="us-west-2",
            health_status="healthy",
            resource_usage={"cpu": 45.0, "memory": 60.0, "replica_utilization": 85.0},
            time_info=ContainerTimeInfo(
                created=now - timedelta(days=10),
                updated=now - timedelta(hours=2),
                last_health_check=now - timedelta(minutes=5),
            ),
            labels={"app": "frontend", "tier": "web"},
            annotations={"version": "1.21.0"},
        ),
        EnhancedContainerInfo(
            name="api-python-1",
            image="python:3.9-slim",
            workload_name="api-backend",
            gvc="production",
            location="us-west-2",
            health_status="unhealthy",
            resource_usage={"cpu": 78.0, "memory": 85.0, "replica_utilization": 60.0},
            time_info=ContainerTimeInfo(
                created=now - timedelta(days=5),
                updated=now - timedelta(minutes=30),
                last_restart=now - timedelta(hours=1),
            ),
            labels={"app": "backend", "tier": "api"},
            annotations={"version": "3.9.18"},
        ),
        EnhancedContainerInfo(
            name="cache-redis-1",
            image="redis:6.2-alpine",
            workload_name="cache-service",
            gvc="production",
            location="us-east-1",
            health_status="healthy",
            resource_usage={"cpu": 25.0, "memory": 40.0, "replica_utilization": 95.0},
            time_info=ContainerTimeInfo(
                created=now - timedelta(days=15),
                updated=now - timedelta(days=1),
                last_health_check=now - timedelta(minutes=1),
            ),
            labels={"app": "cache", "tier": "data"},
            annotations={"version": "6.2.14"},
        ),
        EnhancedContainerInfo(
            name="db-postgres-1",
            image="postgres:14",
            workload_name="database",
            gvc="staging",
            location="us-west-2",
            health_status="degraded",
            resource_usage={"cpu": 65.0, "memory": 70.0, "replica_utilization": 80.0},
            time_info=ContainerTimeInfo(
                created=now - timedelta(days=20),
                updated=now - timedelta(hours=6),
                last_health_check=now - timedelta(minutes=10),
            ),
            labels={"app": "database", "tier": "data"},
            annotations={"version": "14.9"},
        ),
        EnhancedContainerInfo(
            name="worker-celery-1",
            image="python:3.9",
            workload_name="background-workers",
            gvc="staging",
            location="us-east-1",
            health_status="healthy",
            resource_usage={"cpu": 35.0, "memory": 55.0, "replica_utilization": 70.0},
            time_info=ContainerTimeInfo(
                created=now - timedelta(days=8),
                updated=now - timedelta(hours=4),
                last_health_check=now - timedelta(minutes=3),
            ),
            labels={"app": "workers", "tier": "processing"},
            annotations={"version": "3.9.18"},
        ),
    ]

    return containers


def demonstrate_query_parsing():
    """Demonstrate advanced query parsing capabilities."""
    print("🔍 ADVANCED QUERY PARSING EXAMPLES")
    print("=" * 50)

    parser = AdvancedQueryParser()

    queries = [
        "image:nginx*",
        "cpu>50 AND memory<80",
        "(health:healthy OR health:degraded) AND gvc:production",
        "NOT health:unhealthy",
        "created_after:2024-01-01",
        "updated_within:7d",
        'name:"web-*" AND location:us-west-2',
        "replica_utilization>=80 OR cpu>70",
    ]

    for query in queries:
        try:
            result = parser.parse(query)
            print(f"✅ Query: {query}")
            print(f"   Parsed successfully: {type(result).__name__}")
            print()
        except QueryParseError as e:
            print(f"❌ Query: {query}")
            print(f"   Error: {e}")
            print()


def demonstrate_enhanced_filtering():
    """Demonstrate enhanced container filtering with complex queries."""
    print("🎯 ENHANCED CONTAINER FILTERING")
    print("=" * 50)

    containers = create_sample_containers()
    filter_engine = EnhancedContainerFilter()

    # Example queries to demonstrate
    test_queries = [
        {
            "name": "Find all healthy containers",
            "query": "health:healthy",
        },
        {
            "name": "Find containers with high resource usage",
            "query": "cpu>60 OR memory>80",
        },
        {
            "name": "Find production containers that are healthy",
            "query": "gvc:production AND health:healthy",
        },
        {
            "name": "Find containers in US West region with high replica utilization",
            "query": "location:us-west-2 AND replica_utilization>80",
        },
        {
            "name": "Find containers excluding unhealthy ones",
            "query": "NOT health:unhealthy",
        },
        {
            "name": "Find recently updated containers (within 1 day)",
            "query": "updated_within:1d",
        },
    ]

    for test in test_queries:
        print(f"📋 {test['name']}")
        print(f"   Query: {test['query']}")

        try:
            results = filter_engine.filter_containers_by_query(
                containers, test["query"]
            )
            print(f"   Results: {len(results)} containers found")

            for container in results:
                health_icon = (
                    "🟢"
                    if container.health_status == "healthy"
                    else "🔴"
                    if container.health_status == "unhealthy"
                    else "🟡"
                )
                print(
                    f"     {health_icon} {container.name} ({container.gvc}) - {container.health_status}"
                )

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()


def demonstrate_sorting_and_pagination():
    """Demonstrate advanced sorting and pagination."""
    print("📊 SORTING AND PAGINATION")
    print("=" * 50)

    containers = create_sample_containers()
    filter_engine = EnhancedContainerFilter()

    # Demonstrate sorting
    print("🔀 Sorting Examples:")
    print()

    # Sort by health status (healthy first), then by CPU usage (high to low)
    sort_options = [
        SortOptions(SortField.HEALTH_STATUS, SortOrder.ASC),
        SortOptions(SortField.CPU_USAGE, SortOrder.DESC),
    ]

    sorted_containers = filter_engine.sort_containers(containers, sort_options)

    print("Containers sorted by health (healthy first), then CPU usage (high to low):")
    for i, container in enumerate(sorted_containers, 1):
        status_icon = {"healthy": "🟢", "unhealthy": "🔴", "degraded": "🟡"}.get(
            container.health_status, "⚪"
        )
        cpu_usage = container.resource_usage.get("cpu", 0)
        print(
            f"  {i}. {status_icon} {container.name} - {container.health_status} (CPU: {cpu_usage}%)"
        )

    print()

    # Demonstrate pagination
    print("📄 Pagination Example:")
    print()

    pagination = PaginationOptions(page=1, per_page=3)
    paginated_result = filter_engine.paginate_containers(sorted_containers, pagination)

    print(
        f"Page {paginated_result['pagination']['page']} of {paginated_result['pagination']['total_pages']}"
    )
    print(
        f"Showing {len(paginated_result['containers'])} of {paginated_result['pagination']['total_count']} containers:"
    )

    for i, container in enumerate(paginated_result["containers"], 1):
        print(f"  {i}. {container.name} ({container.gvc})")

    print(f"Has next page: {paginated_result['pagination']['has_next']}")
    print(f"Has previous page: {paginated_result['pagination']['has_prev']}")

    if paginated_result["pagination"]["has_next"]:
        print(f"Next page: {paginated_result['pagination']['next_page']}")

    print()


def demonstrate_time_based_filtering():
    """Demonstrate time-based filtering capabilities."""
    print("⏰ TIME-BASED FILTERING")
    print("=" * 50)

    containers = create_sample_containers()
    filter_engine = EnhancedContainerFilter()

    # Time-based query examples
    time_queries = [
        {
            "name": "Containers updated within last 1 hour",
            "query": "updated_within:1h",
        },
        {
            "name": "Containers updated within last 1 day",
            "query": "updated_within:1d",
        },
        {
            "name": "Containers created in the last week",
            "query": "updated_within:7d",
        },
    ]

    for test in time_queries:
        print(f"🕐 {test['name']}")
        print(f"   Query: {test['query']}")

        try:
            results = filter_engine.filter_containers_by_query(
                containers, test["query"]
            )
            print(f"   Results: {len(results)} containers found")

            for container in results:
                if container.time_info and container.time_info.updated:
                    time_ago = datetime.now() - container.time_info.updated
                    hours_ago = time_ago.total_seconds() / 3600
                    print(
                        f"     📦 {container.name} - updated {hours_ago:.1f} hours ago"
                    )
                else:
                    print(f"     📦 {container.name} - no update time available")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()


def demonstrate_cross_workload_discovery():
    """Demonstrate cross-workload container discovery (simulated)."""
    print("🌐 CROSS-WORKLOAD DISCOVERY")
    print("=" * 50)

    # Since we don't have a real client, we'll simulate the discovery process
    print("📡 Simulating cross-workload container discovery...")
    print()

    # Simulate containers from different GVCs
    containers_by_gvc = {
        "production": [
            EnhancedContainerInfo(
                name="web-nginx-prod",
                image="nginx:1.21",
                workload_name="web-app",
                gvc="production",
                health_status="healthy",
                resource_usage={"cpu": 45.0, "memory": 60.0},
            ),
            EnhancedContainerInfo(
                name="api-python-prod",
                image="python:3.9",
                workload_name="api-service",
                gvc="production",
                health_status="unhealthy",
                resource_usage={"cpu": 80.0, "memory": 85.0},
            ),
        ],
        "staging": [
            EnhancedContainerInfo(
                name="web-nginx-staging",
                image="nginx:1.20",
                workload_name="web-app",
                gvc="staging",
                health_status="healthy",
                resource_usage={"cpu": 30.0, "memory": 45.0},
            ),
        ],
        "development": [
            EnhancedContainerInfo(
                name="test-container",
                image="alpine:latest",
                workload_name="test-workload",
                gvc="development",
                health_status="healthy",
                resource_usage={"cpu": 10.0, "memory": 20.0},
            ),
        ],
    }

    # Simulate discovery results
    total_containers = sum(len(containers) for containers in containers_by_gvc.values())
    print(
        f"🔍 Discovered {total_containers} containers across {len(containers_by_gvc)} GVCs:"
    )
    print()

    for gvc, containers in containers_by_gvc.items():
        print(f"📋 GVC: {gvc} ({len(containers)} containers)")
        for container in containers:
            status_icon = "🟢" if container.health_status == "healthy" else "🔴"
            cpu = container.resource_usage.get("cpu", 0)
            print(f"  {status_icon} {container.name} - {container.image} (CPU: {cpu}%)")
        print()

    # Simulate filtering across all GVCs
    all_containers = [
        c for containers in containers_by_gvc.values() for c in containers
    ]
    filter_engine = EnhancedContainerFilter()

    print("🎯 Filtering across all GVCs for high CPU usage (>40%):")
    high_cpu_containers = filter_engine.filter_containers_by_query(
        all_containers, "cpu>40"
    )

    for container in high_cpu_containers:
        cpu = container.resource_usage.get("cpu", 0)
        print(f"  ⚡ {container.name} ({container.gvc}) - CPU: {cpu}%")

    print()


def main():
    """Main demonstration function."""
    print("🚀 CONTAINER FILTERING PHASE 2 - ADVANCED FEATURES DEMO")
    print("=" * 60)
    print()

    try:
        # Run all demonstrations
        demonstrate_query_parsing()
        print()

        demonstrate_enhanced_filtering()
        print()

        demonstrate_sorting_and_pagination()
        print()

        demonstrate_time_based_filtering()
        print()

        demonstrate_cross_workload_discovery()
        print()

        print("✅ All Phase 2 demonstrations completed successfully!")
        print()
        print("🎉 Phase 2 Features Summary:")
        print("  • Complex query syntax with AND/OR/NOT operators")
        print("  • Time-based filtering (created_after, updated_within, etc.)")
        print("  • Advanced sorting by multiple fields")
        print("  • Pagination with metadata")
        print("  • Cross-workload container discovery")
        print("  • Enhanced container information with metadata")
        print("  • Robust error handling and validation")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
