#!/usr/bin/env python3
"""
Example: Container Operations with Control Plane API

This example demonstrates how to list and inspect containers
across workloads in a Control Plane GVC.

Note: Container operations are read-only since the Control Plane API
does not expose direct container management endpoints.
"""

import os
import sys
from typing import List

# Add the src directory to the path to import cpln
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ruff: noqa: E402
import cpln
from cpln.models.containers import Container


def list_containers_basic(client: cpln.CPLNClient, gvc_name: str) -> List[Container]:
    """
    Basic container listing example.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC to list containers from

    Returns:
        List of Container instances
    """
    print(f"\n=== Listing containers in GVC: {gvc_name} ===")

    try:
        containers = client.containers.list(gvc=gvc_name)

        if not containers:
            print("No containers found in this GVC.")
            return []

        print(f"Found {len(containers)} container(s):")

        for container in containers:
            print(f"\nContainer: {container.name}")
            print(f"  Image: {container.image}")
            print(f"  Workload: {container.workload_name}")
            print(f"  Location: {container.location}")
            print(f"  Status: {container.status or 'Unknown'}")
            print(f"  Health: {container.health_status or 'Unknown'}")

            # Show environment variables if any
            if container.environment_variables:
                print(
                    f"  Environment variables: {len(container.environment_variables)}"
                )
                for name, value in list(container.environment_variables.items())[:3]:
                    print(f"    {name}={value}")
                if len(container.environment_variables) > 3:
                    print(
                        f"    ... and {len(container.environment_variables) - 3} more"
                    )

            # Show resource limits if any
            if container.resource_limits:
                print("  Resource limits:")
                if container.resource_limits.get("cpu"):
                    print(f"    CPU: {container.resource_limits['cpu']}")
                if container.resource_limits.get("memory"):
                    print(f"    Memory: {container.resource_limits['memory']}")

            # Show health status
            health_emoji = "✅" if container.is_healthy() else "❌"
            print(f"  Healthy: {health_emoji} {container.is_healthy()}")

        return containers

    except cpln.errors.APIError as e:
        print(f"Error listing containers: {e}")
        return []


def list_containers_filtered(
    client: cpln.CPLNClient, gvc_name: str, location: str
) -> List[Container]:
    """
    Container listing with location filter.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        location: Location to filter by

    Returns:
        List of Container instances
    """
    print(f"\n=== Listing containers in GVC: {gvc_name}, Location: {location} ===")

    try:
        containers = client.containers.list(gvc=gvc_name, location=location)

        if not containers:
            print(f"No containers found in location '{location}'.")
            return []

        print(f"Found {len(containers)} container(s) in {location}:")

        for container in containers:
            print(f"\n  📦 {container.name} ({container.image})")
            print(f"     Workload: {container.workload_name}")

            # Show replica information if available
            if (
                container.ready_replicas is not None
                and container.total_replicas is not None
            ):
                print(
                    f"     Replicas: {container.ready_replicas}/{container.total_replicas}"
                )

            # Show resource utilization if available
            utilization = container.get_resource_utilization()
            if any(utilization.values()):
                print("     Resource usage:")
                if utilization["cpu"]:
                    print(f"       CPU: {utilization['cpu']:.1f}%")
                if utilization["memory"]:
                    print(f"       Memory: {utilization['memory']:.1f}%")

        return containers

    except cpln.errors.APIError as e:
        print(f"Error listing containers: {e}")
        return []


def list_containers_by_workload(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
) -> List[Container]:
    """
    List containers for a specific workload.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload

    Returns:
        List of Container instances
    """
    print(f"\n=== Listing containers for workload: {workload_name} ===")

    try:
        containers = client.containers.list(gvc=gvc_name, workload_name=workload_name)

        if not containers:
            print(f"No containers found for workload '{workload_name}'.")
            return []

        print(f"Found {len(containers)} container(s) in workload {workload_name}:")

        for container in containers:
            print(f"\n  Container: {container.name}")
            print(f"    Image: {container.image}")
            print(f"    Location: {container.location}")
            print(f"    Deployment: {container.deployment_name or 'Unknown'}")

            # Convert to dict for detailed view
            container_dict = container.to_dict()

            # Show timestamps if available
            if container_dict.get("created_at"):
                print(f"    Created: {container_dict['created_at']}")
            if container_dict.get("updated_at"):
                print(f"    Updated: {container_dict['updated_at']}")

        return containers

    except cpln.errors.APIError as e:
        print(f"Error listing containers for workload: {e}")
        return []


def show_container_health_summary(containers: List[Container]) -> None:
    """
    Show a health summary of containers.

    Args:
        containers: List of Container instances
    """
    if not containers:
        return

    print("\n=== Container Health Summary ===")

    healthy_count = sum(1 for c in containers if c.is_healthy())
    unhealthy_count = len(containers) - healthy_count

    print(f"Total containers: {len(containers)}")
    print(f"Healthy: ✅ {healthy_count}")
    print(f"Unhealthy: ❌ {unhealthy_count}")

    if unhealthy_count > 0:
        print("\nUnhealthy containers:")
        for container in containers:
            if not container.is_healthy():
                status = container.health_status or "Unknown"
                print(f"  - {container.workload_name}/{container.name} ({status})")


def main():
    """
    Main example function.
    """
    print("Control Plane Container Operations Example")
    print("==========================================")

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
        print("\nConnected to Control Plane API")
        print(f"Organization: {os.getenv('CPLN_ORG')}")
        print(f"Base URL: {os.getenv('CPLN_BASE_URL', 'https://api.cpln.io')}")
    except Exception as e:
        print(f"\nError initializing client: {e}")
        return

    # Example GVC name - you may need to change this
    gvc_name = "example-gvc"

    # Check if the user provided a GVC name as command line argument
    if len(sys.argv) > 1:
        gvc_name = sys.argv[1]
    else:
        print(f"\nUsing default GVC name: {gvc_name}")
        print(f"You can specify a different GVC: python {sys.argv[0]} <gvc-name>")

    # Example 1: List all containers in the GVC
    all_containers = list_containers_basic(client, gvc_name)

    # Example 2: List containers with location filter (if any containers were found)
    if all_containers:
        # Use the location from the first container
        sample_location = all_containers[0].location
        list_containers_filtered(client, gvc_name, sample_location)

        # Example 3: List containers for a specific workload
        sample_workload = all_containers[0].workload_name
        list_containers_by_workload(client, gvc_name, sample_workload)

        # Example 4: Show health summary
        show_container_health_summary(all_containers)

    print("\n=== Container API Limitations ===")
    print("Note: Container operations are read-only in the Control Plane API.")
    print("Containers are managed through workload deployments, not directly.")
    print("Available operations:")
    print("  ✅ List containers")
    print("  ✅ View container status and health")
    print("  ✅ Inspect container configuration")
    print("  ❌ Start/stop containers")
    print("  ❌ Execute commands in containers (use workload.exec() instead)")
    print("  ❌ Access container logs directly")


if __name__ == "__main__":
    main()
