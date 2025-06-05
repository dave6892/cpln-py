from typing import (
    Any,
)

from ..config import WorkloadConfig
from ..utils import WebSocketAPI
from .config import APIConfig

IGNORED_CONTAINERS = ["cpln-mounter"]


class WorkloadDeploymentMixin:
    """
    A mixin class that provides workload deployment-related API methods.
    """

    def get_workload_deployment(self, config: WorkloadConfig) -> dict[str, Any]:
        """
        Retrieves deployment information for a specific workload.

        Args:
            config (WorkloadConfig): Configuration object containing workload details

        Returns:
            dict: Deployment information for the workload

        Raises:
            ValueError: If the config is not properly set
            APIError: If the request fails
        """
        if config.workload_id is None or config.location is None:
            raise ValueError("Config not set properly")

        endpoint = f"gvc/{config.gvc}/workload/{config.workload_id}/deployment/{config.location}"
        return self._get(endpoint)

    @classmethod
    def get_remote_api(cls, api_config: APIConfig, config: WorkloadConfig):
        """
        Creates a new API client instance for remote operations.

        Args:
            api_config (APIConfig): API configuration
            config (WorkloadConfig): Workload configuration

        Returns:
            WorkloadDeploymentMixin: A new instance configured for remote operations
        """
        env = api_config.asdict()
        env["base_url"] = cls(**env).get_remote(config) + "/replicas"
        return cls(**env)

    def get_remote(self, config: WorkloadConfig) -> str:
        """
        Gets the remote URL for a workload deployment.

        Args:
            config (WorkloadConfig): Configuration object containing workload details

        Returns:
            str: The remote URL for the workload deployment
        """
        return self.get_workload_deployment(config)["status"]["remote"]

    def get_remote_wss(self, config: WorkloadConfig) -> str:
        """
        Gets the WebSocket URL for a workload deployment.

        Args:
            config (WorkloadConfig): Configuration object containing workload details

        Returns:
            str: The WebSocket URL for the workload deployment
        """
        return self.get_remote(config).replace("https:", "wss:") + "/remote"

    def get_replicas(self, config: WorkloadConfig) -> list[str]:
        """
        Gets the list of replicas for a workload.

        Args:
            config (WorkloadConfig): Configuration object containing workload details

        Returns:
            list[str]: List of replica names
        """
        remote_api_client = self.get_remote_api(self.config, config)
        replicas = remote_api_client._get(
            f"/gvc/{config.gvc}/workload/{config.workload_id}"
        )["items"]
        return replicas

    def get_containers(
        self, config: WorkloadConfig, ignored_containers: list[str] = IGNORED_CONTAINERS
    ) -> list[str]:
        """
        Gets the list of containers for a workload, excluding ignored containers.

        Args:
            config (WorkloadConfig): Configuration object containing workload details
            ignored_containers (list[str], optional): List of container names to ignore

        Returns:
            list[str]: List of container names
        """
        item = self.get_workload_deployment(config)
        workload_versions = item["status"]["versions"]
        containers = [
            container
            for ver in workload_versions
            for container, container_specs in ver["containers"].items()
        ]
        return [x for x in containers if x not in ignored_containers]


class WorkloadApiMixin(WorkloadDeploymentMixin):
    """
    A mixin class that provides workload-related API methods.
    """

    def get_workload(self, config: WorkloadConfig):
        """
        Retrieves information about a workload.

        Args:
            config (WorkloadConfig): Configuration object containing workload details

        Returns:
            dict: Workload information

        Raises:
            APIError: If the request fails
        """
        endpoint = f"gvc/{config.gvc}/workload"
        if config.workload_id:
            endpoint += f"/{config.workload_id}"
        return self._get(endpoint)

    def create_workload(
        self,
        config: WorkloadConfig,
        metadata: dict[str, Any],
    ):
        """
        Creates a workload.
        """
        endpoint = f"gvc/{config.gvc}/workload"
        return self._post(endpoint, data=metadata)

    def delete_workload(self, config: WorkloadConfig):
        """
        Deletes a workload.

        Args:
            config (WorkloadConfig): Configuration object containing workload details

        Returns:
            requests.Response: The response from the API

        Raises:
            APIError: If the request fails
        """
        endpoint = f"gvc/{config.gvc}/workload/{config.workload_id}"
        return self._delete(endpoint)

    def patch_workload(self, config: WorkloadConfig, data: dict[str, Any]):
        """
        Updates a workload with the provided data.

        Args:
            config (WorkloadConfig): Configuration object containing workload details
            data (dict): The data to update the workload with

        Returns:
            requests.Response: The response from the API

        Raises:
            APIError: If the request fails
        """
        endpoint = f"gvc/{config.gvc}/workload/{config.workload_id}"
        return self._patch(endpoint, data=data)

    def exec_workload(self, config: WorkloadConfig, command: str):
        """
        Executes a command in a workload container.

        Args:
            config (WorkloadConfig): Configuration object containing workload details
            command (str): The command to execute

        Returns:
            Any: The result of the command execution

        Raises:
            APIError: If the request fails
        """
        containers = self.get_containers(config)
        replicas = self.get_replicas(config)
        remote_wss = self.get_remote_wss(config)
        request = {
            "token": self.config.token,
            "org": self.config.org,
            "gvc": config.gvc,
            "container": containers[-1],
            "pod": replicas[-1],
            "command": command.split(" ") if isinstance(command, str) else command,
        }
        websocket_api = WebSocketAPI(remote_wss)
        return websocket_api.exec(**request)
