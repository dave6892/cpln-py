class GVCApiMixin:
    """
    A mixin class that provides GVC (Global Virtual Cluster) related API methods.
    """

    def get_gvc(self, name: str = None):
        """
        Retrieves GVC information from the Control Plane API.

        Args:
            name (str, optional): The name of the specific GVC to retrieve.
                If not provided, returns a list of all GVCs.

        Returns:
            dict: The GVC information or list of GVCs

        Raises:
            APIError: If the request fails
        """
        endpoint = "gvc"
        if name:
            endpoint += f"/{name}"
        return self._get(endpoint)

    def create_gvc(self, name: str, description: str = None):
        """
        Creates a new GVC in the Control Plane.

        Args:
            name (str): The name of the GVC to create
            description (str, optional): A description of the GVC

        Raises:
            ValueError: Currently not implemented
        """
        raise ValueError(
            "Not implemented! The payload to do this is annoyingly long, so somebody else do it."
        )

    def delete_gvc(self, name: str):
        """
        Deletes a GVC from the Control Plane.

        Args:
            name (str): The name of the GVC to delete

        Returns:
            requests.Response: The response from the API

        Raises:
            APIError: If the request fails
        """
        return self._delete(f"gvc/{name}")
