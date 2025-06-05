from typing import Any, Dict, Optional

import requests

from ..errors import APIError, NotFound
from .config import APIConfig
from .gvc import GVCApiMixin
from .image import ImageApiMixin
from .workload import (
    WorkloadApiMixin,
    WorkloadDeploymentMixin,
)


class APIClient(
    requests.Session,
    GVCApiMixin,
    ImageApiMixin,
    WorkloadApiMixin,
    WorkloadDeploymentMixin,
):
    """
    A low-level client for the Control Plane API.

    Example:

        >>> import cpln
        >>> client = cpln.APIClient(
            base_url='https://api.cpln.io/'
        )
        >>> client.version()

    Args:
        base_url (str): URL to the Control Plane server.
        version (str): The version of the API to use. Set to ``auto`` to
            automatically detect the server's version. Default: ``1.0.0``
        timeout (int): Default timeout for API calls, in seconds.
    """

    def __init__(self, config: Optional[APIConfig] = None, **kwargs):
        super().__init__()

        # Initialize the config object
        if config is None:
            config = APIConfig(**kwargs)

        self.config = config

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Makes a GET request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to request

        Returns:
            dict: The JSON response from the API

        Raises:
            NotFound: If the resource is not found
            APIError: If the API returns an error
        """
        resp = self.get(f"{self.config.org_url}/{endpoint}", headers=self._headers)

        # Handle error responses
        if resp.status_code == 404:
            raise NotFound(f"Resource not found: {endpoint}")
        elif resp.status_code >= 400:
            raise APIError(f"API error ({resp.status_code}): {resp.text}")

        return resp.json()

    def _delete(self, endpoint: str) -> requests.Response:
        """
        Makes a DELETE request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to delete

        Returns:
            requests.Response: The response object from the API

        Raises:
            NotFound: If the resource is not found
            APIError: If the API returns an error
        """
        resp = self.delete(f"{self.config.org_url}/{endpoint}", headers=self._headers)

        # Handle error responses
        if resp.status_code == 404:
            raise NotFound(f"Resource not found: {endpoint}")
        elif resp.status_code >= 400:
            raise APIError(f"API error ({resp.status_code}): {resp.text}")

        return resp

    def _post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Makes a POST request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to post to
            data (dict, optional): The data to send in the request body

        Returns:
            requests.Response: The response object from the API

        Raises:
            APIError: If the API returns an error
        """
        resp = self.post(
            f"{self.config.org_url}/{endpoint}",
            json=data,
            headers=self._headers,
        )

        # Handle error responses
        if resp.status_code >= 400:
            error_msg = f"API error ({resp.status_code})"
            try:
                error_data = resp.json()
                if isinstance(error_data, dict) and "error" in error_data:
                    error_msg = f"{error_msg}: {error_data['error']}"
                else:
                    error_msg = f"{error_msg}: {resp.text}"
            except (ValueError, KeyError):
                error_msg = f"{error_msg}: {resp.text}"

            raise APIError(error_msg)

        return resp

    def _patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Makes a PATCH request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to update
            data (dict, optional): The data to send in the request body

        Returns:
            requests.Response: The response object from the API

        Raises:
            NotFound: If the resource is not found
            APIError: If the API returns an error
        """
        resp = self.patch(
            f"{self.config.org_url}/{endpoint}",
            json=data,
            headers=self._headers,
        )

        # Handle error responses
        if resp.status_code == 404:
            raise NotFound(f"Resource not found: {endpoint}")
        elif resp.status_code >= 400:
            raise APIError(f"API error ({resp.status_code}): {resp.text}")

        return resp

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self.config.token}"}
