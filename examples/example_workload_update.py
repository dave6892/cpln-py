#!/usr/bin/env python3
"""
Example: Workload Update Operations with Control Plane API

This example demonstrates how to update workloads using the new update() method.
The update method supports both individual parameter updates and full spec updates
with comprehensive validation and partial update capabilities.

Key features demonstrated:
- Container image updates
- Workload scaling (replica management)
- Resource limit updates (CPU/memory)
- Environment variable management
- Description and type updates
- Full spec and metadata updates
- Error handling and validation

Usage:
    python examples/example_workload_update.py [gvc-name] [workload-name]
"""

import os
import sys

# Add the src directory to the path to import cpln
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ruff: noqa: E402
import cpln
from cpln.config import WorkloadConfig


def demonstrate_image_update(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    Demonstrate container image updates.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
    """
    print(f"\n=== Image Update Demo: {workload_name} ===")

    try:
        # Get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        print(f"📦 Current workload: {workload.name}")

        # Get current containers to show before state
        containers = workload.get_containers()
        if containers:
            print("🔍 Current container images:")
            for container in containers:
                print(f"  - {container.name}: {container.image}")

        # Update container image
        new_image = "nginx:1.21-alpine"
        container_name = containers[0].name if containers else "app"

        print(
            f"\n🔄 Updating image for container '{container_name}' to '{new_image}'..."
        )

        workload.update(image=new_image, container_name=container_name)

        print("✅ Image update completed successfully!")

    except Exception as e:
        print(f"❌ Image update failed: {e}")


def demonstrate_scaling_update(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    Demonstrate workload scaling operations.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
    """
    print(f"\n=== Scaling Demo: {workload_name} ===")

    try:
        # Get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        # Scale to 3 replicas
        new_replica_count = 3

        print(
            f"📈 Scaling workload '{workload.name}' to {new_replica_count} replicas..."
        )

        workload.update(replicas=new_replica_count)

        print("✅ Scaling update completed successfully!")

    except Exception as e:
        print(f"❌ Scaling update failed: {e}")


def demonstrate_resource_update(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    Demonstrate resource limit updates.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
    """
    print(f"\n=== Resource Update Demo: {workload_name} ===")

    try:
        # Get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        # Update CPU and memory resources
        new_cpu = "500m"
        new_memory = "1Gi"

        print(f"💾 Updating resources for workload '{workload.name}':")
        print(f"  - CPU: {new_cpu}")
        print(f"  - Memory: {new_memory}")

        workload.update(cpu=new_cpu, memory=new_memory)

        print("✅ Resource update completed successfully!")

    except Exception as e:
        print(f"❌ Resource update failed: {e}")


def demonstrate_environment_variables_update(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    Demonstrate environment variable updates.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
    """
    print(f"\n=== Environment Variables Demo: {workload_name} ===")

    try:
        # Get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        # Update environment variables
        env_vars = {
            "NODE_ENV": "production",
            "DEBUG": "false",
            "API_VERSION": "v2",
            "CACHE_TTL": "3600",
        }

        print(f"🔧 Updating environment variables for workload '{workload.name}':")
        for key, value in env_vars.items():
            print(f"  - {key}={value}")

        workload.update(environment_variables=env_vars)

        print("✅ Environment variables update completed successfully!")

    except Exception as e:
        print(f"❌ Environment variables update failed: {e}")


def demonstrate_combined_update(
    client: cpln.CPLNClient, gvc_name: str, workload_name: str
):
    """
    Demonstrate combined parameter updates.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
    """
    print(f"\n=== Combined Update Demo: {workload_name} ===")

    try:
        # Get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        # Get first container name for image update
        containers = workload.get_containers()
        container_name = containers[0].name if containers else "app"

        print(f"🔄 Performing combined update on workload '{workload.name}':")
        print("  - Updating description")
        print("  - Updating container image")
        print("  - Scaling replicas")
        print("  - Updating resources")
        print("  - Adding environment variables")
        print("  - Changing workload type")

        workload.update(
            description="Updated workload with comprehensive changes",
            image="nginx:1.22-alpine",
            container_name=container_name,
            replicas=2,
            cpu="300m",
            memory="768Mi",
            environment_variables={"ENVIRONMENT": "staging", "LOG_LEVEL": "info"},
            workload_type="serverless",
        )

        print("✅ Combined update completed successfully!")

    except Exception as e:
        print(f"❌ Combined update failed: {e}")


def demonstrate_spec_update(client: cpln.CPLNClient, gvc_name: str, workload_name: str):
    """
    Demonstrate full spec update.

    Args:
        client: CPLN client instance
        gvc_name: Name of the GVC
        workload_name: Name of the workload
    """
    print(f"\n=== Spec Update Demo: {workload_name} ===")

    try:
        # Get the workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)

        # Define a new spec
        new_spec = {
            "type": "job",
            "containers": [
                {
                    "name": "worker",
                    "image": "busybox:latest",
                    "command": ["/bin/sh", "-c", "echo 'Job completed successfully'"],
                    "resources": {"cpu": "100m", "memory": "256Mi"},
                    "env": [
                        {"name": "WORKER_ID", "value": "worker-001"},
                        {"name": "JOB_TYPE", "value": "batch-processing"},
                    ],
                }
            ],
            "defaultOptions": {"suspend": False, "debug": False},
        }

        print(f"📋 Updating workload '{workload.name}' with full spec replacement...")
        print("  - Changing type to 'job'")
        print("  - Replacing container with batch worker")
        print("  - Setting up job-specific configuration")

        workload.update(spec=new_spec)

        print("✅ Spec update completed successfully!")

    except Exception as e:
        print(f"❌ Spec update failed: {e}")


def demonstrate_validation_errors():
    """
    Demonstrate validation error handling.
    """
    print("\n=== Validation Demo ===")

    try:
        # Create a mock workload for demonstration
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        workload = cpln.models.workloads.Workload(
            client=mock_client,
            attrs={"name": "test-workload", "spec": {"containers": []}},
            state={"gvc": "test-gvc"},
        )

        print("🧪 Testing validation scenarios...")

        # Test invalid CPU specification
        print("\n1. Testing invalid CPU specification:")
        try:
            workload.update(cpu="invalid_cpu")
        except ValueError as e:
            print(f"  ✅ Correctly caught error: {e}")

        # Test invalid memory specification
        print("\n2. Testing invalid memory specification:")
        try:
            workload.update(memory="invalid_memory")
        except ValueError as e:
            print(f"  ✅ Correctly caught error: {e}")

        # Test invalid workload type
        print("\n3. Testing invalid workload type:")
        try:
            workload.update(workload_type="invalid_type")
        except ValueError as e:
            print(f"  ✅ Correctly caught error: {e}")

        # Test negative replicas
        print("\n4. Testing negative replicas:")
        try:
            workload.update(replicas=-1)
        except ValueError as e:
            print(f"  ✅ Correctly caught error: {e}")

        # Test mutually exclusive options
        print("\n5. Testing mutually exclusive options:")
        try:
            workload.update(
                metadata={"spec": {"type": "serverless"}}, spec={"type": "standard"}
            )
        except ValueError as e:
            print(f"  ✅ Correctly caught error: {e}")

        print("\n✅ All validation tests completed successfully!")

    except Exception as e:
        print(f"❌ Validation demo failed: {e}")


def demonstrate_file_based_update():
    """
    Demonstrate file-based metadata update.
    """
    print("\n=== File-based Update Demo ===")

    try:
        # Create a temporary metadata file
        import json
        import tempfile

        metadata = {
            "name": "file-updated-workload",
            "description": "Workload updated from JSON file",
            "spec": {
                "type": "standard",
                "containers": [
                    {
                        "name": "web",
                        "image": "httpd:2.4-alpine",
                        "resources": {"cpu": "250m", "memory": "512Mi"},
                        "ports": [{"number": 80, "protocol": "http"}],
                    }
                ],
                "defaultOptions": {
                    "suspend": False,
                    "autoscaling": {
                        "metric": "cpu",
                        "target": 70,
                        "minScale": 1,
                        "maxScale": 3,
                    },
                },
            },
        }

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(metadata, f, indent=2)
            temp_file_path = f.name

        print(f"📄 Created temporary metadata file: {temp_file_path}")
        print("📋 Metadata content preview:")
        print(f"  - Name: {metadata['name']}")
        print(f"  - Type: {metadata['spec']['type']}")
        print(
            f"  - Container: {metadata['spec']['containers'][0]['name']} ({metadata['spec']['containers'][0]['image']})"
        )

        print("\n💡 To use with actual workload:")
        print(f"   workload.update(metadata_file_path='{temp_file_path}')")

        # Cleanup
        os.unlink(temp_file_path)
        print("🗑️  Cleaned up temporary file")

    except Exception as e:
        print(f"❌ File-based update demo failed: {e}")


def main():
    """
    Main demonstration function.
    """
    print("Control Plane Workload Update Examples")
    print("=====================================")

    # Check for required environment variables
    if not os.getenv("CPLN_TOKEN"):
        print("\n🔧 Environment Setup Instructions:")
        print("   export CPLN_TOKEN=your_service_account_token")
        print("   export CPLN_ORG=your_organization_name")
        print("\n💡 These examples demonstrate update functionality.")
        print("   Set environment variables to run against live workloads.")

        # Run validation and file demos which don't require live connection
        demonstrate_validation_errors()
        demonstrate_file_based_update()
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

    if len(sys.argv) <= 1:
        print("\nUsing defaults:")
        print(f"  GVC: {gvc_name}")
        print(f"  Workload: {workload_name}")
        print(f"\nUsage: python {sys.argv[0]} <gvc-name> <workload-name>")

    print(f"\n🎯 Target workload: {workload_name} in GVC {gvc_name}")

    # Check if workload exists
    try:
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)
        print(f"✅ Found workload: {workload.name}")
    except Exception as e:
        print(
            f"❌ Could not access workload '{workload_name}' in GVC '{gvc_name}': {e}"
        )
        print("Please check that the GVC and workload exist and you have access.")

        # Still run validation and file demos
        demonstrate_validation_errors()
        demonstrate_file_based_update()
        return

    # Run demonstrations
    print("\n" + "=" * 50)
    print("🚀 Starting Update Demonstrations")
    print("=" * 50)

    # 1. Image update demo
    demonstrate_image_update(client, gvc_name, workload_name)

    # 2. Scaling demo
    demonstrate_scaling_update(client, gvc_name, workload_name)

    # 3. Resource update demo
    demonstrate_resource_update(client, gvc_name, workload_name)

    # 4. Environment variables demo
    demonstrate_environment_variables_update(client, gvc_name, workload_name)

    # 5. Combined update demo
    demonstrate_combined_update(client, gvc_name, workload_name)

    # 6. Spec update demo
    demonstrate_spec_update(client, gvc_name, workload_name)

    # 7. Validation demos (always run)
    demonstrate_validation_errors()

    # 8. File-based update demo
    demonstrate_file_based_update()

    # Summary
    print("\n" + "=" * 50)
    print("📋 Update Method Summary")
    print("=" * 50)
    print("✅ Individual parameter updates:")
    print("   - workload.update(image='nginx:1.21', container_name='web')")
    print("   - workload.update(replicas=5)")
    print("   - workload.update(cpu='500m', memory='1Gi')")
    print("   - workload.update(environment_variables={'ENV': 'prod'})")
    print("   - workload.update(description='Updated description')")
    print("   - workload.update(workload_type='serverless')")

    print("\n✅ Full updates:")
    print("   - workload.update(spec={...})  # Spec-only update")
    print("   - workload.update(metadata={...})  # Full metadata update")
    print("   - workload.update(metadata_file_path='workload.json')")

    print("\n✅ Combined updates:")
    print("   - workload.update(image='nginx:1.21', replicas=3, cpu='300m')")

    print("\n🛡️  Built-in validation:")
    print("   - CPU/memory resource specifications")
    print("   - Workload type validation")
    print("   - Replica count validation")
    print("   - Container name requirements")
    print("   - Mutually exclusive parameter checks")

    print("\n⚡ Key features:")
    print("   - Partial updates (merges with existing config)")
    print("   - Immediate return (doesn't wait for deployment)")
    print("   - Comprehensive error handling")
    print("   - Auto-detection for single-container workloads")
    print("   - Same interface as workload.create() method")

    print("\n🎉 All demonstrations completed!")


if __name__ == "__main__":
    main()
