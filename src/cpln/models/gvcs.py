from .resource import Collection, Model


class GVC(Model):

    def get(self) -> dict[str, any]:
        return self.client.api.get_gvc(self.attrs["name"]).json()

    def create(self) -> None:
        print(f"Creating GVC: {self}")
        self.client.api.create_gvc(
            self.attrs["name"],
            self.attrs["description"]
        )
        print("Created!")

    def delete(self) -> None:
        print(f"Deleting GVC: {self}")
        self.client.api.delete_gvc(self.attrs["name"])
        print("Deleted!")


class GVCCollection(Collection):
    model = GVC

    def get(self, name: str):
        return self.prepare_model(self.client.api.get_gvc(name).json())

    def list(self):
        resp = self.client.api.get_gvc()
        return [self.get(gvc["name"]) for gvc in resp.json()["items"]]
