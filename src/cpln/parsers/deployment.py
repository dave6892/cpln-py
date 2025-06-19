from dataclasses import dataclass
from typing import Any, Optional, Union

import requests

from ..api.config import APIConfig
from ..config import WorkloadConfig
from ..errors import WebSocketExitCodeError
from ..filters.container import ContainerFilterOptions
from ..utils import WebSocketAPI
from .base import BaseParser, preparse


@dataclass
class ContainerDeploymentResources(BaseParser):
    """
    Represents resource allocation for a container deployment.

    Attributes:
        memory (int): Memory allocation in bytes
        cpu (int): CPU allocation
        replicas (int): Total number of replicas
        replicas_ready (int): Number of ready replicas
    """

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

    def is_healthy(self) -> bool:
        """
        Determine if the container deployment is healthy.

        Returns:
            bool: True if the container is considered healthy, False otherwise

        A container is considered healthy if:
        - It is ready (self.ready is True)
        - Has at least one ready replica
        - Message doesn't indicate error states
        """
        # Basic readiness check
        if not self.ready:
            return False

        # Check if we have ready replicas
        if self.resources.replicas_ready == 0:
            return False

        # Check for common error message patterns
        error_keywords = [
            "error",
            "failed",
            "crash",
            "terminated",
            "unhealthy",
            "unavailable",
            "timeout",
        ]

        message_lower = self.message.lower() if self.message else ""
        if any(keyword in message_lower for keyword in error_keywords):
            return False

        return True

    def get_resource_utilization(self) -> dict[str, Optional[float]]:
        """
        Calculate resource utilization percentages for the container.

        Returns:
            dict: Dictionary containing utilization percentages:
                - 'replica_utilization': Percentage of replicas that are ready
                - 'cpu': CPU utilization (placeholder - actual metrics would need monitoring API)
                - 'memory': Memory utilization (placeholder - actual metrics would need monitoring API)

        Note:
            CPU and memory utilization require access to metrics/monitoring APIs
            which are not available through the standard Control Plane deployment API.
            These return None as placeholders for potential future implementation.
        """
        utilization = {
            "replica_utilization": None,
            "cpu": None,  # Would need metrics API access
            "memory": None,  # Would need metrics API access
        }

        # Calculate replica utilization if we have replica data
        if self.resources.replicas > 0:
            utilization["replica_utilization"] = (
                self.resources.replicas_ready / self.resources.replicas
            ) * 100.0
        else:
            utilization["replica_utilization"] = 0.0

        # CPU and memory utilization would require additional API calls
        # to monitoring/metrics endpoints that aren't part of the deployment API
        # For now, these remain None as placeholders

        return utilization


@dataclass
class Version(BaseParser):
    """
    Represents a deployment version from the Control Plane API.

    Attributes:
        message (str): Status message for this version
        ready (bool): Whether this version is ready
        containers (list[ContainerDeployment]): List of container deployments
        created (str): Creation timestamp
        workload (int): The workload version number
    """

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
    """
    Represents internal deployment status information.

    Attributes:
        pod_status (dict[str, Any]): Kubernetes pod status information
        pods_valid_zone (bool): Whether pods are in a valid zone
        timestamp (str): Timestamp of status
        ksvc_status (dict[str, Any]): Knative service status information
    """

    pod_status: dict[str, Any]
    pods_valid_zone: bool
    timestamp: str
    ksvc_status: dict[str, Any]


@dataclass
class Status(BaseParser):
    """
    Represents the status of a deployment.

    Attributes:
        endpoint (str): The deployment endpoint URL
        remote (str): Remote endpoint URL
        last_processed_version (str): Last processed version identifier
        expected_deployment_version (str): Expected deployment version
        message (str): Status message
        internal (Internal): Internal status information
        ready (bool): Whether the deployment is ready
        versions (list[Version]): List of deployment versions
    """

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
    """
    Represents a link object from the API response.

    Attributes:
        rel (str): The relationship type of the link
        href (str): The URL of the link
    """

    rel: str
    href: str


class APIClient(requests.Session):
    pass


