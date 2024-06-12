from .resource import Collection, Model


class GVC(Model):
    id_attribute = "id"


class GVCCollection(Collection):
    model = GVC

    def get(self, name: str):
        return self.prepare_model(self.client.api.get_gvc(name).json())

    def list(self):
        resp = self.client.api.get_gvc()
        return [self.get(gvc["name"]) for gvc in resp.json()["items"]]
