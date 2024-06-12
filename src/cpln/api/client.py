from .config import APIConfig
import requests


class APIClient(requests.Session):
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
        return self.get(
            f"{self.config.org_url}/{endpoint}",
            headers = self._headers
        )

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.config.token}"
        }