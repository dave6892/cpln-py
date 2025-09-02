#!/usr/bin/env python3
"""
Simplest possible test for the workload update() method.

Usage:
    python simple_test.py [gvc-name] [workload-name]

Environment variables needed:
    CPLN_TOKEN=your_service_account_token
    CPLN_ORG=your_organization_name
"""

import os
import sys

# Add the src directory to the path to import cpln
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import cpln  # noqa: E402
from cpln.config import WorkloadConfig  # noqa: E402


def main():
    # Check environment
    if not os.getenv("CPLN_TOKEN"):
        print("❌ CPLN_TOKEN environment variable required")
        print("   export CPLN_TOKEN=your_service_account_token")
        return

    if not os.getenv("CPLN_ORG"):
        print("❌ CPLN_ORG environment variable required")
        print("   export CPLN_ORG=your_organization_name")
        return

    # Get workload details
    gvc_name = sys.argv[1] if len(sys.argv) > 1 else input("Enter GVC name: ")
    workload_name = sys.argv[2] if len(sys.argv) > 2 else input("Enter workload name: ")

    try:
        # Initialize client
        client = cpln.CPLNClient.from_env()
        print(f"✅ Connected to Control Plane (org: {os.getenv('CPLN_ORG')})")

        # Get workload
        config = WorkloadConfig(gvc=gvc_name, workload_id=workload_name)
        workload = client.workloads.get(config)
        print(f"✅ Found workload: {workload.name}")

        # Simple test: update description
        print("\n🧪 Testing update() method...")
        workload.update(description="Updated by simple test script")
        print("✅ Successfully updated workload description!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
