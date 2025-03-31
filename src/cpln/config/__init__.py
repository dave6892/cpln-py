from dataclasses import dataclass
from typing import (
    Optional,
)


@dataclass
class WorkloadConfig:
    gvc: str
    workload_id: Optional[str] = None
    location: Optional[str] = None
