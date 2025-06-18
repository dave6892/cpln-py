from dataclasses import dataclass
from typing import Optional, TypedDict


class JSON(TypedDict):
    """
    Type alias for JSON data structures.
    """

    pass


@dataclass
class WorkloadConfig:
    """
    Configuration object for workload operations.

    This class encapsulates the configuration parameters needed to identify
    and operate on a specific workload within a GVC.

    Attributes:
        gvc (str): The Global Virtual Cluster name
        workload_id (str): The unique identifier of the workload
        location (Optional[str]): The location/region of the workload deployment
        specs (Optional[JSON]): Optional specification data for the workload
    """

    gvc: str
    workload_id: str
    location: Optional[str] = None
    specs: Optional[JSON] = None
