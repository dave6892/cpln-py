from dataclasses import dataclass
from typing import Any


@dataclass
class ContainerSpec:
    name: str
    cpu: int
    env: list[dict[str, Any]]
    image: str
    inheritEnv: bool
    memory: int
    ports: list[int]


@dataclass
class AutoscalingSpec:
    maxConcurrency: int
    maxScale: int
    metric: str
    minScale: int
    scaleToZeroDelay: int
    target: int


@dataclass
class DefaultOptionsSpec:
    autoscaling: AutoscalingSpec
    capacityAI: bool
    debug: bool
    suspend: bool
    timeoutSeconds: int


@dataclass
class FirewallExternalSpec:
    inboundAllowCIDR: list[str]
    inboundBlockedCIDR: list[str]
    outboundAllowCIDR: list[str]
    outboundAllowHostname: list[str]
    outboundAllowPort: list[int]
    outboundBlockedCIDR: list[str]


@dataclass
class FirewallInternalSpec:
    inboundAllowType: str
    inboundAllowWorkload: list[str]


@dataclass
class FirewallConfigSpec:
    external: FirewallExternalSpec
    internal: FirewallInternalSpec


@dataclass
class IdentityLinkSpec:
    path: str


@dataclass
class LoadBalancerSpec:
    direct: bool
    replicaDirect: bool = False


@dataclass
class WorkloadSpec:
    type: str
    containers: ContainerSpec
    defaultOptions: DefaultOptionsSpec
    firewallConfig: FirewallConfigSpec
    identityLink: IdentityLinkSpec
    loadBalancer: LoadBalancerSpec


@dataclass
class WorkloadStatus:
    canonicalEndpoint: str
    endpoint: str
    internalName: str
    loadBalancer: list[str]
    parentId: str
    ready: bool
    readyCheckTimestamp: str
    readyLatest: bool


@dataclass
class WorkloadStatus:
    canonicalEndpoint: str
    endpoint: str
    internalName: str
    loadBalancer: list[str]
    parentId: str
    ready: bool
    readyCheckTimestamp: str
    readyLatest: bool