from .config import APIConfig
from .gvc import GVCApiMixin
from .image import ImageApiMixin
from .workload import (
    WorkloadApiMixin,
    WorkloadDeploymentMixin,
)
import requests


class APIClient(
    requests.Session,
    GVCApiMixin,
    ImageApiMixin,
    WorkloadApiMixin,
    WorkloadDeploymentMixin, #TODO: Test if I can remove this
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
    def __init__(self,
        config: APIConfig | None = None,
        **kwargs
    ):
        super().__init__()
        if config is None:
            config = APIConfig(**kwargs)

        self.config = config

    def _get(self,
        endpoint: str
    ):
        """
        Makes a GET request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to request

        Returns:
            dict: The JSON response from the API
        """
        resp = self.get(
            f"{self.config.org_url}/{endpoint}",
            headers = self._headers
        )
        return resp.json()

    def _delete(self,
        endpoint: str
    ):
        """
        Makes a DELETE request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to delete

        Returns:
            requests.Response: The response object from the API
        """
        return self.delete(
            f"{self.config.org_url}/{endpoint}",
            headers = self._headers
        )

    def _post(self,
        endpoint: str,
        data: dict[str, any] | None = None
    ):
        """
        Makes a PATCH request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to update
            data (dict, optional): The data to send in the request body

        Returns:
            requests.Response: The response object from the API
        """
        return self.post(
            f"{self.config.org_url}/{endpoint}",
            json = data,
            headers = self._headers,
        )

    def _patch(self,
        endpoint: str,
        data: dict[str, any] | None = None
    ):
        """
        Makes a PATCH request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to update
            data (dict, optional): The data to send in the request body

        Returns:
            requests.Response: The response object from the API
        """
        return self.patch(
            f"{self.config.org_url}/{endpoint}",
            json = data,
            headers = self._headers,
        )

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.config.token}"
        }
