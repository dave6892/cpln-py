from typing import Optional
from .resource import (
    Collection,
    Model
)
from ..api import APIClient
from ..config import WorkloadConfig


class Workload(Model):

    def get(self) -> dict[str, any]:
        return self.client.api.get_workload(self.config)

    def delete(self) -> None:
        print(f"Deleting Workload: {self}")
        self.client.api.delete_workload(self.config)
        print("Deleted!")

    def config(self, location: Optional[str] = None) -> WorkloadConfig:
        return WorkloadConfig(
            gvc=self.state["gvc"],
            workload_id=self.attrs["name"],
            location=location
        )

    def get_remote(self, location: Optional[str] = None) -> str:
        return self.client.api.get_remote(self.config(location=location))

    def get_remote_wss(self, location: Optional[str] = None) -> str:
        return self.client.api.get_remote_wss(self.config(location=location))

    def get_replicas(self, location: Optional[str] = None) -> list[str]:
        return self.client.api.get_replicas(self.config(location=location))


    def get_containers(self, location: Optional[str] = None) -> list[str]:
        return self.client.api.get_containers(self.config(location=location))


class WorkloadCollection(Collection):
    model = Workload

    def get(self,
        config: WorkloadConfig
    ):
        return self.prepare_model(
            self.client.api.get_workload(config=config),
            state = {
                "gvc": config.gvc
            }
        )

    def list(self,
        gvc: Optional[str] = None,
        config: Optional[WorkloadConfig] = None
    ) -> list[Workload]:
        if gvc is None and config is None:
            raise ValueError("Either GVC or WorkloadConfig must be defined.")

        config = WorkloadConfig(gvc=gvc) if gvc else config
        resp = self.client.api.get_workload(config)["items"]
        return [
            self.get(config=WorkloadConfig(
                gvc=config.gvc,
                workload_id=workload["name"]
            ))
            for workload in resp
        ]
