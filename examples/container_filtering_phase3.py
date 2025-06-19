#!/usr/bin/env python3
"""
Phase 3 Container Filtering Integration Demo

This script demonstrates the advanced integration features of the container filtering system:
- Production-ready filter with caching and monitoring
- Performance metrics collection and reporting
- CLI-style integration and output formatting
- Error handling and logging
- Integration with all previous phases

Run this script to see Phase 3 features in action.
"""

import asyncio
import logging
import time


# Mock CPLN client for demonstration
class MockCPLNClient:
    """Mock CPLN client that simulates real behavior."""

    def __init__(self):
        self.call_count = 0
        self.delay = 0.1  # Simulate network delay

    async def list_workloads(self, gvc: str = None):
        """Mock workload listing with simulated delay."""
        self.call_count += 1
        await asyncio.sleep(self.delay)

        workloads = [
            {
                "name": "web-frontend",
                "gvc": gvc or "production",
                "containers": [
                    {
                        "name": "nginx-container",
                        "image": "nginx:1.21",
                        "status": "running",
                        "labels": {"env": "prod", "tier": "frontend"},
                        "resources": {"cpu": "200m", "memory": "256Mi"},
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T12:00:00Z",
                    },
                    {
                        "name": "app-container",
                        "image": "myapp:v2.1",
                        "status": "running",
                        "labels": {"env": "prod", "tier": "frontend"},
                        "resources": {"cpu": "500m", "memory": "512Mi"},
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T12:00:00Z",
                    },
                ],
            },
            {
                "name": "backend-api",
                "gvc": gvc or "production",
                "containers": [
                    {
                        "name": "api-container",
                        "image": "api-service:v1.5",
                        "status": "running",
                        "labels": {"env": "prod", "tier": "backend"},
                        "resources": {"cpu": "1000m", "memory": "1Gi"},
                        "created_at": "2024-01-15T09:30:00Z",
                        "updated_at": "2024-01-15T11:45:00Z",
                    }
                ],
            },
            {
                "name": "data-processor",
                "gvc": gvc or "production",
                "containers": [
                    {
                        "name": "worker-container",
                        "image": "data-worker:latest",
                        "status": "pending",
                        "labels": {"env": "prod", "tier": "processing"},
                        "resources": {"cpu": "2000m", "memory": "2Gi"},
                        "created_at": "2024-01-15T11:00:00Z",
                        "updated_at": "2024-01-15T11:00:00Z",
                    }
                ],
            },
        ]

        if gvc:
            return [w for w in workloads if w["gvc"] == gvc]
        return workloads


