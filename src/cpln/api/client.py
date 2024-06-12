from .config import APIConfig
from ..utils.requests import make_request


class APIClient:
    def __init__(self,
        config: APIConfig | None = None,
        **kwargs
    ):
        if config is None:
            config = APIConfig(**kwargs)

        self.config = config

    def request(self):
        return make_request(
            "gvc",
            token = self.config.token,
            base_url=self.config.org_url,
            request_method="GET",
        )