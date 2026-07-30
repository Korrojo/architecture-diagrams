"""Manage a collection-scoped MongoDB reader through Ops Manager Automation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from urllib.parse import quote

import requests
from requests.auth import HTTPDigestAuth

from .aws_config import AwsConfigProvider, require_secret_fields


class OpsManagerChangeError(RuntimeError):
    """Raised when an Ops Manager change is invalid or unsafe."""


def desired_role(database: str, collection: str, role_name: str) -> dict[str, Any]:
    """Build the custom collection-scoped MongoDB role."""
    return {
        "role": role_name,
        "db": database,
        "privileges": [
            {
                "resource": {"db": database, "collection": collection},
                "actions": ["find"],
            }
        ],
        "roles": [],
    }


def desired_user(
    username: str,
    authentication_database: str,
    role_database: str,
    role_name: str,
    initial_password: str,
) -> dict[str, Any]:
    """Build a new Automation-managed MongoDB database user."""
    return {
        "user": username,
        "db": authentication_database,
        "roles": [{"db": role_database, "role": role_name}],
        "initPwd": initial_password,
    }


def _assert_auth_is_managed(automation_config: dict[str, Any]) -> dict[str, Any]:
    auth = automation_config.get("auth")
    if not isinstance(auth, dict):
        raise OpsManagerChangeError(
            "Ops Manager authentication is not configured; this sample will not enable it"
        )
    if auth.get("disabled", False):
        raise OpsManagerChangeError(
            "Ops Manager authentication is disabled; this sample will not change auth mode"
        )
    if auth.get("authoritativeSet") is not True:
        raise OpsManagerChangeError(
            "auth.authoritativeSet must already be true before managing users"
        )
    return auth


def build_collection_reader_change(
    automation_config: dict[str, Any],
    *,
    database: str,
    collection: str,
    role_name: str,
    username: str,
    authentication_database: str,
    initial_password: str,
) -> tuple[dict[str, Any], bool]:
    """Return a modified full Automation config and whether it changed."""
    updated = deepcopy(automation_config)
    auth = _assert_auth_is_managed(updated)
    roles = updated.setdefault("roles", [])
    users = auth.setdefault("usersWanted", [])
    if not isinstance(roles, list) or not isinstance(users, list):
        raise OpsManagerChangeError("Automation roles and auth.usersWanted must be arrays")

    role = desired_role(database, collection, role_name)
    matching_roles = [
        candidate
        for candidate in roles
        if candidate.get("role") == role_name and candidate.get("db") == database
    ]
    if matching_roles and matching_roles[0] != role:
        raise OpsManagerChangeError(
            f"Custom role {database}.{role_name} exists with a different definition"
        )
    changed = not matching_roles
    if not matching_roles:
        roles.append(role)

    matching_users = [
        candidate
        for candidate in users
        if candidate.get("user") == username
        and candidate.get("db") == authentication_database
    ]
    expected_roles = [{"db": database, "role": role_name}]
    if matching_users:
        if matching_users[0].get("roles") != expected_roles:
            raise OpsManagerChangeError(
                f"MongoDB user {authentication_database}.{username} exists with different roles"
            )
    else:
        users.append(
            desired_user(
                username,
                authentication_database,
                database,
                role_name,
                initial_password,
            )
        )
        changed = True

    return updated, changed


class OpsManagerClient:
    """Minimal client for the Ops Manager Automation Configuration endpoint."""

    def __init__(
        self,
        base_url: str,
        project_id: str,
        public_key: str,
        private_key: str,
        ca_file: str | bool = True,
        session: requests.Session | None = None,
    ) -> None:
        self._session = session or requests.Session()
        self._session.auth = HTTPDigestAuth(public_key, private_key)
        safe_project_id = quote(project_id, safe="")
        self._url = (
            f"{base_url.rstrip('/')}/api/public/v1.0/groups/"
            f"{safe_project_id}/automationConfig"
        )
        self._verify = ca_file

    def get_automation_config(self) -> dict[str, Any]:
        response = self._session.get(
            self._url,
            headers={"Accept": "application/json"},
            timeout=(10, 60),
            verify=self._verify,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise OpsManagerChangeError("Ops Manager returned an invalid Automation config")
        return payload

    def put_automation_config(self, payload: dict[str, Any]) -> None:
        response = self._session.put(
            self._url,
            json=payload,
            headers={"Accept": "application/json"},
            timeout=(10, 120),
            verify=self._verify,
        )
        response.raise_for_status()


def apply_collection_reader(
    config: dict[str, Any],
    aws: AwsConfigProvider,
    *,
    ca_file: str | bool = True,
    client_factory: type[OpsManagerClient] = OpsManagerClient,
) -> dict[str, str]:
    """Safely apply the collection reader change to a full Automation config."""
    ops = config["ops_manager"]
    base_url = aws.get_parameter(ops["base_url_parameter"])
    project_id = aws.get_parameter(ops["project_id_parameter"])

    api_secret_id = ops["api_key_secret"]
    api_key = require_secret_fields(
        aws.get_secret_json(api_secret_id),
        api_secret_id,
        ("publicKey", "privateKey"),
    )
    user_secret_id = ops["new_user_secret"]
    new_user = require_secret_fields(
        aws.get_secret_json(user_secret_id),
        user_secret_id,
        ("username", "password"),
    )

    client = client_factory(
        base_url,
        project_id,
        api_key["publicKey"],
        api_key["privateKey"],
        ca_file,
    )
    original = client.get_automation_config()
    version = original.get("version")
    if version is None:
        raise OpsManagerChangeError(
            "Automation config has no version; refusing an unguarded full-config update"
        )

    updated, changed = build_collection_reader_change(
        original,
        database=ops["database"],
        collection=ops["collection"],
        role_name=ops["role_name"],
        username=new_user["username"],
        authentication_database=ops["authentication_database"],
        initial_password=new_user["password"],
    )
    if not changed:
        return {"status": "unchanged", "role": ops["role_name"]}

    latest = client.get_automation_config()
    if latest.get("version") != version:
        raise OpsManagerChangeError(
            "Automation config changed during this job; rerun after reviewing the new version"
        )
    client.put_automation_config(updated)
    return {"status": "changed", "role": ops["role_name"]}
