"""Small AWS Parameter Store and Secrets Manager adapter."""

from __future__ import annotations

import json
from typing import Any

import boto3


class AwsConfigurationError(RuntimeError):
    """Raised when an AWS configuration value is missing or malformed."""


class AwsConfigProvider:
    """Retrieve deployment configuration using the Runner's AWS identity."""

    def __init__(self, region: str) -> None:
        session = boto3.session.Session(region_name=region)
        self._ssm = session.client("ssm")
        self._secrets = session.client("secretsmanager")

    def get_parameter(self, name: str) -> str:
        response = self._ssm.get_parameter(Name=name, WithDecryption=True)
        value = response.get("Parameter", {}).get("Value")
        if not value:
            raise AwsConfigurationError(f"AWS parameter has no value: {name}")
        return str(value)

    def get_secret_json(self, secret_id: str) -> dict[str, Any]:
        response = self._secrets.get_secret_value(SecretId=secret_id)
        secret_string = response.get("SecretString")
        if not secret_string:
            raise AwsConfigurationError(
                f"AWS secret must contain a JSON SecretString: {secret_id}"
            )
        try:
            value = json.loads(secret_string)
        except json.JSONDecodeError as exc:
            raise AwsConfigurationError(f"AWS secret is not valid JSON: {secret_id}") from exc
        if not isinstance(value, dict):
            raise AwsConfigurationError(f"AWS secret must be a JSON object: {secret_id}")
        return value


def require_secret_fields(
    secret: dict[str, Any], secret_id: str, fields: tuple[str, ...]
) -> dict[str, str]:
    """Return required string fields without exposing their values in errors."""
    missing = [field for field in fields if not isinstance(secret.get(field), str)]
    if missing:
        raise AwsConfigurationError(
            f"AWS secret {secret_id!r} is missing required fields: {', '.join(missing)}"
        )
    return {field: secret[field] for field in fields}
