from dataclasses import dataclass
from typing import Any

from .base import BaseParser, preparse


@dataclass
class ContainerPort(BaseParser):
    number: int
    protocol: str


@dataclass
class Container(BaseParser):
    cpu: str
    name: str
    image: str
    ports: list[ContainerPort]
    memory: int
    inherit_env: bool

    @classmethod
    @preparse
    def parse(cls, data: dict[str, Any]) -> Any:
        ports = data.pop("ports")
        return cls(
            **cls.format_key_of_dict(data),
            ports=[ContainerPort.parse(port) for port in ports],
        )
