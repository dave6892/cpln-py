#!/usr/bin/env python3
"""
Example script demonstrating how to list and inspect workloads using the CPLN Python client.
"""

import sys
from typing import List

import cpln
from cpln.exceptions import CPLNError
from cpln.models.workloads import Workload


def get_cpln_client() -> cpln.CPLNClient:
    """
    Initialize and return a CPLN client using environment variables.

    Returns:
        cpln.CPLNClient: An authenticated CPLN client instance

    Raises:
        cpln.exceptions.CPLNError: If client initialization fails
    """
    try:
        # First create client from environment variables
        client = cpln.CPLNClient.from_env()

        # Then create a new client with explicit configuration
        client = cpln.CPLNClient(
            token=client.api.config.token,
            org=client.api.config.org,
        )
        return client
    except CPLNError as e:
        print(f"Failed to initialize CPLN client: {e}", file=sys.stderr)
        raise


def list_workloads(client: cpln.CPLNClient, gvc: str) -> List[Workload]:
    """
    List all workloads in a specified GVC.

    Args:
        client: Authenticated CPLN client
        gvc: GVC name to list workloads from

    Returns:
        List[Workload]: List of workload objects

    Raises:
        cpln.exceptions.CPLNError: If workload listing fails
    """
    try:
        return client.workloads.list(gvc=gvc)
    except CPLNError as e:
        print(f"Failed to list workloads: {e}", file=sys.stderr)
        raise


def main() -> None:
    """Main function to demonstrate workload operations."""
    try:
        # Initialize client
        client = get_cpln_client()
        print("CPLN Client initialized successfully")

        # List workloads
        gvc_name = "david"  # You might want to make this configurable
        workloads = list_workloads(client, gvc_name)

        # Print workload information
        print(f"\nFound {len(workloads)} workloads in GVC '{gvc_name}':")
        for workload in workloads:
            print(f"\nWorkload: {workload.name}")
            print(f"Status: {workload.get_spec_state()}")

    except CPLNError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
