from .resource import Collection, Model


class Image(Model):

    def get(self) -> dict[str, any]:
        return self.client.api.get_image(self.attrs["id"])["items"]

    def delete(self) -> None:
        print(f"Deleting Image: {self}")
        self.client.api.delete_image(self.attrs["id"])
        print("Deleted!")


class ImageCollection(Collection):
    model = Image

    def get(self, image_id: str):
        return self.prepare_model(
            self.client.api.get_image(image_id)
        )

    def list(self):
        resp = self.client.api.get_image()["items"]
        return [self.get(image["name"]) for image in resp]
