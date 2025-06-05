class ImageApiMixin:
    """
    A mixin class that provides image-related API methods.
    """

    def get_image(self, image_id: str = None):
        """
        Retrieves image information from the Control Plane API.

        Args:
            image_id (str, optional): The ID of the specific image to retrieve.
                If not provided, returns a list of all images.

        Returns:
            dict: The image information or list of images

        Raises:
            APIError: If the request fails
        """
        endpoint = "image"
        if image_id:
            endpoint += f"/{image_id}"
        return self._get(endpoint)

    def delete_image(self, image_id):
        """
        Deletes an image from the Control Plane.

        Args:
            image_id (str): The ID of the image to delete

        Returns:
            requests.Response: The response from the API

        Raises:
            APIError: If the request fails
        """
        return self._delete(f"image/{image_id}")
