from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config import WorkloadConfig
from ..errors import APIError
from .resource import Collection


@dataclass
class Container:
    """
    Represents a container extracted from Control Plane deployment data.

    Since Control Plane API doesn't expose direct container endpoints,
    this data model extracts container information from workload deployment payloads.
    """

    # Core identification
    name: str
    image: str
    workload_name: str
    gvc_name: str
    location: str

    # Status and health
    status: Optional[str] = None
    health_status: Optional[str] = None
    ready_replicas: Optional[int] = None
    total_replicas: Optional[int] = None
    restart_count: Optional[int] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_restart_time: Optional[datetime] = None

    # Configuration
    environment_variables: Optional[Dict[str, str]] = None
    resource_limits: Optional[Dict[str, Any]] = None
    ports: Optional[List[Dict[str, Any]]] = None

    # Resource utilization
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None

    # Deployment metadata
    deployment_name: Optional[str] = None
    version: Optional[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.environment_variables is None:
            self.environment_variables = {}
        if self.resource_limits is None:
            self.resource_limits = {}
        if self.ports is None:
            self.ports = []

    @classmethod
    def from_deployment_payload(
        cls,
        container_data: Dict[str, Any],
        workload_name: str,
        gvc_name: str,
        location: str,
        deployment_name: Optional[str] = None,
        version_data: Optional[Dict[str, Any]] = None,
    ) -> "Container":
        """
        Create a Container instance from deployment payload data.

        Args:
            container_data: Container data from deployment spec.containers[]
            workload_name: Name of the parent workload
            gvc_name: Name of the parent GVC
            location: Deployment location
            deployment_name: Name of the deployment
            version_data: Optional version metadata

        Returns:
            Container instance
        """
        # Extract basic container info
        name = container_data.get("name", "")
        image = container_data.get("image", "")

        # Extract environment variables
        env_vars = {}
        for env in container_data.get("env", []):
            if isinstance(env, dict) and "name" in env and "value" in env:
                env_vars[env["name"]] = env["value"]

        # Extract resource limits
        resources = container_data.get("resources", {})
        resource_limits = {
            "cpu": resources.get("cpu"),
            "memory": resources.get("memory"),
        }

        # Extract ports
        ports = container_data.get("ports", [])

        # Extract version info if available
        version = None
        if version_data:
            version = version_data.get("version")

        return cls(
            name=name,
            image=image,
            workload_name=workload_name,
            gvc_name=gvc_name,
            location=location,
            deployment_name=deployment_name,
            version=version,
            environment_variables=env_vars,
            resource_limits=resource_limits,
            ports=ports,
        )

    @classmethod
    def from_job_payload(
        cls,
        container_data: Dict[str, Any],
        workload_name: str,
        gvc_name: str,
        location: str,
        job_data: Optional[Dict[str, Any]] = None,
    ) -> "Container":
        """
        Create a Container instance from job execution payload data.

        Args:
            container_data: Container data from job spec.job.containers[]
            workload_name: Name of the parent workload
            gvc_name: Name of the parent GVC
            location: Deployment location
            job_data: Optional job metadata

        Returns:
            Container instance
        """
        # Job containers are similar to deployment containers
        # but may have different structure
        return cls.from_deployment_payload(
            container_data=container_data,
            workload_name=workload_name,
            gvc_name=gvc_name,
            location=location,
            deployment_name=job_data.get("name") if job_data else None,
            version_data=job_data,
        )

    def update_status(
        self,
        status: Optional[str] = None,
        health_status: Optional[str] = None,
        ready_replicas: Optional[int] = None,
        total_replicas: Optional[int] = None,
        restart_count: Optional[int] = None,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
    ) -> None:
        """
        Update container status information.

        Args:
            status: Current container status
            health_status: Container health status
            ready_replicas: Number of ready replicas
            total_replicas: Total desired replicas
            restart_count: Container restart count
            cpu_usage: Current CPU utilization
            memory_usage: Current memory utilization
        """
        if status is not None:
            self.status = status
        if health_status is not None:
            self.health_status = health_status
        if ready_replicas is not None:
            self.ready_replicas = ready_replicas
        if total_replicas is not None:
            self.total_replicas = total_replicas
        if restart_count is not None:
            self.restart_count = restart_count
        if cpu_usage is not None:
            self.cpu_usage = cpu_usage
        if memory_usage is not None:
            self.memory_usage = memory_usage

        # Update timestamp
        self.updated_at = datetime.now()

    def is_healthy(self) -> bool:
        """
        Check if the container is healthy.

        Returns:
            True if container is healthy, False otherwise
        """
        if self.health_status:
            return self.health_status.lower() == "healthy"

        # Fallback to replica status if health status not available
        if self.ready_replicas is not None and self.total_replicas is not None:
            return self.ready_replicas == self.total_replicas

        # Default to unknown/unhealthy if no status available
        return False

    def get_resource_utilization(self) -> Dict[str, Optional[float]]:
        """
        Get current resource utilization.

        Returns:
            Dictionary with CPU and memory utilization percentages
        """
        return {
            "cpu": self.cpu_usage,
            "memory": self.memory_usage,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert container to dictionary representation.

        Returns:
            Dictionary representation of the container
        """
        return {
            "name": self.name,
            "image": self.image,
            "workload_name": self.workload_name,
            "gvc_name": self.gvc_name,
            "location": self.location,
            "status": self.status,
            "health_status": self.health_status,
            "ready_replicas": self.ready_replicas,
            "total_replicas": self.total_replicas,
            "restart_count": self.restart_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_restart_time": self.last_restart_time.isoformat()
            if self.last_restart_time
            else None,
            "environment_variables": self.environment_variables,
            "resource_limits": self.resource_limits,
            "ports": self.ports,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "deployment_name": self.deployment_name,
            "version": self.version,
        }


class ContainerParser:
    """
    Utility class for parsing container data from various Control Plane API payloads.
    """

    # Container names to ignore (system containers)
    IGNORED_CONTAINERS = ["cpln-mounter"]

    @classmethod
    def parse_deployment_containers(
        cls,
        deployment_data: Dict[str, Any],
        workload_name: str,
        gvc_name: str,
        location: str,
    ) -> List[Container]:
        """
        Parse containers from deployment data.

        Args:
            deployment_data: Full deployment payload
            workload_name: Name of the parent workload
            gvc_name: Name of the parent GVC
            location: Deployment location

        Returns:
            List of Container instances

        Raises:
            APIError: If deployment data is malformed
        """
        containers = []

        try:
            # Validate deployment data structure
            if (
                "status" not in deployment_data
                or "versions" not in deployment_data["status"]
            ):
                raise APIError("Invalid deployment data: missing status.versions")

            # Parse containers from deployment versions
            versions = deployment_data["status"]["versions"]

            for version_data in versions:
                if (
                    not isinstance(version_data, dict)
                    or "containers" not in version_data
                ):
                    continue

                version_containers = version_data["containers"]

                for container_name, container_spec in version_containers.items():
                    # Skip system containers
                    if container_name in cls.IGNORED_CONTAINERS:
                        continue

                    # Create container data dict for parsing
                    container_data = {"name": container_name, **container_spec}

                    container = Container.from_deployment_payload(
                        container_data=container_data,
                        workload_name=workload_name,
                        gvc_name=gvc_name,
                        location=location,
                        deployment_name=deployment_data.get("metadata", {}).get("name"),
                        version_data=version_data,
                    )

                    containers.append(container)

        except (KeyError, TypeError, AttributeError) as e:
            raise APIError(f"Failed to parse deployment containers: {e}") from e

        return containers

    @classmethod
    def parse_job_containers(
        cls,
        job_data: Dict[str, Any],
        workload_name: str,
        gvc_name: str,
        location: str,
    ) -> List[Container]:
        """
        Parse containers from job execution data.

        Args:
            job_data: Job execution payload
            workload_name: Name of the parent workload
            gvc_name: Name of the parent GVC
            location: Deployment location

        Returns:
            List of Container instances

        Raises:
            APIError: If job data is malformed
        """
        containers = []

        try:
            # Validate job data structure
            if (
                "spec" not in job_data
                or "job" not in job_data["spec"]
                or "containers" not in job_data["spec"]["job"]
            ):
                raise APIError("Invalid job data: missing spec.job.containers")

            # Parse containers from job spec
            job_containers = job_data["spec"]["job"]["containers"]

            for container_data in job_containers:
                if not isinstance(container_data, dict):
                    continue

                container_name = container_data.get("name")

                # Skip system containers
                if container_name in cls.IGNORED_CONTAINERS:
                    continue

                container = Container.from_job_payload(
                    container_data=container_data,
                    workload_name=workload_name,
                    gvc_name=gvc_name,
                    location=location,
                    job_data=job_data,
                )

                containers.append(container)

        except (KeyError, TypeError, AttributeError) as e:
            raise APIError(f"Failed to parse job containers: {e}") from e

        return containers

    @classmethod
    def parse_workload_spec_containers(
        cls,
        workload_spec: Dict[str, Any],
        workload_name: str,
        gvc_name: str,
        location: str = "unknown",
    ) -> List[Container]:
        """
        Parse containers from workload specification.

        Args:
            workload_spec: Workload spec data
            workload_name: Name of the workload
            gvc_name: Name of the parent GVC
            location: Deployment location

        Returns:
            List of Container instances

        Raises:
            APIError: If workload spec is malformed
        """
        containers = []

        try:
            # Validate workload spec structure
            if "containers" not in workload_spec:
                raise APIError("Invalid workload spec: missing containers")

            # Parse containers from workload spec
            spec_containers = workload_spec["containers"]

            for container_data in spec_containers:
                if not isinstance(container_data, dict):
                    continue

                container_name = container_data.get("name")

                # Skip system containers
                if container_name in cls.IGNORED_CONTAINERS:
                    continue

                container = Container.from_deployment_payload(
                    container_data=container_data,
                    workload_name=workload_name,
                    gvc_name=gvc_name,
                    location=location,
                )

                containers.append(container)

        except (KeyError, TypeError, AttributeError) as e:
            raise APIError(f"Failed to parse workload spec containers: {e}") from e

        return containers


class ContainerCollection(Collection):
    """
    A collection of containers that provides listing and search functionality.

    Since Control Plane API doesn't expose direct container endpoints,
    this collection iterates through workloads and deployments to discover containers.
    """

    model = Container

    def list(
        self,
        gvc: str,
        workload_name: str,
        location: Optional[str] = None,
    ) -> List[Container]:
        """
        List containers for a SPECIFIC workload only.

        Args:
            gvc: Name of the GVC
            workload_name: Name of the workload (REQUIRED)
            location: Optional location filter

        Returns:
            List of Container instances

        Note:
            For multi-workload container listing, iterate through workloads:

            for workload in client.workloads.list(gvc='my-gvc'):
                containers = workload.get_container_objects()
                # ... process containers

        Raises:
            APIError: If the API request fails
        """
        # Only handle single workload's containers
        workload_config = WorkloadConfig(gvc=gvc, workload_id=workload_name)

        return self._get_workload_containers(workload_config, location)

    def _get_workload_containers(
        self,
        workload_config: WorkloadConfig,
        location_filter: Optional[str] = None,
    ) -> List[Container]:
        """
        Get containers for a specific workload.

        Args:
            workload_config: Workload configuration
            location_filter: Optional location filter to only get containers
                          from a specific deployment location (e.g., 'aws-us-east-1')

        Returns:
            List of Container instances
        """
        containers = []

        try:
            # Get workload details to find available locations
            workload_data = self._get_workload_data(workload_config)

            # If no location filter, try to get deployments from workload spec
            if location_filter:
                locations = [location_filter]
            else:
                # Try to infer locations from workload data or use common locations
                locations = self._infer_workload_locations(workload_data)

            for location in locations:
                try:
                    deployment_containers = self._get_deployment_containers(
                        workload_config, location
                    )
                    containers.extend(deployment_containers)

                except (APIError, Exception):
                    # Skip locations where deployment data is not available
                    continue

        except APIError:
            # Skip workloads that can't be accessed
            pass

        return containers

    def _get_workload_data(self, workload_config: WorkloadConfig) -> Dict[str, Any]:
        """
        Get workload data from the API.

        Args:
            workload_config: Workload configuration

        Returns:
            Workload data dictionary
        """
        return self.client.api.get_workload(workload_config)

    def _get_deployment_containers(
        self, workload_config: WorkloadConfig, location: str
    ) -> List[Container]:
        """
        Get containers for a specific workload deployment.

        Args:
            workload_config: Workload configuration
            location: Deployment location

        Returns:
            List of Container instances
        """
        # Get deployment data for this location
        deployment_config = WorkloadConfig(
            gvc=workload_config.gvc,
            workload_id=workload_config.workload_id,
            location=location,
        )

        deployment_data = self.client.api.get_workload_deployment(deployment_config)

        # Parse containers from deployment data
        return ContainerParser.parse_deployment_containers(
            deployment_data=deployment_data,
            workload_name=workload_config.workload_id,
            gvc_name=workload_config.gvc,
            location=location,
        )

    def _infer_workload_locations(self, workload_data: Dict[str, Any]) -> List[str]:
        """
        Infer possible deployment locations for a workload.

        Args:
            workload_data: Workload specification data

        Returns:
            List of possible location names
        """
        # Try to extract locations from workload spec
        locations = []

        # Check if locations are specified in workload spec
        spec = workload_data.get("spec", {})
        default_options = spec.get("defaultOptions", {})

        # Look for location hints in various places
        if "locations" in default_options:
            locations.extend(default_options["locations"])

        # If no locations found, try common location names
        if not locations:
            common_locations = [
                "aws-us-east-1",
                "aws-us-west-2",
                "aws-eu-west-1",
                "gcp-us-central1",
                "azure-eastus",
            ]
            locations = common_locations

        return locations

    def get(self, **kwargs) -> Optional[Container]:
        """
        Get a specific container by name within a workload.

        For containers, you must provide:
        - gvc: Name of the GVC
        - workload_name: Name of the workload
        - container_name: Name of the container to find
        - location: Optional location filter to search in specific deployment

        Args:
            **kwargs: Container search parameters

        Returns:
            Container instance if found, None otherwise

        Raises:
            ValueError: If required parameters are missing
            APIError: If the API request fails
            NotImplementedError: If called with unsupported parameters (like 'id')
        """
        # Check for the old-style 'id' parameter that tests might use
        if "id" in kwargs:
            raise NotImplementedError(
                "Container retrieval by ID is not supported. "
                "Use get(gvc='name', workload_name='name', container_name='name') instead."
            )

        # Extract required parameters
        gvc = kwargs.get("gvc")
        workload_name = kwargs.get("workload_name")
        container_name = kwargs.get("container_name")
        location = kwargs.get("location")

        # Validate required parameters
        if not all([gvc, workload_name, container_name]):
            raise ValueError(
                "get() requires 'gvc', 'workload_name', and 'container_name' parameters"
            )

        # List all containers for the workload
        containers = self.list(gvc=gvc, workload_name=workload_name, location=location)

        # Find the specific container by name
        for container in containers:
            if container.name == container_name:
                return container

        return None

    def create(self, **kwargs) -> Container:
        """
        Create a container (not implemented for read-only model).

        Raises:
            NotImplementedError: Containers are read-only in this implementation
        """
        raise NotImplementedError(
            "Container creation is not supported. "
            "Containers are managed through workload deployments."
        )
