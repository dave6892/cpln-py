import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

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

    def update_status_from_deployment(
        self,
        deployment_status: Dict[str, Any],
        client=None,
    ) -> None:
        """
        Update container status from Control Plane deployment status data.

        This method uses the StatusParser, HealthEvaluator, and MetricsExtractor
        to populate status information from real-time deployment data.

        Args:
            deployment_status: Deployment status data from the API
            client: Optional client for additional API calls
        """
        # Parse deployment status information
        status_info = StatusParser.parse_deployment_status(deployment_status)

        # Parse container-specific status from versions
        versions = deployment_status.get("versions", [])
        container_status = StatusParser.parse_container_status_from_versions(
            versions, self.name
        )

        # Evaluate health status
        health_summary = HealthEvaluator.get_health_summary(
            status_info, container_status
        )

        # Extract resource metrics
        resource_metrics = MetricsExtractor.extract_resource_metrics(
            status_info, container_status
        )
        replica_metrics = MetricsExtractor.calculate_replica_metrics(status_info)

        # Update container status fields
        self.health_status = health_summary["health_status"]

        # Update status based on deployment readiness
        if status_info.get("ready"):
            self.status = "running"
        elif status_info.get("deploying"):
            self.status = "deploying"
        else:
            self.status = "pending"

        # Update replica information
        if replica_metrics["ready_replicas"] is not None:
            self.ready_replicas = replica_metrics["ready_replicas"]
        if replica_metrics["total_replicas"] is not None:
            self.total_replicas = replica_metrics["total_replicas"]
        if replica_metrics["restart_count"] is not None:
            self.restart_count = replica_metrics["restart_count"]

        # Update resource utilization
        if resource_metrics["cpu_usage"] is not None:
            self.cpu_usage = resource_metrics["cpu_usage"]
        if resource_metrics["memory_usage"] is not None:
            self.memory_usage = resource_metrics["memory_usage"]

        # Update timestamp
        self.updated_at = datetime.now()

    def refresh_status(self, client) -> bool:
        """
        Refresh container status from the Control Plane API.

        Args:
            client: Control Plane client instance

        Returns:
            True if status was successfully refreshed, False otherwise
        """
        try:
            from ..config import WorkloadConfig

            # Create workload config for API call
            workload_config = WorkloadConfig(
                gvc=self.gvc_name,
                workload_id=self.workload_name,
                location=self.location,
            )

            # Get current deployment data
            deployment_data = client.api.get_workload_deployment(workload_config)

            # Extract deployment status
            deployment_status = deployment_data.get("status", {})

            # Update status from deployment data
            self.update_status_from_deployment(deployment_status, client)

            return True

        except Exception:
            # Silently fail for status refresh to avoid breaking existing functionality
            return False

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive health summary for this container.

        Returns:
            Dictionary containing health status and related information
        """
        return {
            "health_status": self.health_status or "unknown",
            "is_healthy": self.is_healthy(),
            "status": self.status,
            "ready_replicas": self.ready_replicas,
            "total_replicas": self.total_replicas,
            "restart_count": self.restart_count,
            "last_updated": self.updated_at.isoformat() if self.updated_at else None,
        }

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


class StatusParser:
    """
    Utility class for parsing container status and health information from deployment status payloads.

    This class extracts real-time status information from Control Plane's deployment_status schema
    as defined in the OpenAPI specification.
    """

    @classmethod
    def parse_deployment_status(
        cls,
        deployment_status: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse deployment status information from Control Plane deployment_status payload.

        Args:
            deployment_status: Deployment status data from the API

        Returns:
            Dictionary containing parsed status information
        """
        # Validate and extract basic status information with type checking
        ready_raw = deployment_status.get("ready", False)
        deploying_raw = deployment_status.get("deploying", False)

        status_info = {
            "endpoint": deployment_status.get("endpoint"),
            "remote": deployment_status.get("remote"),
            "last_processed_version": deployment_status.get("lastProcessedVersion"),
            "expected_deployment_version": deployment_status.get(
                "expectedDeploymentVersion"
            ),
            "ready": ready_raw if isinstance(ready_raw, bool) else False,
            "deploying": deploying_raw if isinstance(deploying_raw, bool) else False,
            "message": deployment_status.get("message"),
        }

        # Parse version information
        versions = deployment_status.get("versions", [])
        if versions and isinstance(versions, list):
            latest_version = versions[-1]  # Most recent version
            if isinstance(latest_version, dict):
                status_info.update(
                    {
                        "latest_version_name": latest_version.get("name"),
                        "latest_version_created": latest_version.get("created"),
                        "latest_version_workload": latest_version.get("workload"),
                        "latest_version_gvc": latest_version.get("gvc"),
                        "latest_version_ready": latest_version.get("ready"),
                        "latest_version_message": latest_version.get("message"),
                        "latest_version_zone": latest_version.get("zone"),
                    }
                )
        else:
            # Set default None values when versions is not valid
            status_info.update(
                {
                    "latest_version_name": None,
                    "latest_version_created": None,
                    "latest_version_workload": None,
                    "latest_version_gvc": None,
                    "latest_version_ready": None,
                    "latest_version_message": None,
                    "latest_version_zone": None,
                }
            )

        # Parse job execution information
        job_executions = deployment_status.get("jobExecutions", [])
        if job_executions:
            latest_job = job_executions[-1]  # Most recent job execution
            status_info.update(
                {
                    "latest_job_workload_version": latest_job.get("workloadVersion"),
                    "latest_job_status": latest_job.get("status"),
                    "latest_job_start_time": latest_job.get("startTime"),
                    "latest_job_completion_time": latest_job.get("completionTime"),
                    "latest_job_name": latest_job.get("name"),
                    "latest_job_replica": latest_job.get("replica"),
                }
            )

            # Parse job conditions for more detailed status
            conditions = latest_job.get("conditions", [])
            if conditions:
                latest_condition = conditions[-1]
                status_info.update(
                    {
                        "latest_job_condition_status": latest_condition.get("status"),
                        "latest_job_condition_type": latest_condition.get("type"),
                        "latest_job_condition_message": latest_condition.get("message"),
                        "latest_job_condition_reason": latest_condition.get("reason"),
                        "latest_job_condition_last_detection_time": latest_condition.get(
                            "lastDetectionTime"
                        ),
                        "latest_job_condition_last_transition_time": latest_condition.get(
                            "lastTransitionTime"
                        ),
                    }
                )

        return status_info

    @classmethod
    def parse_container_status_from_versions(
        cls,
        versions: List[Dict[str, Any]],
        container_name: str,
    ) -> Dict[str, Any]:
        """
        Parse container-specific status from deployment versions.

        Args:
            versions: List of version data from deployment status
            container_name: Name of the container to extract status for

        Returns:
            Dictionary containing container-specific status information
        """
        container_status = {
            "ready": False,
            "total_replicas": 0,
            "ready_replicas": 0,
            "restart_count": 0,
        }

        for version in versions:
            containers = version.get("containers", {})
            if container_name in containers:
                container_info = containers[container_name]

                # Extract container-specific information
                # Note: The actual structure may vary based on the deployment type
                container_status.update(
                    {
                        "version_ready": version.get("ready", False),
                        "version_name": version.get("name"),
                        "version_zone": version.get("zone"),
                        "version_message": version.get("message"),
                    }
                )

                # Container-specific data (structure depends on deployment type)
                if isinstance(container_info, dict):
                    # Extract any additional container metadata if available
                    container_status.update(
                        {
                            "container_data": container_info,
                        }
                    )

                break

        return container_status


