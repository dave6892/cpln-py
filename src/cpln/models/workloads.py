import random
from typing import Optional

import inflection

from ..config import WorkloadConfig
from ..errors import WebSocketExitCodeError
from ..parsers.container import Container
from ..parsers.deployment import Deployment
from ..parsers.spec import Spec
from ..utils import get_default_workload_template, load_template
from .resource import Collection, Model


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

    def get_spec(self) -> Spec:
        return Spec.parse(self.attrs["spec"])

    def get_deployment(self, location: Optional[str] = None) -> Deployment:
        return self.client.api.get_workload_deployment(self.config(location=location))

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
            config=self.config(gvc=metadata["gvc"]),
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

    def exec(
        self,
        command: str,
        location: str,
        container: Optional[str] = None,
        replica_selector: Optional[int] = None,
    ):
        """
        Execute a command on the workload.

        Args:
            command (str): The command to execute.
            location (str): The location of the workload.
            container (str): The container to execute the command on.

        Returns:
            (dict): The response from the server.

        Raises:
            :py:class:`cpln.errors.WebSocketExitCodeError`
                If the command returns a non-zero exit code.
        """
        deployment = self.get_deployment(location=location)
        replicas = deployment.get_replicas()
        if len(replicas) == 0:
            raise ValueError(f"No replicas found in workload {self.attrs['name']}")

        replica = replicas.get(container, [])
        if len(replica) == 0:
            raise ValueError(
                f"Container {container} not found in workload {self.attrs['name']}"
            )

        # Choose a number between 0 and len(replica) - 1 randomly if replica_selector is None
        index = (
            replica_selector
            if replica_selector is not None
            else random.randint(0, len(replica) - 1)
        )
        return replica[index].exec(command)

    def ping(
        self,
        location: Optional[str] = None,
        container: Optional[str] = None,
        replica_selector: Optional[int] = None,
    ) -> dict[str, any]:
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
                container=container,
                replica_selector=replica_selector,
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
        from ..utils.utils import convert_dictionary_keys

        return {
            "name": self.name,
            "gvc": self.state["gvc"],
            "spec": convert_dictionary_keys(
                self.get_spec().to_dict(),
                lambda x: inflection.camelize(x, False),
                key_map={
                    "capacity_ai": "capacityAI",
                },
            ),
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

    def get_replicas(self, location: Optional[str] = None) -> list[str]:
        """
        Get the replicas of the workload.

        Args:
            location (str): The location of the workload.
                Default: None

        Returns:
            (list): The replicas of the workload.
        """
        return self.get_deployment(location=location).get_replicas()

    def get_containers(self):
        """
        Get containers for this workload with full Container objects.

        Args:
            location: Optional location filter

        Returns:
            List of Container instances with full metadata
        """
        return self.get_spec().containers

    def get_container(self, container_name: str) -> Optional["Container"]:
        """
        Get a specific container by name within this workload.

        Args:
            container_name: Name of the container to find

        Returns:
            Container instance if found, None otherwise
        """
        containers = self.get_containers()
        return next(filter(lambda c: c.name == container_name, containers), None)

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
