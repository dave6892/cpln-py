#!/usr/bin/env python3
"""
Example: Container Filtering Phase 1 - Basic Filtering

This example demonstrates the basic container filtering capabilities implemented
in Phase 1 of Issue 32. It shows how to filter containers within workloads
using the new ContainerFilterOptions class.

Usage:
    python examples/container_filtering_phase1.py [gvc-name] [workload-name]
"""

import os
import sys

# Add the src directory to the path to import cpln
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ruff: noqa: E402
import cpln
from cpln.config import WorkloadConfig
from cpln.filters.container import ContainerFilterOptions


def demonstrate_workload_container_filtering(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    Demonstrate container filtering within a workload.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
    """
    print(f"\n=== Workload Container Filtering: {workload_name} ===")

    try:
        # Create config and get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        # Example 1: Get all containers (no filtering)
        print("\n1. All containers in workload:")
        all_containers = workload.find_containers()
        print(f"   Total containers: {len(all_containers)}")
        for container in all_containers:
            print(f"   - {container.name}: {container.image}")

        # Example 2: Filter by image patterns
        print("\n2. Filter by image patterns (nginx*, redis*):")
        filters = ContainerFilterOptions(image_patterns=["nginx*", "redis*"])
        filtered_containers = workload.find_containers(filters)
        print(f"   Matching containers: {len(filtered_containers)}")
        for container in filtered_containers:
            print(f"   - {container.name}: {container.image}")

        # Example 3: Filter by container name patterns
        print("\n3. Filter by name patterns (web-*, api-*):")
        filters = ContainerFilterOptions(name_patterns=["web-*", "api-*"])
        filtered_containers = workload.find_containers(filters)
        print(f"   Matching containers: {len(filtered_containers)}")
        for container in filtered_containers:
            print(f"   - {container.name}: {container.image}")

        # Example 4: Filter by port numbers
        print("\n4. Filter by exposed ports (80, 443):")
        filters = ContainerFilterOptions(port_filters=[80, 443])
        filtered_containers = workload.find_containers(filters)
        print(f"   Containers with ports 80 or 443: {len(filtered_containers)}")
        for container in filtered_containers:
            ports = [f"{port.number}/{port.protocol}" for port in container.ports]
            print(f"   - {container.name}: ports {ports}")

        # Example 5: Filter by environment variables
        print("\n5. Filter by environment variables:")
        # Note: This requires containers to have environment variables set
        filters = ContainerFilterOptions(environment_filters={"ENV": "production"})
        filtered_containers = workload.find_containers(filters)
        print(f"   Containers with ENV=production: {len(filtered_containers)}")
        for container in filtered_containers:
            print(f"   - {container.name}: env={container.env}")

        # Example 6: Container counting
        print("\n6. Container counting:")
        total_count = workload.count_containers()
        nginx_count = workload.count_containers(
            ContainerFilterOptions(image_patterns=["nginx*"])
        )
        print(f"   Total containers: {total_count}")
        print(f"   Nginx containers: {nginx_count}")

    except Exception as e:
        print(f"Error demonstrating filtering: {e}")


def demonstrate_deployment_container_filtering(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str, location: str
):
    """
    Demonstrate container filtering within a deployment (live data).

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
        location: Location for deployment
    """
    print(f"\n=== Deployment Container Filtering: {workload_name} @ {location} ===")

    try:
        # Create config and get the deployment
        config = WorkloadConfig(
            gvc=gvc_name, workload_id=workload_name, location=location
        )
        workload = client.workloads.get(config)
        deployment = workload.get_deployment(location=location)

        # Example 1: Get all live containers
        print("\n1. All live containers in deployment:")
        all_containers = deployment.get_containers()
        print(f"   Total live containers: {len(all_containers)}")
        for name, container in all_containers.items():
            health = "healthy" if container.is_healthy() else "unhealthy"
            utilization = container.get_resource_utilization()
            replica_util = utilization.get("replica_utilization", 0)
            print(f"   - {name}: {health}, replica utilization: {replica_util:.1f}%")

        # Example 2: Filter by health status
        print("\n2. Filter by health status (unhealthy):")
        unhealthy_containers = deployment.get_unhealthy_containers()
        print(f"   Unhealthy containers: {len(unhealthy_containers)}")
        for name, container in unhealthy_containers.items():
            print(f"   - {name}: {container.message}")

        # Example 3: Filter by resource thresholds
        print("\n3. Filter by replica utilization threshold (>50%):")
        high_util_containers = deployment.get_containers_by_resource_usage(
            replica_threshold=50.0
        )
        print(f"   High utilization containers: {len(high_util_containers)}")
        for name, container in high_util_containers.items():
            utilization = container.get_resource_utilization()
            replica_util = utilization.get("replica_utilization", 0)
            print(f"   - {name}: {replica_util:.1f}% replica utilization")

        # Example 4: Combined filtering
        print("\n4. Combined filtering (nginx* images AND healthy):")
        filters = ContainerFilterOptions(
            image_patterns=["nginx*"], health_status=["healthy"]
        )
        filtered_containers = deployment.find_containers(filters)
        print(f"   Healthy nginx containers: {len(filtered_containers)}")
        for name, container in filtered_containers.items():
            print(f"   - {name}: {container.image}")

    except Exception as e:
        print(f"Error demonstrating deployment filtering: {e}")


def main():
    """
    Main example function.
    """
    print("Container Filtering Phase 1 - Basic Filtering Demo")
    print("================================================")

    # Check for required environment variables
    if not os.getenv("CPLN_TOKEN"):
        print("\nError: CPLN_TOKEN environment variable is required.")
        print("Please set it to your Control Plane service account token.")
        return

    if not os.getenv("CPLN_ORG"):
        print("\nError: CPLN_ORG environment variable is required.")
        print("Please set it to your Control Plane organization name.")
        return

    # Initialize client from environment variables
    try:
        client = cpln.CPLNClient.from_env()
        print("\n✅ Connected to Control Plane API")
        print(f"   Organization: {os.getenv('CPLN_ORG')}")
        print(f"   Base URL: {os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}")
    except Exception as e:
        print(f"\nError initializing client: {e}")
        return

    # Get parameters from command line or use defaults
    gvc_name = sys.argv[1] if len(sys.argv) > 1 else "example-gvc"
    workload_name = sys.argv[2] if len(sys.argv) > 2 else "example-workload"
    location = sys.argv[3] if len(sys.argv) > 3 else "aws-us-east-1"

    if len(sys.argv) <= 1:
        print("\nUsing defaults:")
        print(f"  GVC: {gvc_name}")
        print(f"  Workload: {workload_name}")
        print(f"  Location: {location}")
        print(f"\nUsage: python {sys.argv[0]} <gvc-name> <workload-name> [location]")

    # Demonstrate workload-level container filtering
    demonstrate_workload_container_filtering(client, gvc_name, workload_name)

    # Demonstrate deployment-level container filtering
    demonstrate_deployment_container_filtering(
        client, gvc_name, workload_name, location
    )

    print("\n=== Phase 1 Summary ===")
    print("✅ ContainerFilterOptions dataclass implemented")
    print("✅ Workload.find_containers() method added")
    print("✅ Deployment.find_containers() method added")
    print("✅ Basic filtering by name, image, ports, environment")
    print("✅ Health status filtering for live deployments")
    print("✅ Resource threshold filtering for live deployments")
    print("✅ Container counting functionality")

    print("\n=== Next Steps ===")
    print("Phase 2: Advanced query builder with complex operations (AND, OR, NOT)")
    print("Phase 3: Cross-workload search functionality")
    print("Phase 4: Container statistics and analytics")


if __name__ == "__main__":
    main()
