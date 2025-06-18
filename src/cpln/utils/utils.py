import json
import os
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from inflection import underscore

from ..constants import DEFAULT_CPLN_API_URL

load_dotenv()


def kwargs_from_env(environment=None):
    if not environment:
        environment = os.environ

    base_url = DEFAULT_CPLN_API_URL
    token = environment.get("CPLN_TOKEN")
    org = environment.get("CPLN_ORG")

    params = {}
    if base_url:
        params["base_url"] = base_url

    if token:
        params["token"] = token
    else:
        raise ValueError("CPLN_TOKEN is not set")

    if org:
        params["org"] = org
    else:
        raise ValueError("CPLN_ORG is not set")

    return params


def load_template(template_path: str) -> dict[str, Any]:
    with open(template_path) as file:
        return json.load(file)


def get_default_workload_template(workload_type: str) -> dict[str, Any]:
    if workload_type == "serverless":
        template_path = "../templates/default-serverless-workload.json"
    elif workload_type == "standard":
        template_path = "../templates/default-standard-workload.json"
    else:
        raise ValueError(f"Invalid workload type: {workload_type}")
    spec = load_template(os.path.join(os.path.dirname(__file__), template_path))
    return spec


def convert_dictionary_keys(
    data: dict[str, Any],
    format_func: Callable[[str], str] = underscore,
    key_map: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    result = {}
    key_map = key_map or {}
    for key, value in data.items():
        new_key = key_map.get(key, format_func(key))
        if isinstance(value, dict):
            result[new_key] = convert_dictionary_keys(value, format_func, key_map)
        elif isinstance(value, list):
            result[new_key] = [
                convert_dictionary_keys(item, format_func, key_map)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            result[new_key] = value
    return result
