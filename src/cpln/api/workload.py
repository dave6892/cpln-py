from typing import (
    Any,
    cast,
)

from ..config import WorkloadConfig
from ..parsers.deployment import Deployment

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
        if config.workload_id is None:
            raise ValueError("Config not set properly")

        endpoint = f"gvc/{config.gvc}/workload/{config.workload_id}/deployment"

        print(f"Debug: config = {config}")
        print(f"Debug: client = {self.__dict__}")

        if config.location:
            endpoint += f"/{config.location}"

        print(f"Debug: endpoint = {endpoint}")

        # Type cast to indicate parent class has _get method
        deployment_data_raw = cast(Any, self)._get(endpoint)

        deployment_data = deployment_data_raw.get("items", None)
        if deployment_data:
            return {
                deployment["name"]: Deployment.parse(
                    deployment,
                    api_client=cast(Any, self),
                    config=config,
                )
                for deployment in deployment_data
            }
        return Deployment.parse(
            deployment_data_raw,
            api_client=cast(Any, self),
            config=config,
        )


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
        return cast(Any, self)._get(endpoint)

    def create_workload(
        self,
        config: WorkloadConfig,
        metadata: dict[str, Any],
    ):
        """
        Creates a new workload in the specified GVC.

        Args:
            config (WorkloadConfig): Configuration object containing workload details
            metadata (dict[str, Any]): The workload metadata including spec and configuration

        Returns:
            requests.Response: The response from the API

        Raises:
            APIError: If the request fails
        """
        endpoint = f"gvc/{config.gvc}/workload"
        return cast(Any, self)._post(endpoint, data=metadata)

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
        return cast(Any, self)._delete(endpoint)

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
        return cast(Any, self)._patch(endpoint, data=data)