class HealthEvaluator:
    """
    Utility class for determining container health status from deployment and status information.
    """

    @classmethod
    def evaluate_health_status(
        cls,
        status_info: Dict[str, Any],
        container_status: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Evaluate the overall health status of a container based on deployment status information.

        Args:
            status_info: Parsed deployment status information
            container_status: Container-specific status information

        Returns:
            Health status: "healthy", "degraded", "unhealthy", or "unknown"
        """
        # Check if deployment is ready
        deployment_ready = status_info.get("ready", False)
        deployment_deploying = status_info.get("deploying", False)

        # Check latest version status
        version_ready = status_info.get("latest_version_ready")

        # Check job execution status if available
        job_status = status_info.get("latest_job_status")

        # Evaluate based on available information
        if deployment_deploying:
            # Currently deploying - status is transitional
            return "degraded"

        if deployment_ready and version_ready:
            # Both deployment and version are ready
            if job_status in ["successful", None]:  # No job or successful job
                return "healthy"
            elif job_status == "active":
                return "degraded"  # Job is running
            elif job_status in ["failed", "invalid", "removed"]:
                return "unhealthy"
            else:
                return "unknown"

        elif deployment_ready and version_ready is None:
            # Deployment ready but no version info - likely healthy but uncertain
            return "degraded" if job_status == "failed" else "healthy"

        elif not deployment_ready:
            # Deployment not ready
            if version_ready is False:
                return "unhealthy"
            else:
                return "degraded"

        # Default to unknown if we can't determine status
        return "unknown"

    @classmethod
    def get_health_summary(
        cls,
        status_info: Dict[str, Any],
        container_status: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get a comprehensive health summary including status and reason.

        Args:
            status_info: Parsed deployment status information
            container_status: Container-specific status information

        Returns:
            Dictionary containing health status and additional context
        """
        health_status = cls.evaluate_health_status(status_info, container_status)

        summary = {
            "health_status": health_status,
            "deployment_ready": status_info.get("ready", False),
            "deployment_deploying": status_info.get("deploying", False),
            "version_ready": status_info.get("latest_version_ready"),
            "job_status": status_info.get("latest_job_status"),
            "status_message": status_info.get("message")
            or status_info.get("latest_version_message"),
        }

        # Add reason for the health status
        if health_status == "healthy":
            summary["reason"] = "Deployment and version are ready"
        elif health_status == "degraded":
            if status_info.get("deploying"):
                summary["reason"] = "Deployment in progress"
            elif status_info.get("latest_job_status") == "active":
                summary["reason"] = "Job execution in progress"
            else:
                summary["reason"] = "Partially ready or transitional state"
        elif health_status == "unhealthy":
            if status_info.get("latest_job_status") in ["failed", "invalid", "removed"]:
                summary[
                    "reason"
                ] = f"Job execution {status_info.get('latest_job_status')}"
            else:
                summary["reason"] = "Deployment or version not ready"
        else:
            summary["reason"] = "Insufficient information to determine health"

        return summary


class MetricsExtractor:
    """
    Utility class for extracting resource utilization metrics from deployment status information.
    """

    @classmethod
    def extract_resource_metrics(
        cls,
        status_info: Dict[str, Any],
        container_status: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Extract CPU and memory utilization metrics from status information.

        Args:
            status_info: Parsed deployment status information
            container_status: Container-specific status information

        Returns:
            Dictionary containing CPU and memory utilization percentages
        """
        metrics = {
            "cpu_usage": None,
            "memory_usage": None,
        }

        # Note: The current deployment_status schema doesn't include detailed resource metrics
        # This is a placeholder for future enhancement when metrics endpoints are integrated
        # or when the deployment status includes resource utilization data

        # For now, we can infer basic resource health based on status
        # In the future, this could integrate with metrics APIs or enhanced status data

        return metrics

    @classmethod
    def calculate_replica_metrics(
        cls,
        status_info: Dict[str, Any],
    ) -> Dict[str, Optional[int]]:
        """
        Calculate replica-related metrics from deployment status.

        Args:
            status_info: Parsed deployment status information

        Returns:
            Dictionary containing replica counts and ratios
        """
        # Extract replica information from versions if available
        # This is a basic implementation - the actual data structure may vary

        return {
            "total_replicas": None,  # Not directly available in current schema
            "ready_replicas": None,  # Not directly available in current schema
            "restart_count": None,  # Not directly available in current schema
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


@dataclass
class AdvancedListingOptions:
    """
    Configuration options for advanced container listing features.
    """

    # Parallel processing
    enable_parallel: bool = True
    max_workers: int = 5

    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes

    # Pagination
    enable_pagination: bool = False
    page_size: int = 50
    max_results: Optional[int] = None

    # Retry logic
    enable_retry: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_backoff_factor: float = 2.0

    # Progress callbacks
    progress_callback: Optional[Callable[[str, int, int], None]] = None

    # Filtering
    filter_unhealthy: bool = False
    include_system_containers: bool = False

    # Statistics
    collect_statistics: bool = True


@dataclass
class ContainerListingStatistics:
    """
    Statistics collected during container listing operations.
    """

    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    total_workloads_processed: int = 0
    successful_workloads: int = 0
    failed_workloads: int = 0

    total_containers_found: int = 0
    healthy_containers: int = 0
    unhealthy_containers: int = 0

    cache_hits: int = 0
    cache_misses: int = 0
    api_calls_made: int = 0

    errors: List[str] = field(default_factory=list)

    def finalize(self) -> None:
        """Mark the statistics collection as complete."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()


@dataclass
class CacheEntry:
    """
    Cache entry for storing container data with TTL.
    """

    data: List[Container]
    timestamp: datetime
    ttl_seconds: int

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl_seconds


class ContainerCache:
    """
    Simple in-memory cache for container data with TTL support.
    """

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[List[Container]]:
        """Get cached data if not expired."""
        with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return entry.data
            elif entry:
                # Remove expired entry
                del self._cache[key]
            return None

    def set(self, key: str, data: List[Container], ttl_seconds: int) -> None:
        """Store data in cache with TTL."""
        with self._lock:
            self._cache[key] = CacheEntry(
                data=data, timestamp=datetime.now(), ttl_seconds=ttl_seconds
            )

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()

    def remove(self, key: str) -> None:
        """Remove specific cache entry."""
        with self._lock:
            self._cache.pop(key, None)

    def get_size(self) -> int:
        """Get number of cached entries."""
        with self._lock:
            # Clean up expired entries first
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(self._cache)


class ContainerCollection(Collection):
    """
    A collection of containers that provides listing and search functionality.

    Since Control Plane API doesn't expose direct container endpoints,
    this collection iterates through workloads and deployments to discover containers.
    """

    model = Container

    def __init__(self, client):
        super().__init__(client)
        self._cache = ContainerCache()

    def list(
        self,
        gvc: str,
        workload_name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Container]:
        """
        List containers for a specific workload (workload-centric approach).

        Args:
            gvc: Name of the GVC
            workload_name: Name of the specific workload
            location: Optional location filter

        Returns:
            List of Container instances for the specified workload

        Raises:
            APIError: If the API request fails
            ValueError: If workload_name is not provided

        Note:
            This method follows the workload-centric design pattern.
            To access containers across multiple workloads, use the
            workload.get_container_objects() method on each workload individually.
        """
        if not workload_name:
            raise ValueError(
                "workload_name is required. Container access should be workload-centric. "
                "Use workload.get_container_objects() to access containers through workloads."
            )

        # Get workloads in the GVC
        workload_config = WorkloadConfig(gvc=gvc, workload_id=workload_name)

        # List containers for the specific workload
        containers = self._get_workload_containers(workload_config, location)
        return containers

    def _get_workload_containers(
        self,
        workload_config: WorkloadConfig,
        location_filter: Optional[str] = None,
    ) -> List[Container]:
        """
        Get containers for a specific workload.

        Args:
            workload_config: Workload configuration
            location_filter: Optional location filter

        Returns:
            List of Container instances
        """
        containers = []

        try:
            # Get workload details to find available locations
            workload_data = self.client.api.get_workload(workload_config)

            # If no location filter, try to get deployments from workload spec
            if location_filter:
                locations = [location_filter]
            else:
                # Try to infer locations from workload data or use common locations
                locations = self._infer_workload_locations(workload_data)

            for location in locations:
                try:
                    # Get deployment data for this location
                    deployment_config = WorkloadConfig(
                        gvc=workload_config.gvc,
                        workload_id=workload_config.workload_id,
                        location=location,
                    )

                    deployment_data = self.client.api.get_workload_deployment(
                        deployment_config
                    )

                    # Parse containers from deployment data
                    deployment_containers = ContainerParser.parse_deployment_containers(
                        deployment_data=deployment_data,
                        workload_name=workload_config.workload_id,
                        gvc_name=workload_config.gvc,
                        location=location,
                    )

                    containers.extend(deployment_containers)

                except APIError:
                    # Re-raise APIError so it can be handled by retry logic
                    raise
                except Exception:
                    # Skip locations where deployment data is not available for other errors
                    continue

        except APIError:
            # Re-raise APIError so it can be handled by retry logic
            raise

        return containers

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

    def get(self, **kwargs) -> Container:
        """
        Get a specific container (not implemented for read-only model).

        Raises:
            NotImplementedError: Containers are read-only in this implementation
        """
        raise NotImplementedError(
            "Container retrieval by ID is not supported. "
            "Use list() method with filters instead."
        )

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

    def list_advanced(
        self,
        gvc: str,
        workload_name: str,
        location: Optional[str] = None,
        options: Optional[AdvancedListingOptions] = None,
    ) -> Tuple[List[Container], ContainerListingStatistics]:
        """
        List containers for a specific workload with advanced features like caching, retry logic, and statistics.

        Args:
            gvc: Name of the GVC
            workload_name: Name of the specific workload
            location: Optional location filter
            options: Advanced listing options

        Returns:
            Tuple of (containers list, statistics)

        Note:
            This method follows the workload-centric design pattern.
            For cross-workload operations, use this method on each workload individually.
        """
        if not workload_name:
            raise ValueError(
                "workload_name is required. Container access should be workload-centric. "
                "Use workload.get_container_objects() to access containers through workloads."
            )

        if options is None:
            options = AdvancedListingOptions()

        stats = ContainerListingStatistics() if options.collect_statistics else None

        # Check cache first
        if options.enable_cache:
            cache_key = self._generate_cache_key(gvc, location, workload_name)
            cached_containers = self._cache.get(cache_key)
            if cached_containers is not None:
                if stats:
                    stats.cache_hits += 1
                    stats.total_containers_found = len(cached_containers)
                    stats.finalize()
                return cached_containers, stats
            elif stats:
                stats.cache_misses += 1

        # Fetch containers for the specific workload
        containers = self._list_containers_sequential(
            gvc, location, workload_name, options, stats
        )

        # Apply filtering
        if options.filter_unhealthy:
            containers = [c for c in containers if c.is_healthy()]

        if not options.include_system_containers:
            containers = [
                c
                for c in containers
                if c.name not in ContainerParser.IGNORED_CONTAINERS
            ]

        # Apply pagination
        if options.enable_pagination:
            containers = self._apply_pagination(containers, options)

        # Update statistics
        if stats:
            stats.total_containers_found = len(containers)
            stats.healthy_containers = sum(1 for c in containers if c.is_healthy())
            stats.unhealthy_containers = (
                stats.total_containers_found - stats.healthy_containers
            )
            stats.finalize()

        # Cache results
        if options.enable_cache:
            cache_key = self._generate_cache_key(gvc, location, workload_name)
            self._cache.set(cache_key, containers, options.cache_ttl_seconds)

        return containers, stats

    def _list_containers_parallel(
        self,
        gvc: str,
        location: Optional[str],
        options: AdvancedListingOptions,
        stats: Optional[ContainerListingStatistics],
    ) -> List[Container]:
        """
        List containers using parallel processing for better performance.
        """
        containers = []

        # Get workloads list first
        workload_config = WorkloadConfig(gvc=gvc)

        try:
            workloads_data = self.client.api.get_workload(workload_config)
            if stats:
                stats.api_calls_made += 1
        except APIError as e:
            if stats:
                stats.errors.append(f"Failed to get workloads: {e}")
            return containers

        workloads = workloads_data.get("items", [])
        total_workloads = len(workloads)

        if stats:
            stats.total_workloads_processed = total_workloads

        # Process workloads in parallel
        with ThreadPoolExecutor(max_workers=options.max_workers) as executor:
            # Submit all workload processing tasks
            future_to_workload = {
                executor.submit(
                    self._get_workload_containers_with_retry,
                    WorkloadConfig(gvc=gvc, workload_id=workload.get("name")),
                    location,
                    options,
                ): workload.get("name")
                for workload in workloads
                if workload.get("name")
            }

            # Collect results as they complete
            completed = 0
            for completed, future in enumerate(as_completed(future_to_workload), 1):
                workload_name = future_to_workload[future]

                # Call progress callback if provided
                if options.progress_callback:
                    options.progress_callback(
                        "Processing workloads", completed, total_workloads
                    )

                try:
                    workload_containers = future.result()
                    containers.extend(workload_containers)
                    if stats:
                        stats.successful_workloads += 1
                except Exception as e:
                    if stats:
                        stats.failed_workloads += 1
                        stats.errors.append(
                            f"Failed to process workload {workload_name}: {e}"
                        )

        return containers

    def _list_containers_sequential(
        self,
        gvc: str,
        location: Optional[str],
        workload_name: Optional[str],
        options: AdvancedListingOptions,
        stats: Optional[ContainerListingStatistics],
    ) -> List[Container]:
        """
        List containers using sequential processing.
        """
        containers = []
        workload_config = WorkloadConfig(gvc=gvc)

        if workload_name:
            # Process single workload
            workload_config.workload_id = workload_name

            # Call progress callback if provided
            if options.progress_callback:
                options.progress_callback("Processing workloads", 1, 1)

            workload_containers = self._get_workload_containers_with_retry(
                workload_config, location, options
            )
            containers.extend(workload_containers)

            if stats:
                stats.total_workloads_processed = 1
                stats.successful_workloads = 1 if workload_containers else 0
                stats.failed_workloads = 0 if workload_containers else 1
        else:
            # Process all workloads
            try:
                workloads_data = self.client.api.get_workload(workload_config)
                if stats:
                    stats.api_calls_made += 1
            except APIError as e:
                if stats:
                    stats.errors.append(f"Failed to get workloads: {e}")
                return containers

            workloads = workloads_data.get("items", [])
            total_workloads = len(workloads)

            if stats:
                stats.total_workloads_processed = total_workloads

            for idx, workload in enumerate(workloads):
                workload_name = workload.get("name")
                if not workload_name:
                    continue

                # Call progress callback if provided
                if options.progress_callback:
                    options.progress_callback(
                        "Processing workloads", idx + 1, total_workloads
                    )

                workload_config.workload_id = workload_name

                try:
                    workload_containers = self._get_workload_containers_with_retry(
                        workload_config, location, options
                    )
                    containers.extend(workload_containers)
                    if stats:
                        stats.successful_workloads += 1
                except Exception as e:
                    if stats:
                        stats.failed_workloads += 1
                        stats.errors.append(
                            f"Failed to process workload {workload_name}: {e}"
                        )

        return containers

    def _get_workload_containers_with_retry(
        self,
        workload_config: WorkloadConfig,
        location_filter: Optional[str],
        options: AdvancedListingOptions,
    ) -> List[Container]:
        """
        Get containers for a workload with retry logic.
        """
        if not options.enable_retry:
            return self._get_workload_containers(workload_config, location_filter)

        retry_count = 0
        delay = options.retry_delay_seconds

        while retry_count <= options.max_retries:
            try:
                return self._get_workload_containers(workload_config, location_filter)
            except APIError as e:
                retry_count += 1

                if retry_count > options.max_retries:
                    raise e

                # Check if this is a rate limiting error that should be retried
                if "rate limit" in str(e).lower() or "429" in str(e):
                    time.sleep(delay)
                    delay *= options.retry_backoff_factor
                else:
                    # For other errors, don't retry
                    raise e

        return []

    def _apply_pagination(
        self, containers: List[Container], options: AdvancedListingOptions
    ) -> List[Container]:
        """
        Apply pagination to container results.
        """
        if options.max_results:
            containers = containers[: options.max_results]

        return containers

    def _generate_cache_key(
        self, gvc: str, location: Optional[str], workload_name: Optional[str]
    ) -> str:
        """
        Generate a cache key for the given parameters.
        """
        parts = [gvc]
        if location:
            parts.append(f"loc:{location}")
        if workload_name:
            parts.append(f"wl:{workload_name}")
        return "|".join(parts)

    def clear_cache(self) -> None:
        """
        Clear all cached container data.
        """
        self._cache.clear()

    def get_cache_size(self) -> int:
        """
        Get the number of cached entries.

        Returns:
            Number of cached entries
        """
        return self._cache.get_size()

    def count_containers(
        self,
        gvc: str,
        workload_name: str,
        location: Optional[str] = None,
        options: Optional[AdvancedListingOptions] = None,
    ) -> int:
        """
        Count containers for a specific workload without returning the full list.

        Args:
            gvc: Name of the GVC
            workload_name: Name of the specific workload
            location: Optional location filter
            options: Advanced listing options

        Returns:
            Number of containers in the specified workload

        Note:
            This method follows the workload-centric design pattern.
        """
        containers, _ = self.list_advanced(gvc, workload_name, location, options)
        return len(containers)

    def refresh_all_status(
        self,
        containers: List[Container],
        options: Optional[AdvancedListingOptions] = None,
    ) -> Tuple[int, int]:
        """
        Refresh status for all containers in the provided list.

        Args:
            containers: List of containers to refresh status for
            options: Advanced listing options for parallel processing

        Returns:
            Tuple of (successful_refreshes, failed_refreshes)
        """
        if options is None:
            options = AdvancedListingOptions()

        successful = 0
        failed = 0

        if options.enable_parallel and len(containers) > 1:
            # Use parallel processing for better performance
            with ThreadPoolExecutor(max_workers=options.max_workers) as executor:
                future_to_container = {
                    executor.submit(container.refresh_status, self.client): container
                    for container in containers
                }

                for future in as_completed(future_to_container):
                    try:
                        result = future.result()
                        if result:
                            successful += 1
                        else:
                            failed += 1
                    except Exception:
                        failed += 1
        else:
            # Sequential processing
            for i, container in enumerate(containers):
                # Call progress callback if provided
                if options.progress_callback:
                    options.progress_callback(
                        "Refreshing container status", i + 1, len(containers)
                    )

                try:
                    result = container.refresh_status(self.client)
                    if result:
                        successful += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

        return successful, failed

    def get_containers_with_status(
        self,
        gvc: str,
        workload_name: str,
        location: Optional[str] = None,
        refresh_status: bool = True,
        options: Optional[AdvancedListingOptions] = None,
    ) -> Tuple[List[Container], ContainerListingStatistics]:
        """
        Get containers for a workload with real-time status information.

        This is a convenience method that combines container listing with status refresh.

        Args:
            gvc: Name of the GVC
            workload_name: Name of the specific workload
            location: Optional location filter
            refresh_status: Whether to refresh status from API
            options: Advanced listing options

        Returns:
            Tuple of (containers list with refreshed status, statistics)
        """
        # Get containers using advanced listing
        containers, stats = self.list_advanced(gvc, workload_name, location, options)

        # Refresh status if requested
        if refresh_status and containers:
            successful, failed = self.refresh_all_status(containers, options)

            # Update statistics with status refresh info
            if stats:
                stats.api_calls_made += len(
                    containers
                )  # Estimate API calls for status refresh

        return containers, stats