@dataclass
class WorkloadReplica(BaseParser):
    """
    Represents a replica of a workload container.

    Attributes:
        name (str): Name of the replica
        container (str): Container name
        config (WorkloadConfig): Workload configuration
        api_config (APIConfig): API configuration
        remote_wss (str): Remote WebSocket URL
    """

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
    """
    Represents a deployment in the Control Plane system.

    This class encapsulates deployment information including status, metadata,
    and provides methods for interacting with deployment replicas.

    Attributes:
        name (str): Name of the deployment
        status (Status): Current deployment status
        last_modified (str): Last modification timestamp
        kind (str): Type/kind of the deployment
        links (list[Link]): Related links for this deployment
        api_client (Optional[APIClient]): API client for making requests
        config (Optional[WorkloadConfig]): Workload configuration
    """

    name: str
    status: Status
    last_modified: str
    kind: str
    links: list[Link]
    api_client: Optional[APIClient] = None
    config: Optional[WorkloadConfig] = None

    def __post_init__(self):
        # Don't modify the original API client at all
        # We'll create a separate config only when needed for replica operations
        pass

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

    def find_containers(
        self, filters: Optional["ContainerFilterOptions"] = None
    ) -> dict[str, ContainerDeployment]:
        """
        Find containers within this deployment matching the specified filters.

        This method filters live deployment containers with health status and resource data.
        Unlike workload specification filtering, this includes live status information.

        Args:
            filters: ContainerFilterOptions instance with filtering criteria

        Returns:
            Dict of container name -> ContainerDeployment instances matching the filter criteria

        Example:
            # Find unhealthy containers
            filters = ContainerFilterOptions(health_status=["unhealthy"])
            containers = deployment.find_containers(filters)

            # Find containers with high resource usage
            filters = ContainerFilterOptions(resource_thresholds={"replica_utilization": 80.0})
            containers = deployment.find_containers(filters)
        """
        from ..filters.container import (
            _match_patterns,
            _match_resource_thresholds,
        )

        if filters is None:
            return self.get_containers()

        if not filters.has_filters():
            return self.get_containers()

        all_containers = self.get_containers()
        filtered_containers = {}

        for name, container in all_containers.items():
            # Check name pattern matching
            if filters.name_patterns and not _match_patterns(
                container.name, filters.name_patterns
            ):
                continue

            # Check image pattern matching
            if filters.image_patterns and not _match_patterns(
                container.image, filters.image_patterns
            ):
                continue

            # Check health status filtering (available for deployment containers)
            if filters.health_status:
                container_health = "healthy" if container.is_healthy() else "unhealthy"
                if container_health not in filters.health_status:
                    continue

            # Check resource threshold filtering (available for deployment containers)
            if filters.resource_thresholds:
                container_resources = container.get_resource_utilization()
                if not _match_resource_thresholds(
                    container_resources, filters.resource_thresholds
                ):
                    continue

            # Check replica state filtering
            if filters.replica_states and (
                (container.ready and "ready" not in filters.replica_states)
                or (not container.ready and "pending" not in filters.replica_states)
            ):
                continue

            # Note: Port and environment filtering are not available for deployment containers
            # as this information is in the workload specification, not deployment status
            if filters.port_filters or filters.environment_filters:
                # These filters require workload specification data
                # For now, we'll skip these filters for deployment containers
                pass

            filtered_containers[name] = container

        return filtered_containers

    def get_unhealthy_containers(self) -> dict[str, ContainerDeployment]:
        """
        Quick access to unhealthy containers in this deployment.

        Returns:
            Dict of container name -> ContainerDeployment instances that are unhealthy
        """
        from ..filters.container import ContainerFilterOptions

        filters = ContainerFilterOptions(health_status=["unhealthy"])
        return self.find_containers(filters)

    def get_containers_by_resource_usage(
        self,
        cpu_threshold: Optional[float] = None,
        memory_threshold: Optional[float] = None,
        replica_threshold: Optional[float] = None,
    ) -> dict[str, ContainerDeployment]:
        """
        Find containers exceeding resource thresholds.

        Args:
            cpu_threshold: CPU utilization threshold (0-100)
            memory_threshold: Memory utilization threshold (0-100)
            replica_threshold: Replica utilization threshold (0-100)

        Returns:
            Dict of container name -> ContainerDeployment instances exceeding thresholds
        """
        from ..filters.container import ContainerFilterOptions

        thresholds = {}
        if cpu_threshold is not None:
            thresholds["cpu"] = cpu_threshold
        if memory_threshold is not None:
            thresholds["memory"] = memory_threshold
        if replica_threshold is not None:
            thresholds["replica_utilization"] = replica_threshold

        if not thresholds:
            return {}

        filters = ContainerFilterOptions(resource_thresholds=thresholds)
        return self.find_containers(filters)

    def count_containers(
        self, filters: Optional["ContainerFilterOptions"] = None
    ) -> int:
        """
        Count containers within this deployment matching the specified filters.

        Args:
            filters: ContainerFilterOptions instance with filtering criteria

        Returns:
            Number of containers matching the filter criteria
        """
        return len(self.find_containers(filters))
