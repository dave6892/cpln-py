from dataclasses import dataclass

@dataclass
class APIConfig:
    base_url: str
    token: str
    org: str
    org_url: str = None

    def __post_init__(self):
        self.org_url = self.get_org_url()

    def get_org_url(self) -> str:
        return f"{self.base_url}/org/{self.org}"
