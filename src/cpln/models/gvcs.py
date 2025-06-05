from .resource import Collection, Model


class GVC(Model):
    """
    A GVC (Global Virtual Cloud) on the server.
    """

    def get(self) -> dict[str, any]:
        """
        Get the GVC.

        Returns:
            (dict): The GVC.

        Raises:
            :py:class:`cpln.errors.NotFound`
                If the GVC does not exist.
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.get_gvc(self.attrs["name"])

    def create(self) -> None:
        """
        Create the GVC.

        Raises:
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        print(f"Creating GVC: {self}")
        self.client.api.create_gvc(self.attrs["name"], self.attrs["description"])
        print("Created!")

    def delete(self) -> None:
        """
        Delete the GVC.

        Raises:
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        print(f"Deleting GVC: {self}")
        self.client.api.delete_gvc(self.attrs["name"])
        print("Deleted!")


class GVCCollection(Collection):
    """
    GVCs on the server.
    """

    model = GVC

    def get(self, name: str):
        """
        Get a GVC.

        Args:
            name (str): The name of the GVC.

        Returns:
            (:py:class:`GVC`): The GVC.

        Raises:
            :py:class:`cpln.errors.NotFound`
                If the GVC does not exist.
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        return self.prepare_model(self.client.api.get_gvc(name))

    def list(self):
        """
        List GVCs on the server.

        Returns:
            (list[:py:class:`GVC`]): The GVCs.

        Raises:
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.get_gvc()["items"]
        return [self.prepare_model(gvc) for gvc in resp]
