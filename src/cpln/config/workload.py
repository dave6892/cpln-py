from dataclasses import dataclass
from typing import TypedDict


class JSON(TypedDict):
    pass


@dataclass
class WorkloadConfig:
    gvc: str
    workload_id: str
    location: str
    specs: JSON