async def demo_integrated_filtering():
    """Demonstrate integrated container filtering with caching and metrics."""
    print("🔧 Phase 3: Integrated Container Filtering Demo")
    print("=" * 60)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Import after path setup
    from cpln.filters.container import ContainerFilterOptions
    from cpln.filters.integration import (
        create_production_filter,
        quick_filter,
    )

    # Create mock client
    client = MockCPLNClient()

    print("\n1. Creating Production-Ready Filter")
    print("-" * 40)

    # Create production filter with optimized settings
    filter_system = create_production_filter(
        cpln_client=client, cache_size=2000, cache_ttl=600
    )

    print(f"✓ Created filter with cache size: {filter_system.cache.max_size}")
    print(f"✓ Cache TTL: {filter_system.cache.default_ttl}s")
    print(f"✓ Metrics enabled: {filter_system.metrics is not None}")

    print("\n2. Performance Monitoring Demo")
    print("-" * 40)

    # Perform several filter operations to generate metrics
    filter_options = ContainerFilterOptions(gvc="production")

    print("Executing filter operations...")

    # First operation (cache miss)
    start_time = time.time()
    await filter_system.filter_containers(filter_options)
    duration1 = time.time() - start_time
    print(f"✓ First operation: {duration1:.3f}s (cache miss)")

    # Second operation (cache hit)
    start_time = time.time()
    await filter_system.filter_containers(filter_options)
    duration2 = time.time() - start_time
    print(f"✓ Second operation: {duration2:.3f}s (cache hit)")

    # Advanced query operation
    query = "status=running AND (tier=frontend OR tier=backend)"
    start_time = time.time()
    await filter_system.filter_containers(filter_options, query=query)
    duration3 = time.time() - start_time
    print(f"✓ Advanced query: {duration3:.3f}s")

    print("\n3. Metrics Analysis")
    print("-" * 40)

    metrics = filter_system.get_metrics()
    if metrics:
        ops = metrics["operations"]
        cache = metrics["cache"]

        print(f"Operations performed: {ops['count']}")
        print(f"Total duration: {ops['total_duration']:.3f}s")
        print(f"Average duration: {ops['average_duration']:.3f}s")
        print(f"Cache hit rate: {cache['hit_rate']:.1%}")
        print(f"Cache hits: {cache['hits']}")
        print(f"Cache misses: {cache['misses']}")
        print(f"Current cache size: {cache['size']}")

    print("\n4. Cache Management Demo")
    print("-" * 40)

    # Show cache statistics
    cache_stats = filter_system.cache.stats()
    print(f"Cache utilization: {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"Total cache accesses: {cache_stats['total_accesses']}")

    # Cleanup expired entries
    cleanup_result = filter_system.cleanup_cache()
    print(f"Expired entries removed: {cleanup_result['expired_entries_removed']}")

    print("\n5. CLI Integration Demo")
    print("-" * 40)

    from cpln.filters.integration import CLIIntegration

    cli = CLIIntegration(filter_system)

    # Simulate CLI commands
    cli_args = {
        "gvc": "production",
        "query": "status=running",
        "format": "json",
        "show_metrics": True,
        "sort_by": ["name"],
        "page_size": 10,
    }

    print("Executing CLI-style command...")
    cli_result = await cli.execute_filter_command(cli_args)

    if cli_result["success"]:
        print("✓ CLI command executed successfully")
        print(f"  Containers found: {len(cli_result['data']['containers'])}")
        if cli_result["metrics"]:
            print(f"  Operations: {cli_result['metrics']['operations']['count']}")
    else:
        print(f"✗ CLI command failed: {cli_result['error']}")

    print("\n6. Output Formatting Demo")
    print("-" * 40)

    # Test different output formats
    result = {
        "containers": [
            {
                "name": "nginx-container",
                "image": "nginx:1.21",
                "status": "running",
                "gvc": "production",
                "workload": "web-frontend",
                "resources": {"cpu": "200m", "memory": "256Mi"},
            },
            {
                "name": "api-container",
                "image": "api-service:v1.5",
                "status": "running",
                "gvc": "production",
                "workload": "backend-api",
                "resources": {"cpu": "1000m", "memory": "1Gi"},
            },
        ]
    }

    # Table format
    table_data = cli._format_as_table(result)
    print("Table format preview:")
    for row in table_data[:2]:
        print(f"  {row['Name']:<20} {row['Image']:<20} {row['Status']:<10}")

    # CSV format
    csv_output = cli._format_as_csv(result)
    print("\nCSV format preview:")
    print("  " + csv_output.split("\n")[0])  # Header
    print("  " + csv_output.split("\n")[1])  # First row

    print("\n7. Error Handling Demo")
    print("-" * 40)

    # Simulate error condition
    try:
        # Invalid filter options to trigger error
        invalid_options = ContainerFilterOptions(gvc="non-existent-gvc")
        await filter_system.filter_containers(invalid_options, use_cache=False)
    except Exception as e:
        print(f"✓ Error handling working: {type(e).__name__}")

        # Check error metrics
        error_metrics = filter_system.get_metrics()
        print(f"Error count: {error_metrics['operations']['error_count']}")

    print("\n8. Quick Filter Convenience Function")
    print("-" * 40)

    # Demonstrate quick filter for simple use cases
    containers = await quick_filter(
        cpln_client=client, gvc="production", query="tier=frontend"
    )

    print(f"Quick filter found {len(containers)} frontend containers:")
    for container in containers:
        print(f"  - {container['name']} ({container['image']})")

    print("\n9. Production Configuration Demo")
    print("-" * 40)

    # Show different production configurations
    configurations = [
        {"name": "High Performance", "cache_size": 5000, "cache_ttl": 300},
        {"name": "Balanced", "cache_size": 2000, "cache_ttl": 600},
        {"name": "Memory Efficient", "cache_size": 500, "cache_ttl": 1200},
    ]

    for config in configurations:
        create_production_filter(
            cpln_client=client,
            cache_size=config["cache_size"],
            cache_ttl=config["cache_ttl"],
        )

        print(
            f"✓ {config['name']}: "
            f"cache={config['cache_size']}, "
            f"ttl={config['cache_ttl']}s"
        )

    print("\n10. Integration Summary")
    print("-" * 40)

    final_metrics = filter_system.get_metrics()
    if final_metrics:
        ops = final_metrics["operations"]
        print(f"Total operations executed: {ops['count']}")
        print(f"Average response time: {ops['average_duration']:.3f}s")
        print(f"Cache efficiency: {final_metrics['cache']['hit_rate']:.1%}")
        print(
            f"System reliability: {(ops['count'] - ops['error_count']) / max(1, ops['count']):.1%}"
        )

    print("\n✅ Phase 3 Integration Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("  • Production-ready filtering with caching")
    print("  • Performance monitoring and metrics")
    print("  • CLI integration and multiple output formats")
    print("  • Error handling and reliability")
    print("  • Convenience functions for common use cases")
    print("  • Configurable production settings")


async def demo_real_world_scenarios():
    """Demonstrate real-world usage scenarios."""
    print("\n" + "=" * 60)
    print("🌍 Real-World Integration Scenarios")
    print("=" * 60)

    from cpln.filters.container import ContainerFilterOptions
    from cpln.filters.integration import IntegratedContainerFilter

    client = MockCPLNClient()
    filter_system = IntegratedContainerFilter(client, cache_size=1000, cache_ttl=300)

    scenarios = [
        {
            "name": "DevOps Dashboard Query",
            "options": ContainerFilterOptions(gvc="production"),
            "query": "status=running AND cpu>500m",
            "description": "Find high-CPU containers in production",
        },
        {
            "name": "Troubleshooting Query",
            "options": ContainerFilterOptions(gvc="production"),
            "query": "status!=running OR memory>1Gi",
            "description": "Find problematic containers",
        },
        {
            "name": "Resource Planning Query",
            "options": ContainerFilterOptions(),
            "query": "tier=backend AND created_after='2024-01-15'",
            "description": "Analyze recent backend deployments",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Query: {scenario['query']}")

        start_time = time.time()
        result = await filter_system.filter_containers(
            scenario["options"], query=scenario["query"]
        )
        duration = time.time() - start_time

        print(f"   ✓ Found {len(result['containers'])} containers in {duration:.3f}s")

    # Show final performance summary
    metrics = filter_system.get_metrics()
    if metrics:
        print("\nPerformance Summary:")
        print(f"  Average query time: {metrics['operations']['average_duration']:.3f}s")
        print(f"  Cache efficiency: {metrics['cache']['hit_rate']:.1%}")


def main():
    """Main demonstration function."""
    print("🚀 Container Filtering System - Phase 3 Integration")
    print("Advanced production-ready features with caching and monitoring")
    print()

    # Add the src directory to Python path for imports
    import sys
    from pathlib import Path

    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))

    # Run the demos
    asyncio.run(demo_integrated_filtering())
    asyncio.run(demo_real_world_scenarios())


if __name__ == "__main__":
    main()
