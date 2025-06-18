from .resource import Collection, Model


class Image(Model):
    """
    An image on the server.
    """

    def get(self) -> dict[str, any]:
        """
        Get the image.

        Returns:
            (dict): The image.

        Raises:
            :py:class:`cpln.errors.NotFound`
                If the image does not exist.
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.get_image(self.attrs["name"])

    def delete(self) -> None:
        """
        Delete the image.

        Raises:
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        print(f"Deleting Image: {self}")
        self.client.api.delete_image(self.attrs["name"])
        print("Deleted!")


class ImageCollection(Collection):
    """
    Images on the server.
    """

    model = Image

    def get(self, image_id: str):
        """
        Gets an image.

        Args:
            image_id (str): The name of the image.

        Returns:
            (:py:class:`Image`): The image.

        Raises:
            :py:class:`cpln.errors.ImageNotFound`
                If the image does not exist.
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        return self.prepare_model(self.client.api.get_image(image_id))

    def list(self):
        """
        List images on the registry.

        Returns:
            (list of :py:class:`Image`): The images.

        Raises:
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.get_image()["items"]
        return [self.prepare_model(image) for image in resp]
