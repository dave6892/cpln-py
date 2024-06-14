from .resource import (
    Collection,
    Model
)


class Workload(Model):

    def get(self) -> dict[str, any]:
        return self.client.api.get_workload(
            self.state["gvc"],
            self.attrs["name"]
        )

    def delete(self) -> None:
        print(f"Deleting Workload: {self}")
        self.client.api.delete_workload(
            self.state["gvc"],
            self.attrs["name"]
        )
        print("Deleted!")


class WorkloadCollection(Collection):
    model = Workload

    def get(self,
        gvc: str,
        workload_id: str,
    ):
        return self.prepare_model(
            self.client.api.get_workload(
                gvc = gvc,
                workload_id = workload_id
            ),
            state = {
                "gvc": gvc
            }
        )

    def list(self,
        gvc: str
    ):
        resp = self.client.api.get_workload(gvc = gvc)["items"]
        return [self.get(gvc=gvc, workload_id=workload["name"]) for workload in resp]
