from dataclasses import dataclass
from typing import (
    Any,
)
from .config import APIConfig
from ..config import WorkloadConfig
from ..utils import WebSocketAPI


IGNORED_CONTAINERS = ["cpln-mounter"]


class WorkloadDeploymentMixin:

    def get_workload_deployment(self,
        config: WorkloadConfig
    ) -> dict[str, Any]:
        if config.workload_id is None or config.location is None:
            raise ValueError("Config not set properly")

        endpoint = f'gvc/{config.gvc}/workload/{config.workload_id}/deployment/{config.location}'
        return self._get(endpoint)

    @classmethod
    def get_remote_api(cls,
        api_config: APIConfig,
        config: WorkloadConfig
    ):
        env = api_config.asdict()
        env["base_url"] = cls(**env).get_remote(config) + "/replicas"
        return cls(**env)

    def get_remote(self,
        config: WorkloadConfig
    ) -> str:
        return self.get_workload_deployment(config)["status"]["remote"]

    def get_remote_wss(self,
        config: WorkloadConfig
    ) -> str:
        return self.get_remote(config).replace("https:", "wss:") + "/remote"

    def get_replicas(self,
        config: WorkloadConfig
    ) -> list[str]:
        remote_api_client = self.get_remote_api(self.config, config)
        replicas = remote_api_client._get(f"/gvc/{config.gvc}/workload/{config.workload_id}")["items"]
        return replicas

    def get_containers(self,
        config: WorkloadConfig,
        ignored_containers: list[str] = IGNORED_CONTAINERS
    ) -> list[str]:
        item = self.get_workload_deployment(config)
        workload_versions = item["status"]["versions"]
        containers = [
            container
            for ver in workload_versions
            for container, container_specs in ver["containers"].items()
        ]
        return [x for x in containers if x not in ignored_containers]


class WorkloadApiMixin(WorkloadDeploymentMixin):

    def get_workload(self,
        config: WorkloadConfig
    ):
        """Get a workload by its ID."""
        endpoint = f'gvc/{config.gvc}/workload'
        if config.workload_id:
            endpoint += f'/{config.workload_id}'
        return self._get(endpoint)

    def delete_workload(self,
        config: WorkloadConfig
    ):
        """Delete a workload by its ID."""
        endpoint = f'gvc/{config.gvc}/workload/{config.workload_id}'
        return self._delete(endpoint)

    def exec_workload(self,
        config: WorkloadConfig,
        command: str
    ):
        containers = self.get_containers(config)
        replicas = self.get_replicas(config)
        remote_wss = self.get_remote_wss(config)
        request = dict(
            token = self.config.token,
            org = self.config.org,
            gvc = config.gvc,
            container = containers[-1],
            pod = replicas[-1],
            command = command,
        )
        print(request)
        websocket_api = WebSocketAPI(remote_wss)
        return websocket_api.exec(**request)
