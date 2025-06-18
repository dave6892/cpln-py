from dataclasses import dataclass
from typing import Any, Optional

from .base import BaseParser, preparse
from .container import Container


@dataclass
class LoadBalancer(BaseParser):
    direct: dict[str, Any]
    replica_direct: bool


@dataclass
class FirewallConfig(BaseParser):
    external: dict[str, Any]
    internal: dict[str, Any]


@dataclass
class Autoscaling(BaseParser):
    metric: str
    target: int
    max_scale: int
    min_scale: int
    max_concurrency: int
    scale_to_zero_delay: int


@dataclass
class MultiZone(BaseParser):
    enabled: bool


@dataclass
class DefaultOptions(BaseParser):
    debug: bool
    suspend: bool
    multi_zone: MultiZone
    capacity_ai: bool
    autoscaling: Autoscaling
    timeout_seconds: int


@dataclass
class Spec(BaseParser):
    type: str
    containers: list[Container]
    identity_link: Optional[str] = None
    load_balancer: Optional[LoadBalancer] = None
    default_options: Optional[DefaultOptions] = None
    firewall_config: Optional[FirewallConfig] = None
    support_dynamic_tags: Optional[bool] = None

    @classmethod
    @preparse
    def parse(cls, data: dict[str, Any]) -> Any:
        containers = data.pop("containers", [])
        load_balancer = data.pop("loadBalancer", None)
        default_options = data.pop("defaultOptions", None)
        firewall_config = data.pop("firewallConfig", None)

        parsed_data = cls.format_key_of_dict(data)

        return cls(
            **parsed_data,
            containers=[Container.parse(container) for container in containers],
            load_balancer=LoadBalancer.parse(load_balancer) if load_balancer else None,
            default_options=DefaultOptions.parse(default_options)
            if default_options
            else None,
            firewall_config=FirewallConfig.parse(firewall_config)
            if firewall_config
            else None,
        )
