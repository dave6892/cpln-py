from dataclasses import (
    dataclass,
    asdict
)
from ..constants import (
    DEFAULT_CPLN_API_VERSION,
    DEFAULT_TIMEOUT_SECONDS
)

@dataclass
class APIConfig:
    base_url: str
    token: str
    org: str
    version: str = DEFAULT_CPLN_API_VERSION
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    org_url: str = None

    def __post_init__(self):
        self.org_url = self.get_org_url()

    def get_org_url(self) -> str:
        return f"{self.base_url}/org/{self.org}"

    def asdict(self):
        return asdict(self)