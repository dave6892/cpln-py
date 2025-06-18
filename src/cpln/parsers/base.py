from dataclasses import asdict, dataclass
from functools import wraps
from typing import Any, Callable, TypeVar, Union, get_args, get_origin

from inflection import underscore

T = TypeVar("T")


def preparse(func: Callable) -> Callable:
    """
    Decorator for pre-processing data before parsing.

    Args:
        func: The pre-processing function to apply

    Returns:
        Decorated function that applies pre-processing
    """

    @wraps(func)
    def wrapper(cls_or_self, data: dict[str, Any], *args, **kwargs) -> Any:
        return func(cls_or_self, data.copy(), *args, **kwargs)

    return wrapper


@dataclass
class BaseParser:
    @classmethod
    def parse(cls, data: dict[str, Any]) -> Any:
        return cls(**cls.format_key_of_dict(data))

    @classmethod
    def format_key_of_dict(
        cls, data: dict[str, Any], format_func: Callable[[str], str] = underscore
    ) -> dict[str, Any]:
        return {format_func(key): value for key, value in data.items()}

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, BaseParser):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    item.to_dict() if isinstance(item, BaseParser) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def pop_optional_fields(self, data: dict):
        for key, annotation in self.__annotations__.items():
            # Check if the annotation is Optional
            if get_origin(annotation) is Union and type(None) in get_args(annotation):
                data.pop(key, None)
