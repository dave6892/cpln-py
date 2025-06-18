#!/usr/bin/env python3
"""
Example: Modern Workload Container Operations with Control Plane API

This example demonstrates how to inspect workload containers and deployments
using the new parser-based architecture with deployment objects.

Key features:
- Workload container specifications
- Live deployment status and containers
- Replica management
- Container execution commands

Usage:
    python examples/example_modern_workload_containers.py [gvc-name] [workload-name]
"""

import os
import sys

# Add the src directory to the path to import cpln
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ruff: noqa: E402
import cpln
from cpln.config import WorkloadConfig


def inspect_workload_containers(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    Inspect container specifications for a specific workload.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the specific workload
    """
    print(f"\n=== Workload Container Specifications: {workload_name} ===")

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

            print(f"\n📊 Total container specs: {len(containers)}")
        else:
            print(f"No container specs found in workload {workload_name}.")

        return workload, containers

    except Exception as e:
        print(f"Error inspecting workload {workload_name}: {e}")
        return None, []


def inspect_deployment_status(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str, location: str
):
    """
    Inspect live deployment status and containers.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
        location: Location to inspect
    """
    print(f"\n=== Live Deployment Status: {workload_name} @ {location} ===")

    try:
        # Create config and get the workload
        config = WorkloadConfig(
            gvc=gvc_name, workload_id=workload_name, location=location
        )
        workload = client.workloads.get(config)

        # Get deployment information
        deployment = workload.get_deployment(location=location)

        print(f"\n🚀 Deployment: {deployment.name}")
        print(f"   Kind: {deployment.kind}")
        print(f"   Last Modified: {deployment.last_modified}")

        # Get deployment status
        status = deployment.status
        print(f"   Ready: {'✅' if status.ready else '❌'} {status.ready}")
        print(f"   Message: {status.message}")

        if hasattr(status, "endpoint") and status.endpoint:
            print(f"   Endpoint: {status.endpoint}")

        if hasattr(status, "remote") and status.remote:
            print(f"   Remote: {status.remote}")

        # Get live container information
        containers = deployment.get_containers()
        if containers:
            print(f"\n📦 Live Containers ({len(containers)}):")
            for name, container in containers.items():
                print(f"  ├─ {name}")
                print(f"  │  Image: {container.image}")
                print(
                    f"  │  Ready: {'✅' if container.ready else '❌'} {container.ready}"
                )
                print(
                    f"  │  Healthy: {'✅' if container.is_healthy() else '❌'} {container.is_healthy()}"
                )

                # Show resource utilization
                utilization = container.get_resource_utilization()
                if utilization["replica_utilization"] is not None:
                    print(
                        f"  │  Replica Utilization: {utilization['replica_utilization']:.1f}%"
                    )
                    print(
                        f"  │  Replicas: {container.resources.replicas_ready}/{container.resources.replicas}"
                    )

                if hasattr(container, "message"):
                    print(f"  │  Message: {container.message}")
                print("  │")

        # Get replicas
        replicas = deployment.get_replicas()
        if replicas:
            print("\n🔄 Replicas:")
            for container_name, replica_list in replicas.items():
                print(f"  Container: {container_name} ({len(replica_list)} replicas)")
                for replica in replica_list:
                    print(f"    ├─ {replica.name}")

        return deployment

    except Exception as e:
        print(f"Error inspecting deployment: {e}")
        return None


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


def main():
    """
    Main example function.
    """
    print("Modern Control Plane Container Operations Example")
    print("==============================================")

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

    # 1. Inspect workload container specifications
    workload, containers = inspect_workload_containers(client, gvc_name, workload_name)

    if not workload:
        print(f"\n❌ Could not access workload '{workload_name}' in GVC '{gvc_name}'")
        print("Please check that the GVC and workload exist and you have access.")
        return

    # 2. Inspect live deployment status
    deployment = inspect_deployment_status(client, gvc_name, workload_name, location)

    # 3. Demonstrate container execution (if deployment is available)
    if deployment:
        demonstrate_container_execution(client, gvc_name, workload_name, location)

    # 4. Summary
    print("\n=== Summary ===")
    print(f"✅ Workload specifications: {len(containers)} containers")
    print(f"✅ Deployment status: {'Available' if deployment else 'Not available'}")
    print("✅ Modern parser-based API successfully demonstrated")

    print("\n=== Key API Changes ===")
    print("✅ workload.get_containers() - Get container specifications")
    print("✅ workload.get_deployment(location) - Get live deployment")
    print("✅ deployment.get_containers() - Get live container status")
    print("✅ deployment.get_replicas() - Get replica information")
    print("✅ workload.exec() - Execute commands in containers")
    print("✅ workload.ping() - Ping containers")


if __name__ == "__main__":
    main()
