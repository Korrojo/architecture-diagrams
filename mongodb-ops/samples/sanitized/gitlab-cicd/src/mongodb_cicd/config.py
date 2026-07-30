"""Load and validate environment-specific deployment configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ALLOWED_ENVIRONMENTS = frozenset({"dev", "sat", "prod"})
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigurationError(ValueError):
    """Raised when deployment configuration is missing or unsafe."""


def resolve_environment(cli_value: str | None = None) -> str:
    """Resolve and validate the requested deployment environment."""
    value = (cli_value or os.getenv("DEPLOY_ENV", "")).strip().lower()
    if value not in ALLOWED_ENVIRONMENTS:
        allowed = ", ".join(sorted(ALLOWED_ENVIRONMENTS))
        raise ConfigurationError(f"DEPLOY_ENV must be one of: {allowed}")
    return value


def _required(mapping: dict[str, Any], path: str) -> Any:
    current: Any = mapping
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            raise ConfigurationError(f"Missing required configuration value: {path}")
        current = current[key]
    if current is None or current == "":
        raise ConfigurationError(f"Configuration value cannot be empty: {path}")
    return current


def load_environment_config(
    environment: str, project_root: Path | None = None
) -> dict[str, Any]:
    """Load a known environment file without allowing arbitrary paths."""
    safe_environment = resolve_environment(environment)
    root = (project_root or PROJECT_ROOT).resolve()
    config_path = root / "config" / "environments" / f"{safe_environment}.yml"

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Configuration file not found for {safe_environment}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML for {safe_environment}") from exc

    if not isinstance(raw, dict):
        raise ConfigurationError("Environment configuration must be a YAML object")
    if raw.get("environment") != safe_environment:
        raise ConfigurationError(
            f"Configuration environment must equal {safe_environment!r}"
        )

    required_paths = (
        "aws.region_variable",
        "mongodb.uri_parameter",
        "mongodb.deployment_secret",
        "mongodb.database",
        "mongodb.collection",
        "mongodb.index.name",
        "mongodb.index.keys",
        "ops_manager.base_url_parameter",
        "ops_manager.project_id_parameter",
        "ops_manager.api_key_secret",
        "ops_manager.new_user_secret",
        "ops_manager.database",
        "ops_manager.collection",
        "ops_manager.role_name",
        "ops_manager.authentication_database",
    )
    for path in required_paths:
        _required(raw, path)

    keys = raw["mongodb"]["index"]["keys"]
    if not isinstance(keys, list) or not keys:
        raise ConfigurationError("mongodb.index.keys must be a nonempty list")
    for key in keys:
        if not isinstance(key, dict) or not key.get("field"):
            raise ConfigurationError("Each index key requires a field")
        if key.get("direction") not in (-1, 1):
            raise ConfigurationError("Index direction must be 1 or -1")

    return raw


def aws_region(config: dict[str, Any]) -> str:
    """Read the AWS region from the configured environment-variable name."""
    variable_name = config["aws"]["region_variable"]
    region = os.getenv(variable_name, "").strip()
    if not region:
        raise ConfigurationError(f"Required environment variable is not set: {variable_name}")
    return region
