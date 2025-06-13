#!/usr/bin/env python3
"""
Example script demonstrating how to work with Images using the CPLN Python client.
"""

import sys
from typing import List

import cpln
from cpln.exceptions import CPLNError
from cpln.models.gvcs import GVC
from cpln.models.images import Image
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


def get_gvc(client: cpln.CPLNClient, gvc_name: str) -> GVC:
    """
    Get a specific GVC by name.

    Args:
        client: Authenticated CPLN client
        gvc_name: Name of the GVC to get

    Returns:
        GVC: The GVC object

    Raises:
        cpln.exceptions.CPLNError: If GVC retrieval fails
    """
    try:
        return client.gvcs.get(gvc_name)
    except CPLNError as e:
        print(f"Failed to get GVC: {e}", file=sys.stderr)
        raise


def list_images(client: cpln.CPLNClient) -> List[Image]:
    """
    List all images.

    Args:
        client: Authenticated CPLN client

    Returns:
        List[Image]: List of image objects

    Raises:
        cpln.exceptions.CPLNError: If image listing fails
    """
    try:
        return client.images.list()
    except CPLNError as e:
        print(f"Failed to list images: {e}", file=sys.stderr)
        raise


def get_image_details(client: cpln.CPLNClient, image_name: str) -> Image:
    """
    Get detailed information about a specific image.

    Args:
        client: Authenticated CPLN client
        image_name: Name of the image to get details for

    Returns:
        Image: The image object with detailed information

    Raises:
        cpln.exceptions.CPLNError: If image retrieval fails
    """
    try:
        return client.images.get(image_name)
    except CPLNError as e:
        print(f"Failed to get image details: {e}", file=sys.stderr)
        raise


def filter_images_by_repository(images: List[Image], repository: str) -> List[Image]:
    """
    Filter images by repository name.

    Args:
        images: List of images to filter
        repository: Repository name to filter by

    Returns:
        List[Image]: Filtered list of images
    """
    return [img for img in images if img.repository == repository]


def main() -> None:
    """Main function to demonstrate image operations."""
    try:
        # Initialize client
        client = get_cpln_client()
        print("CPLN Client initialized successfully")

        # Get GVC first
        gvc_name = "david"  # You might want to make this configurable
        gvc = get_gvc(client, gvc_name)
        print(f"\nUsing GVC: {gvc.name}")

        # List all images
        images = list_images(client)
        print(f"\nFound {len(images)} images in the organization:")

        for image in images:
            print(f"\nImage: {image.name}")
            print(f"Repository: {image.repository}")
            print(f"Tag: {image.tag}")

            # Get detailed information for each image
            details = get_image_details(client, image.name)

            print(f"Digest: {safe_get_attr(details, 'digest')}")
            print(f"Created: {safe_get_attr(details, 'created')}")
            print(f"Last Modified: {safe_get_attr(details, 'last_modified')}")
            # print(f"Size: {details.size_bytes} bytes")

            # Print additional metadata if available
            if hasattr(details, "metadata"):
                print("Metadata:")
                for key, value in details.metadata.items():
                    print(f"  {key}: {value}")

    except CPLNError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
