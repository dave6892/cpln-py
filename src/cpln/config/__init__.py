"""Configuration classes for CPLN operations.

This module provides configuration classes used throughout the CPLN SDK
for specifying operation parameters and resource identifiers.
"""

from dataclasses import dataclass
from typing import (
    Optional,
)


@dataclass
class WorkloadConfig:
    """
    Configuration for workload operations.

    Attributes:
        gvc (str): Global Virtual Cluster name
        workload_id (Optional[str]): Workload identifier
        location (Optional[str]): Deployment location
        remote_wss (Optional[str]): Remote WebSocket URL
        container (Optional[str]): Container name
        replica (Optional[str]): Replica identifier
    """

    gvc: str
    workload_id: Optional[str] = None
    location: Optional[str] = None
    remote_wss: Optional[str] = None
    container: Optional[str] = None
    replica: Optional[str] = None
