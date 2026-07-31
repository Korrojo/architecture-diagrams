"""Load and validate environment-specific deployment intent."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ALLOWED_ENVIRONMENTS = frozenset({"dev", "sat", "prod"})
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigurationError(ValueError):
    """Raised when deployment configuration is missing or unsafe."""


def resolve_environment(value: str | None) -> str:
    """Return a validated environment from the CLI or DEPLOY_ENV."""
    resolved = (value or os.getenv("DEPLOY_ENV", "")).strip().lower()
    if resolved not in ALLOWED_ENVIRONMENTS:
        allowed = ", ".join(sorted(ALLOWED_ENVIRONMENTS))
        raise ConfigurationError(f"Environment must be one of: {allowed}")
    return resolved


def _required(mapping: dict[str, Any], path: str) -> Any:
    current: Any = mapping
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            raise ConfigurationError(f"Missing required configuration: {path}")
        current = current[key]
    if current is None or current == "":
        raise ConfigurationError(f"Configuration cannot be empty: {path}")
    return current


def load_environment_config(
    environment: str,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Load a known environment file without accepting arbitrary paths."""
    safe_environment = resolve_environment(environment)
    root = (project_root or PROJECT_ROOT).resolve()
    path = root / "config" / "environments" / f"{safe_environment}.yml"
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"No configuration for {safe_environment}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML for {safe_environment}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError("Environment configuration must be an object")
    if raw.get("environment") != safe_environment:
        raise ConfigurationError("Environment file does not match requested environment")

    for key in (
        "mongodb.uri_parameter",
        "mongodb.deployment_secret",
        "mongodb.database",
        "mongodb.migration_collection",
        "mongodb.collection",
        "mongodb.index.name",
        "mongodb.index.keys",
        "ops_manager.base_url_parameter",
        "ops_manager.project_id_parameter",
        "ops_manager.api_key_secret",
        "ops_manager.managed_user_secret",
        "ops_manager.authentication_database",
        "ops_manager.role.name",
        "ops_manager.role.database",
        "ops_manager.role.collection",
        "ops_manager.role.actions",
        "ops_manager.alert.event_type",
        "ops_manager.alert.notifications",
    ):
        _required(raw, key)
    return raw


def local_path(name: str, project_root: Path | None = None) -> Path:
    """Resolve a file under the ignored .local directory."""
    root = (project_root or PROJECT_ROOT).resolve()
    return root / ".local" / name

