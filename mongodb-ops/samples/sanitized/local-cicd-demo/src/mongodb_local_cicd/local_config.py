"""Local adapters that mimic Parameter Store and Secrets Manager lookups."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT, local_path


class LocalConfigurationError(RuntimeError):
    """Raised when a local parameter or secret is unavailable."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LocalConfigurationError(
            f"Missing {path}; run ./bin/initialize_local_demo.sh"
        ) from exc
    except json.JSONDecodeError as exc:
        raise LocalConfigurationError(f"Invalid JSON in {path}") from exc
    if not isinstance(value, dict):
        raise LocalConfigurationError(f"Expected a JSON object in {path}")
    return value


class LocalConfigProvider:
    """Resolve named values using the same contract as the future AWS adapter."""

    def __init__(self, project_root: Path | None = None) -> None:
        root = (project_root or PROJECT_ROOT).resolve()
        self._parameters = _load_json(local_path("parameter-store.json", root))
        self._secrets = _load_json(local_path("secrets-manager.json", root))

    def get_parameter(self, name: str) -> str:
        value = self._parameters.get(name)
        if not isinstance(value, str) or not value:
            raise LocalConfigurationError(f"Parameter Store value not found: {name}")
        return value

    def get_secret_json(self, secret_id: str) -> dict[str, Any]:
        value = self._secrets.get(secret_id)
        if not isinstance(value, dict):
            raise LocalConfigurationError(f"Secrets Manager value not found: {secret_id}")
        return value


def require_secret_fields(
    secret: dict[str, Any],
    secret_id: str,
    fields: tuple[str, ...],
) -> dict[str, str]:
    """Return required secret strings without exposing values in an error."""
    missing = [field for field in fields if not isinstance(secret.get(field), str)]
    if missing:
        raise LocalConfigurationError(
            f"Secret {secret_id!r} is missing fields: {', '.join(missing)}"
        )
    return {field: str(secret[field]) for field in fields}

