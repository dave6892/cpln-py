import json
from typing import Optional
from .resource import (
    Collection,
    Model
)
from ..api import APIClient
from ..config import WorkloadConfig
from ..errors import WebSocketExitCodeError
from ..utils import (
    get_default_workload_template,
    load_template
)


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

    def clone(self,
        name: str,
        gvc: str | None = None,
        workload_type: str | None = None,
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
            metadata['spec']['type'] = workload_type
            
            # Ensure defaultOptions exists
            if 'defaultOptions' not in metadata['spec']:
                metadata['spec']['defaultOptions'] = {}
                
            # Ensure autoscaling exists
            if 'autoscaling' not in metadata['spec']['defaultOptions']:
                metadata['spec']['defaultOptions']['autoscaling'] = {}
                
            # Set autoscaling metric and capacityAI
            metadata['spec']['defaultOptions']['autoscaling']['metric'] = "cpu"
            metadata['spec']['defaultOptions']['capacityAI'] = False

        response = self.client.api.create_workload(
            config=self.config(gvc=gvc),
            metadata=metadata,
        )
        if response.status_code // 100 == 2:
            print(response.status_code, response.text)
        else:
            print(response.status_code, response.json())
            raise

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
                config=self.config(location=location),
                command=command
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
            response = self.exec(
                ["echo", "ping"],
                location=location,
            )
            return {
                "status": 200,
                "message": "Successfully pinged workload",
                "exit_code": 0
            }
        except WebSocketExitCodeError as e:
            return {
                "status": 500,
                "message": f"Command failed with exit code: {e}",
                "exit_code": e.exit_code
            }
        except Exception as e:
            return {
                "status": 500,
                "message": str(e),
                "exit_code": -1
            }

    def export(self) -> dict[str, any]:
        """
        Export the workload.
        """
        self.get()
        return {
            "name": self.attrs["name"],
            "gvc": self.state["gvc"],
            "spec": self.attrs["spec"]
        }

    def config(self, location: Optional[str] = None, gvc: Optional[str] = None) -> WorkloadConfig:
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

    def _change_suspend_state(self,
        state: bool = True
    ) -> None:
        output = self.client.api.patch_workload(
            config=self.config(),
            data={
                "spec": {
                    "defaultOptions": {
                        "suspend": str(state).lower()
                    }
                }
            }
        )
        print(f"{'' if state else 'Un'}Suspending Workload: {self}")
        return output


class WorkloadCollection(Collection):
    """
    Workloads on the server.
    """
    model = Workload

    def create(self,
        name: str,
        gvc: str | None = None,
        config: WorkloadConfig | None = None,
        description: str | None = None,
        image: str | None = None,
        container_name: str | None = None,
        workload_type: str | None = None,
        metadata_file_path: str | None = None,
        metadata: dict | None = None,
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

                metadata = get_default_workload_template("serverless" if workload_type is None else workload_type)
                metadata['name'] = name
                metadata['description'] = description if description is not None else ""
                metadata['spec']['containers'][0]['image'] = image
                metadata['spec']['containers'][0]['name'] = container_name

            else:
                metadata = load_template(metadata_file_path)
        else:
            metadata['name'] = name
            if workload_type is not None:
                metadata['spec']['type'] = workload_type
                metadata['spec']['defaultOptions']['autoscaling']['metric'] = "cpu"
                metadata['spec']['defaultOptions']['capacityAI'] = False

        response = self.client.api.create_workload(config, metadata)
        if response.status_code // 100 == 2:
            print(response.status_code, response.text)
        else:
            print(response.status_code, response.json())
            raise

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
