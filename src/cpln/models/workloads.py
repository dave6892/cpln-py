from typing import Optional
from .resource import (
    Collection,
    Model
)
from ..api import APIClient
from ..config import WorkloadConfig


class Workload(Model):
    """
    A workload on the server.
    """
    def get(self) -> dict[str, any]:
        """
        Get the workload.

        Returns:
            (dict): The workload.

        Raises:
            :py:class:`cpln.errors.NotFound`
                If the workload does not exist.
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.get_workload(self.config)

    def delete(self) -> None:
        """
        Delete the workload.

        Raises:
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        print(f"Deleting Workload: {self}")
        self.client.api.delete_workload(self.config)
        print("Deleted!")

    def config(self, location: Optional[str] = None) -> WorkloadConfig:
        """
        Get the workload config.

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (WorkloadConfig): The workload config.
        """
        return WorkloadConfig(
            gvc=self.state["gvc"],
            workload_id=self.attrs["name"],
            location=location
        )

    def get_remote(self, location: Optional[str] = None) -> str:
        """
        Get the remote URL of the workload.

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (str): The remote of the workload.
        """
        return self.client.api.get_remote(self.config(location=location))

    def get_remote_wss(self, location: Optional[str] = None) -> str:
        """
        Get the remote WSS URL of the workload.

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (str): The remote WSS of the workload.
        """
        return self.client.api.get_remote_wss(self.config(location=location))

    def get_replicas(self, location: Optional[str] = None) -> list[str]:
        """
        Get the replicas of the workload.

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (list): The replicas of the workload.
        """
        return self.client.api.get_replicas(self.config(location=location))


    def get_containers(self, location: Optional[str] = None) -> list[str]:
        """
        Get the containers of the workload.

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (list): The containers of the workload.
        """
        return self.client.api.get_containers(self.config(location=location))


class WorkloadCollection(Collection):
    """
    Workloads on the server.
    """
    model = Workload

    def get(self,
        config: WorkloadConfig
    ):
        """
        Gets a workload.

        Args:
            config (WorkloadConfig): The workload config.

        Returns:
            (:py:class:`Workload`): The workload.

        Raises:
            :py:class:`cpln.errors.NotFound`
                If the workload does not exist.
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
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
        """
        List workloads.

        Args:
            gvc (str): The GVC to list workloads from.
            config (WorkloadConfig): The workload config.

        Returns:
            (list): The workloads.

        Raises:
            ValueError: If neither gvc nor config is defined.
        """
        if gvc is None and config is None:
            raise ValueError("Either GVC or WorkloadConfig must be defined.")

        config = WorkloadConfig(gvc=gvc) if gvc else config
        resp = self.client.api.get_workload(config)["items"]
        return {
            workload["name"]: self.get(
                config=WorkloadConfig(
                    gvc=config.gvc,
                    workload_id=workload["name"]
                )
            )
            for workload in resp
        }