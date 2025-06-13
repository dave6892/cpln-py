from dataclasses import dataclass

from inflection import underscore


@dataclass
class WorkloadAutoscaling:
    metric: str
    target: int
    max_scale: int
    min_scale: int
    max_concurrency: int
    scale_to_zero_delay: int


@dataclass
class WorkloadSpecState:
    debug: bool
    autoscaling: WorkloadAutoscaling
    capacity_ai: bool
    suspend: bool
    timeout_seconds: int

    @classmethod
    def parse_from_spec(cls, spec: dict) -> "WorkloadSpecState":
        autoscaling = {
            underscore(label): value
            for label, value in spec["defaultOptions"]["autoscaling"].items()
        }
        return cls(
            debug=spec["defaultOptions"]["debug"],
            autoscaling=WorkloadAutoscaling(**autoscaling),
            capacity_ai=spec["defaultOptions"]["capacityAI"],
            suspend=spec["defaultOptions"]["suspend"],
            timeout_seconds=spec["defaultOptions"]["timeoutSeconds"],
        )
