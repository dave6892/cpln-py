from typing import TYPE_CHECKING, Optional

from ..config import WorkloadConfig
from ..errors import WebSocketExitCodeError
from ..utils import get_default_workload_template, load_template
from .resource import Collection, Model
from .workload_specs import WorkloadSpecState

if TYPE_CHECKING:
    from .containers import Container


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
        return self.client.api.get_workload(self.config())

    def get_spec_state(self) -> WorkloadSpecState:
        self.get()
        return WorkloadSpecState.parse_from_spec(self.spec)

    def delete(self) -> None:
        """
        Delete the workload.

        Raises:
            :py:class:`cpln.errors.APIError`
                If the server returns an error.
        """
        print(f"Deleting Workload: {self}")
        self.client.api.delete_workload(self.config())
        print("Deleted!")

    def clone(
        self,
        name: str,
        gvc: Optional[str] = None,
        workload_type: Optional[str] = None,
    ) -> None:
        """
        Clone the workload.

        Args:
            name (str): The name of the new workload.
            gvc (str, optional): The GVC to create the workload in. Defaults to None.
            workload_type (str, optional): The type of workload to create. Defaults to None.

        Returns:
            None

        Raises:
            Exception: If the API returns a non-2xx status code.
        """
        metadata = self.export()

        # TODO: I need to get identity link from the REST API, in order
        # to change it in the metadata. The path to the identity link is
        # different for different GVCs.

        # TODO: The parameters to the created/cloned workloads are too limited.
        # In order for this package to be more widely used, we need to implement
        # a way to pass more workload configuration parameters.
        metadata["name"] = name
        if gvc is not None:
            metadata["gvc"] = gvc

        if workload_type is not None:
            metadata["spec"]["type"] = workload_type

            # Ensure defaultOptions exists
            if "defaultOptions" not in metadata["spec"]:
                metadata["spec"]["defaultOptions"] = {}

            # Ensure autoscaling exists
            if "autoscaling" not in metadata["spec"]["defaultOptions"]:
                metadata["spec"]["defaultOptions"]["autoscaling"] = {}

            # Set autoscaling metric and capacityAI
            metadata["spec"]["defaultOptions"]["autoscaling"]["metric"] = "cpu"
            metadata["spec"]["defaultOptions"]["capacityAI"] = False

        response = self.client.api.create_workload(
            config=self.config(gvc=gvc),
            metadata=metadata,
        )
        if response.status_code // 100 == 2:
            print(response.status_code, response.text)
        else:
            print(response.status_code, response.json())
            raise RuntimeError(f"API call failed with status {response.status_code}")

    def suspend(self) -> None:
        self._change_suspend_state(state=True)

    def unsuspend(self) -> None:
        self._change_suspend_state(state=False)

    def exec(self, command: str, location: str):
        """
        Execute a command on the workload.

        Args:
            command (str): The command to execute.

        Returns:
            (dict): The response from the server.

        Raises:
            :py:class:`cpln.errors.WebSocketExitCodeError`
                If the command returns a non-zero exit code.
        """
        try:
            return self.client.api.exec_workload(
                config=self.config(location=location), command=command
            )
        except WebSocketExitCodeError as e:
            print(f"Command failed with exit code: {e}")
            raise

    def ping(self, location: Optional[str] = None) -> dict[str, any]:
        """
        Ping the workload.

        Args:
            location (str): The location of the workload.
                Default: None
        Returns:
            (dict): The response from the server containing status, message, and exit code.
        """
        try:
            self.exec(
                ["echo", "ping"],
                location=location,
            )
            return {
                "status": 200,
                "message": "Successfully pinged workload",
                "exit_code": 0,
            }
        except WebSocketExitCodeError as e:
            return {
                "status": 500,
                "message": f"Command failed with exit code: {e}",
                "exit_code": e.exit_code,
            }
        except Exception as e:
            return {"status": 500, "message": str(e), "exit_code": -1}

    def export(self) -> dict[str, any]:
        """
        Export the workload.
        """
        self.get()
        return {
            "name": self.attrs["name"],
            "gvc": self.state["gvc"],
            "spec": self.attrs["spec"],
        }

    def config(
        self, location: Optional[str] = None, gvc: Optional[str] = None
    ) -> WorkloadConfig:
        """
        Get the workload config.

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (WorkloadConfig): The workload config.
        """
        return WorkloadConfig(
            gvc=self.state["gvc"] if gvc is None else gvc,
            workload_id=self.attrs["name"],
            location=location,
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
        Get the containers of the workload (legacy method returning container names).

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (list): The container names of the workload.

        Note:
            This method is deprecated. Use get_container_objects() for full Container instances.
        """
        return self.client.api.get_containers(self.config(location=location))

    def get_container_objects(self, location: Optional[str] = None):
        """
        Get containers for this workload with full Container objects.

        Args:
            location: Optional location filter

        Returns:
            List of Container instances with full metadata
        """
        from .containers import ContainerParser  # Import here to avoid circular imports

        # Get all locations for this workload
        locations = [location] if location else self._get_workload_locations()

        containers = []
        for loc in locations:
            try:
                deployment_data = self.client.api.get_workload_deployment(
                    self.config(location=loc)
                )

                workload_containers = ContainerParser.parse_deployment_containers(
                    deployment_data=deployment_data,
                    workload_name=self.attrs["name"],
                    gvc_name=self.state["gvc"],
                    location=loc,
                )
                containers.extend(workload_containers)

            except Exception:
                # Skip locations where deployment data is unavailable
                continue

        return containers

    def get_container(
        self, container_name: str, location: Optional[str] = None
    ) -> Optional["Container"]:
        """
        Get a specific container by name within this workload.

        Args:
            container_name: Name of the container to find
            location: Optional location filter

        Returns:
            Container instance if found, None otherwise
        """
        containers = self.get_container_objects(location=location)
        for container in containers:
            if container.name == container_name:
                return container
        return None

    def _get_workload_locations(self) -> list[str]:
        """
        Get available locations for this workload.

        Returns:
            List of location names where this workload is deployed
        """
        # Try to extract locations from workload spec
        locations = []

        try:
            # Check if locations are specified in workload spec
            spec = self.attrs.get("spec", {})
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

        except (KeyError, TypeError):
            # Fallback to common locations if spec parsing fails
            locations = [
                "aws-us-east-1",
                "aws-us-west-2",
                "aws-eu-west-1",
                "gcp-us-central1",
                "azure-eastus",
            ]

        return locations

    def _change_suspend_state(self, state: bool = True) -> None:
        output = self.client.api.patch_workload(
            config=self.config(),
            data={"spec": {"defaultOptions": {"suspend": str(state).lower()}}},
        )
        print(f"{'' if state else 'Un'}Suspending Workload: {self}")
        return output


class WorkloadCollection(Collection):
    """
    Workloads on the server.
    """

    model = Workload

    def create(
        self,
        name: str,
        gvc: Optional[str] = None,
        config: Optional[WorkloadConfig] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        container_name: Optional[str] = None,
        workload_type: Optional[str] = None,
        metadata_file_path: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Create the workload.
        """
        if gvc is None and config is None:
            raise ValueError("Either GVC or WorkloadConfig must be defined.")
        config = WorkloadConfig(gvc=gvc) if gvc else config

        if metadata is None:
            if metadata_file_path is None:
                if not image:
                    raise ValueError("Image is required.")
                if not container_name:
                    raise ValueError("Container name is required.")

                metadata = get_default_workload_template(
                    "serverless" if workload_type is None else workload_type
                )
                metadata["name"] = name
                metadata["description"] = description if description is not None else ""
                metadata["spec"]["containers"][0]["image"] = image
                metadata["spec"]["containers"][0]["name"] = container_name

            else:
                metadata = load_template(metadata_file_path)
        else:
            metadata["name"] = name
            if workload_type is not None:
                metadata["spec"]["type"] = workload_type
                metadata["spec"]["defaultOptions"]["autoscaling"]["metric"] = "cpu"
                metadata["spec"]["defaultOptions"]["capacityAI"] = False

        response = self.client.api.create_workload(config, metadata)
        if response.status_code // 100 == 2:
            print(response.status_code, response.text)
        else:
            print(response.status_code, response.json())
            raise RuntimeError(f"API call failed with status {response.status_code}")

    def get(self, config: WorkloadConfig):
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
            self.client.api.get_workload(config=config), state={"gvc": config.gvc}
        )

    def list(
        self, gvc: Optional[str] = None, config: Optional[WorkloadConfig] = None
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
        return [
            self.get(
                config=WorkloadConfig(gvc=config.gvc, workload_id=workload["name"])
            )
            for workload in resp
        ]
