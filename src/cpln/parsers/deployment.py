from dataclasses import dataclass
from typing import Any, Optional, Union

import requests

from ..api.config import APIConfig
from ..config import WorkloadConfig
from ..errors import WebSocketExitCodeError
from ..utils import WebSocketAPI
from .base import BaseParser, preparse


@dataclass
class ContainerDeploymentResources(BaseParser):
    memory: int
    cpu: int
    replicas: int
    replicas_ready: int


@dataclass
class ContainerDeployment(BaseParser):
    """
    Represents a container extracted from Control Plane deployment data.

    Since Control Plane API doesn't expose direct container endpoints,
    this data model extracts container information from workload deployment payloads.
    """

    # Core identification
    name: str
    image: str
    resources: ContainerDeploymentResources
    message: str
    ready: bool

    @classmethod
    @preparse
    def parse(cls, data: dict[str, Any]) -> Any:
        resources = data.pop("resources")
        return cls(
            **cls.format_key_of_dict(data),
            resources=ContainerDeploymentResources.parse(resources),
        )


@dataclass
class Version(BaseParser):
    message: str
    ready: bool
    containers: list[ContainerDeployment]
    created: str
    workload: int  # this is the workload version number

    @classmethod
    @preparse
    def parse(cls, data: dict[str, Any]) -> Any:
        containers = data.pop("containers")
        containers_list = [
            ContainerDeployment.parse(container) for _, container in containers.items()
        ]
        return cls(**cls.format_key_of_dict(data), containers=containers_list)


@dataclass
class Internal(BaseParser):
    pod_status: dict[str, Any]
    pods_valid_zone: bool
    timestamp: str
    ksvc_status: dict[str, Any]


@dataclass
class Status(BaseParser):
    endpoint: str
    remote: str
    last_processed_version: str
    expected_deployment_version: str
    message: str
    internal: Internal
    ready: bool
    versions: list[Version]

    @classmethod
    @preparse
    def parse(cls, data: dict[str, Any]) -> Any:
        internal = data.pop("internal")
        versions = data.pop("versions")
        return cls(
            **cls.format_key_of_dict(data),
            internal=Internal.parse(internal),
            versions=[Version.parse(version) for version in versions],
        )


@dataclass
class Link(BaseParser):
    rel: str
    href: str


class APIClient(requests.Session):
    pass


@dataclass
class WorkloadReplica(BaseParser):
    name: str
    container: str
    config: WorkloadConfig
    api_config: APIConfig
    remote_wss: str

    def exec(
        self,
        command: Union[str, list[str]],
        verbose: bool = False,
    ) -> Any:
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
        error_message = []
        if self.config.container is None and self.container is None:
            error_message.append("Container")
        if self.config.replica is None and self.name is None:
            error_message.append("Replica")
        if self.config.remote_wss is None and self.remote_wss is None:
            error_message.append("Remote WSS")
        if error_message:
            raise ValueError(", ".join(error_message) + " not set")

        request = {
            "token": self.api_config.token,
            "org": self.api_config.org,
            "gvc": self.config.gvc,
            "container": self.container or self.config.container,
            "pod": self.name or self.config.replica,  # TODO: check if this is correct
            "command": command.split(" ") if isinstance(command, str) else command,
        }
        websocket_api = WebSocketAPI(
            self.remote_wss or self.config.remote_wss, verbose=verbose
        )
        try:
            return websocket_api.exec(**request)
        except WebSocketExitCodeError as e:
            print(f"Command failed with exit code: {e}")
            raise

    def ping(self, verbose: bool = False) -> None:
        self.exec(["echo", "ping"], verbose=verbose)


@dataclass
class Deployment(BaseParser):
    name: str
    status: Status
    last_modified: str
    kind: str
    links: list[Link]
    api_client: Optional[APIClient] = None
    config: Optional[WorkloadConfig] = None

    def __post_init__(self):
        self.api_client.config.base_url = self.get_remote() + "/replicas/"
        self.api_client.config.__post_init__()

    def export(self) -> dict[str, Any]:
        data = self.to_dict()
        self.pop_optional_fields(data)

        return {
            "name": data["name"],
            "status": data["status"],
            "last_modified": data["last_modified"],
            "kind": data["kind"],
        }

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        api_client: APIClient,
        config: WorkloadConfig,
    ) -> Any:
        return cls(
            name=data["name"],
            status=Status.parse(data["status"]),
            last_modified=data["lastModified"],
            kind=data["kind"],
            links=[Link.parse(link) for link in data["links"]],
            api_client=api_client,
            config=config,
        )

    def get_remote_deployment(self) -> dict[str, Any]:
        return self.api_client._get(
            f"/gvc/{self.config.gvc}/workload/{self.config.workload_id}"
        )

    def get_replicas(self) -> dict[str, list[WorkloadReplica]]:
        return {
            container_name: [
                WorkloadReplica.parse(
                    {
                        "name": replica,
                        "container": container_name,
                        "config": self.config,
                        "remote_wss": self.get_remote_wss(),
                        "api_config": self.api_client.config,
                    }
                )
                for replica in self.get_remote_deployment()["items"]
            ]
            for container_name in self.get_containers()
        }

    def get_remote_wss(self) -> str:
        return self.status.remote.replace("https:", "wss:") + "/remote"

    def get_remote(self) -> str:
        return self.status.remote

    def get_containers(self) -> dict[str, ContainerDeployment]:
        return {
            container.name: container
            for version in self.status.versions
            for container in version.containers
        }
