from .config import APIConfig
from .gvc import GVCApiMixin
from .image import ImageApiMixin
from .workload import (
    WorkloadApiMixin,
    WorkloadDeploymentMixin,
)
import requests


class APIClient(
    requests.Session,
    GVCApiMixin,
    ImageApiMixin,
    WorkloadApiMixin,
    WorkloadDeploymentMixin,
):
    def __init__(self,
        config: APIConfig | None = None,
        **kwargs
    ):
        super().__init__()
        if config is None:
            config = APIConfig(**kwargs)

        self.config = config

    def _get(self,
        endpoint: str
    ):
        resp = self.get(
            f"{self.config.org_url}/{endpoint}",
            headers = self._headers
        )
        return resp.json()

    def _delete(self,
        endpoint: str
    ):
        return self.delete(
            f"{self.config.org_url}/{endpoint}",
            headers = self._headers
        )

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.config.token}"
        }
