#!/usr/bin/env python3
"""
Example script demonstrating how to work with GVCs (Global Virtual Clusters) using the CPLN Python client.
"""

import sys

import cpln
from cpln.errors import CPLNError
from cpln.models.gvcs import GVC
from utils import safe_get_attr


def get_cpln_client() -> cpln.CPLNClient:
    """
    Initialize and return a CPLN client using environment variables.

    Returns:
        cpln.CPLNClient: An authenticated CPLN client instance

    Raises:
        cpln.exceptions.CPLNError: If client initialization fails
    """
    try:
        client = cpln.CPLNClient.from_env()
        client = cpln.CPLNClient(
            token=client.api.config.token,
            org=client.api.config.org,
        )
        return client
    except CPLNError as e:
        print(f"Failed to initialize CPLN client: {e}", file=sys.stderr)
        raise


def list_gvcs(client: cpln.CPLNClient) -> list[GVC]:
    """
    List all GVCs in the organization.

    Args:
        client: Authenticated CPLN client

    Returns:
        List[GVC]: List of GVC objects

    Raises:
        cpln.exceptions.CPLNError: If GVC listing fails
    """
    try:
        return client.gvcs.list()
    except CPLNError as e:
        print(f"Failed to list GVCs: {e}", file=sys.stderr)
        raise


def get_gvc_details(client: cpln.CPLNClient, gvc_name: str) -> GVC:
    """
    Get detailed information about a specific GVC.

    Args:
        client: Authenticated CPLN client
        gvc_name: Name of the GVC to get details for

    Returns:
        GVC: The GVC object with detailed information

    Raises:
        cpln.exceptions.CPLNError: If GVC retrieval fails
    """
    try:
        return client.gvcs.get(gvc_name)
    except CPLNError as e:
        print(f"Failed to get GVC details: {e}", file=sys.stderr)
        raise


def main() -> None:
    """Main function to demonstrate GVC operations."""
    try:
        # Initialize client
        client = get_cpln_client()
        print("CPLN Client initialized successfully")

        # List all GVCs
        gvcs = list_gvcs(client)
        print(f"\nFound {len(gvcs)} GVCs in the organization:")

        for gvc in gvcs:
            print(f"\nGVC: {gvc.name}")

            # Get detailed information for each GVC
            details = get_gvc_details(client, gvc.name)

            # Print basic information that should always be available
            print(f"Name: {safe_get_attr(details, 'name')}")
            print(f"Description: {safe_get_attr(details, 'description')}")

            # Print optional information if available
            if hasattr(details, "status"):
                print(f"Status: {details.status}")

            # Print spec information if available
            if hasattr(details, "spec"):
                spec = details.spec
                print(f"Spec: {spec}")

    except CPLNError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
