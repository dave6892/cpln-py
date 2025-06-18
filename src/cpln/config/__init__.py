from dataclasses import dataclass
from typing import (
    Optional,
)


@dataclass
class WorkloadConfig:
    gvc: str
    workload_id: Optional[str] = None
    location: Optional[str] = None
    remote_wss: Optional[str] = None
    container: Optional[str] = None
    replica: Optional[str] = None
