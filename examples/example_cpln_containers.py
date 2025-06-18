#!/usr/bin/env python3
"""
Example: Workload Container Operations with Control Plane API

This example demonstrates how to inspect workload containers and deployments
using the new parser-based architecture with deployment objects.

Key features:
- Workload container specifications
- Live deployment status and containers
- Replica management
- Container execution commands

Usage:
    python examples/example_cpln_containers.py [gvc-name] [workload-name]
"""

import os
import sys

# Add the src directory to the path to import cpln
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ruff: noqa: E402
import cpln
from cpln.config import WorkloadConfig


def list_workload_containers(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    List container specifications for a specific workload.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the specific workload

    Returns:
        List of container specifications for the workload
    """
    print(f"\n=== Listing container specs for workload: {workload_name} ===")

    try:
        # Create config and get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        # Get container specifications from the workload spec
        containers = workload.get_containers()

        if containers:
            print(
                f"\n📦 Workload: {workload.attrs['name']} ({len(containers)} container specs)"
            )

            for container in containers:
                print(f"  ├─ Container: {container.name}")
                print(f"  │  Image: {container.image}")
                print(f"  │  CPU: {container.cpu}")
                print(f"  │  Memory: {container.memory}")

                # Show ports if any
                if container.ports:
                    print(f"  │  Ports: {len(container.ports)}")
                    for port in container.ports:
                        print(f"  │    {port.number}/{port.protocol}")

                print(f"  │  Inherit Env: {container.inherit_env}")
                print("  │")

            print(
                f"\n📊 Total container specs in workload {workload_name}: {len(containers)}"
            )
        else:
            print(f"No container specs found in workload {workload_name}.")

        return containers

    except Exception as e:
        print(f"Error listing containers for workload {workload_name}: {e}")
        return []


def demonstrate_container_execution(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str, location: str
):
    """
    Demonstrate container execution capabilities.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
        location: Location to execute in
    """
    print(f"\n=== Container Execution Demo: {workload_name} ===")

    try:
        # Create config and get the workload
        config = WorkloadConfig(
            gvc=gvc_name, workload_id=workload_name, location=location
        )
        workload = client.workloads.get(config)

        # Try to ping the workload
        print("\n🏓 Pinging workload...")
        ping_result = workload.ping(location=location)

        print(f"   Status: {ping_result['status']}")
        print(f"   Message: {ping_result['message']}")
        print(f"   Exit Code: {ping_result['exit_code']}")

        # Get available containers
        containers = workload.get_containers()
        if containers:
            container_name = containers[0].name
            print(f"\n💻 Executing command in container: {container_name}")

            try:
                # Execute a simple command
                result = workload.exec(
                    "echo 'Hello from container!'",
                    location=location,
                    container=container_name,
                )
                print(f"   Command executed successfully: {result}")

            except Exception as e:
                print(f"   Execution failed: {e}")

    except Exception as e:
        print(f"Error during execution demo: {e}")


def list_containers_across_workloads(client: cpln.CPLNClient, gvc_name: str):
    """
    List containers across all workloads in a GVC.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC

    Returns:
        Total count of containers found
    """
    print("\n=== Container Summary Across All Workloads ===")

    try:
        # Get all workloads in the GVC first
        workloads = client.workloads.list(gvc=gvc_name)

        if not workloads:
            print("No workloads found in this GVC.")
            return 0

        print(f"Found {len(workloads)} workload(s) in GVC '{gvc_name}':")

        total_containers = 0
        for workload in workloads:
            try:
                # Get containers for each workload
                containers = workload.get_containers()
                container_count = len(containers) if containers else 0
                total_containers += container_count

                print(f"  ├─ {workload.attrs['name']}: {container_count} containers")

                if containers:
                    for container in containers:
                        print(f"     └─ {container.name} ({container.image})")

            except Exception as e:
                print(f"  ├─ {workload.attrs['name']}: Error getting containers - {e}")

        print(f"\n📊 Total containers across all workloads: {total_containers}")
        return total_containers

    except Exception as e:
        print(f"Error listing workloads: {e}")
        return 0


def main():
    """
    Main example function.
    """
    print("Control Plane Container Operations Example (Workload-Centric)")
    print("=============================================================")

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
    workload_name = "example-workload"

    # Check if the user provided a GVC name as command line argument
    if len(sys.argv) > 1:
        gvc_name = sys.argv[1]
    if len(sys.argv) > 2:
        workload_name = sys.argv[2]
    else:
        print(f"\nUsing default GVC name: {gvc_name}")
        print(f"Using default workload name: {workload_name}")
        print(f"Usage: python {sys.argv[0]} <gvc-name> <workload-name>")

    # Example 1: List containers for a specific workload (preferred workload-centric approach)
    print("\n1. Workload-centric container access (recommended):")
    containers = list_workload_containers(client, gvc_name, workload_name)

    if not containers:
        print(f"\n❌ Could not access workload '{workload_name}' in GVC '{gvc_name}'")
        print("Please check that the GVC and workload exist and you have access.")
        return

    # Example 2: Overview of all containers in the GVC
    print(f"\n2. Overview of all containers in GVC '{gvc_name}':")
    try:
        workloads = client.workloads.list(gvc=gvc_name)
        total_containers = 0

        for workload in workloads:
            try:
                workload_containers = workload.get_containers()
                container_count = len(workload_containers) if workload_containers else 0
                total_containers += container_count
                print(f"  ├─ {workload.attrs['name']}: {container_count} containers")
            except Exception as e:
                print(f"  ├─ {workload.attrs['name']}: Error getting containers - {e}")

        print(f"\n📊 Total containers across all workloads: {total_containers}")
    except Exception as e:
        print(f"Error listing workloads: {e}")

    print("\n=== Workload-Centric Design Principles ===")
    print("✅ Always access containers through their parent workload")
    print("✅ Use workload.get_container_objects() for workload-specific containers")
    print("✅ Use ContainerCollection.list(gvc, workload_name) for specific workloads")
    print("✅ Iterate through workloads individually for multi-workload access")
    print("❌ Avoid cross-workload container listing without workload context")

    print("\n=== Container API Limitations ===")
    print("Note: Container operations are read-only in the Control Plane API.")
    print("Containers are managed through workload deployments, not directly.")
    print("Available operations:")
    print("  ✅ List containers (workload-centric)")
    print("  ✅ View container status and health")
    print("  ✅ Inspect container configuration")
    print("  ❌ Start/stop containers")
    print("  ❌ Execute commands in containers (use workload.exec() instead)")
    print("  ❌ Access container logs directly")


if __name__ == "__main__":
    main()
