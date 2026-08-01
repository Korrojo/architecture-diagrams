"""Guarded Ops Manager Automation and alert configuration changes."""

from __future__ import annotations

import hashlib
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from requests.auth import HTTPDigestAuth

from .config import local_path
from .local_config import LocalConfigProvider, require_secret_fields


class OpsManagerChangeError(RuntimeError):
    """Raised when an Ops Manager change would be invalid or unsafe."""


def assert_authoritative(automation_config: dict[str, Any]) -> dict[str, Any]:
    """Require already-enabled authoritative MongoDB user management."""
    auth = automation_config.get("auth")
    if not isinstance(auth, dict):
        raise OpsManagerChangeError("Ops Manager authentication is not configured")
    if auth.get("disabled", False):
        raise OpsManagerChangeError("Ops Manager authentication is disabled")
    if auth.get("authoritativeSet") is not True:
        raise OpsManagerChangeError("auth.authoritativeSet must already be true")
    return auth


def desired_role(config: dict[str, Any]) -> dict[str, Any]:
    role = config["ops_manager"]["role"]
    return {
        "role": role["name"],
        "db": role["database"],
        "privileges": [
            {
                "resource": {"db": role["database"], "collection": role["collection"]},
                "actions": list(role["actions"]),
            }
        ],
        "roles": [],
    }


def add_role(
    automation_config: dict[str, Any],
    role: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(automation_config)
    assert_authoritative(updated)
    roles = updated.setdefault("roles", [])
    if not isinstance(roles, list):
        raise OpsManagerChangeError("Automation roles must be an array")
    matches = [
        item
        for item in roles
        if item.get("role") == role["role"] and item.get("db") == role["db"]
    ]
    if matches:
        if matches[0] != role:
            raise OpsManagerChangeError("Custom role exists with a conflicting definition")
        return updated, False
    roles.append(role)
    return updated, True


def remove_role(
    automation_config: dict[str, Any],
    role: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(automation_config)
    auth = assert_authoritative(updated)
    users = auth.get("usersWanted", [])
    for user in users:
        if {"db": role["db"], "role": role["role"]} in user.get("roles", []):
            raise OpsManagerChangeError("Remove users assigned to the role before rolling it back")
    roles = updated.setdefault("roles", [])
    matches = [
        item
        for item in roles
        if item.get("role") == role["role"] and item.get("db") == role["db"]
    ]
    if not matches:
        return updated, False
    if matches[0] != role:
        raise OpsManagerChangeError("Refusing to remove a role that was subsequently modified")
    updated["roles"] = [item for item in roles if item is not matches[0]]
    return updated, True


def desired_user(config: dict[str, Any], secret: dict[str, str]) -> dict[str, Any]:
    ops = config["ops_manager"]
    role = ops["role"]
    return {
        "user": secret["username"],
        "db": ops["authentication_database"],
        "roles": [{"db": role["database"], "role": role["name"]}],
        "initPwd": secret["password"],
    }


def add_user(
    automation_config: dict[str, Any],
    user: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(automation_config)
    auth = assert_authoritative(updated)
    users = auth.setdefault("usersWanted", [])
    if not isinstance(users, list):
        raise OpsManagerChangeError("auth.usersWanted must be an array")
    matches = [
        item
        for item in users
        if item.get("user") == user["user"] and item.get("db") == user["db"]
    ]
    if matches:
        if matches[0].get("roles") != user["roles"]:
            raise OpsManagerChangeError("Managed user exists with different role assignments")
        return updated, False
    users.append(user)
    deleted = auth.setdefault("usersDeleted", [])
    auth["usersDeleted"] = [
        item
        for item in deleted
        if not (item.get("user") == user["user"] and user["db"] in item.get("dbs", []))
    ]
    return updated, True


def remove_user(
    automation_config: dict[str, Any],
    user: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(automation_config)
    auth = assert_authoritative(updated)
    users = auth.setdefault("usersWanted", [])
    matches = [
        item
        for item in users
        if item.get("user") == user["user"] and item.get("db") == user["db"]
    ]
    if not matches:
        return updated, False
    if matches[0].get("roles") != user["roles"]:
        raise OpsManagerChangeError("Refusing to remove a user that was subsequently modified")
    auth["usersWanted"] = [item for item in users if item is not matches[0]]
    deleted = auth.setdefault("usersDeleted", [])
    marker = {"user": user["user"], "dbs": [user["db"]]}
    if marker not in deleted:
        deleted.append(marker)
    return updated, True


def desired_alert(config: dict[str, Any]) -> dict[str, Any]:
    alert = config["ops_manager"]["alert"]
    return {
        "enabled": bool(alert.get("enabled", True)),
        "eventTypeName": alert["event_type"],
        "notifications": deepcopy(alert["notifications"]),
    }


def _canonical_alert(alert: dict[str, Any]) -> dict[str, Any]:
    notification_fields = (
        "typeName",
        "roles",
        "delayMin",
        "intervalMin",
        "emailAddress",
        "username",
        "teamId",
        "webhookUrl",
    )
    notifications = [
        {key: item[key] for key in notification_fields if key in item}
        for item in alert.get("notifications", [])
    ]
    return {
        "enabled": bool(alert.get("enabled", False)),
        "eventTypeName": alert.get("eventTypeName"),
        "matchers": alert.get("matchers", []),
        "notifications": notifications,
    }


def alert_fingerprint(alert: dict[str, Any]) -> str:
    canonical = json.dumps(_canonical_alert(alert), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class OpsManagerClient:
    """Small digest-auth client for Automation and alert endpoints."""

    def __init__(
        self,
        base_url: str,
        project_id: str,
        public_key: str,
        private_key: str,
        *,
        ca_file: str | bool = True,
        session: requests.Session | None = None,
    ) -> None:
        self._session = session or requests.Session()
        self._session.auth = HTTPDigestAuth(public_key, private_key)
        project = quote(project_id, safe="")
        self._project_url = f"{base_url.rstrip('/')}/api/public/v1.0/groups/{project}"
        self._verify = ca_file

    def _json(self, response: requests.Response) -> dict[str, Any]:
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise OpsManagerChangeError("Ops Manager returned a non-object response")
        return payload

    def get_automation_config(self, *, no_secrets: bool) -> dict[str, Any]:
        suffix = "/noSecrets" if no_secrets else ""
        response = self._session.get(
            f"{self._project_url}/automationConfig{suffix}",
            headers={"Accept": "application/json"},
            timeout=(10, 60),
            verify=self._verify,
        )
        return self._json(response)

    def put_automation_config(
        self,
        payload: dict[str, Any],
        *,
        no_secrets: bool,
        expected_version: int,
    ) -> None:
        latest = self.get_automation_config(no_secrets=no_secrets)
        if latest.get("version") != expected_version:
            raise OpsManagerChangeError(
                "Automation configuration changed concurrently; rerun after review"
            )
        suffix = "/noSecrets" if no_secrets else ""
        response = self._session.put(
            f"{self._project_url}/automationConfig{suffix}",
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=(10, 120),
            verify=self._verify,
        )
        response.raise_for_status()

    def wait_for_goal_state(self, timeout_seconds: int = 300) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            response = self._session.get(
                f"{self._project_url}/automationStatus",
                headers={"Accept": "application/json"},
                timeout=(10, 60),
                verify=self._verify,
            )
            status = self._json(response)
            goal = status.get("goalVersion")
            processes = status.get("processes", [])
            if goal is not None and all(
                process.get("lastGoalVersionAchieved") == goal for process in processes
            ):
                return
            time.sleep(2)
        raise OpsManagerChangeError("Timed out waiting for Ops Manager goal state")

    def list_alerts(self) -> list[dict[str, Any]]:
        response = self._session.get(
            f"{self._project_url}/alertConfigs",
            headers={"Accept": "application/json"},
            timeout=(10, 60),
            verify=self._verify,
        )
        payload = self._json(response)
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise OpsManagerChangeError("Ops Manager alert list is invalid")
        return results

    def create_alert(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._session.post(
            f"{self._project_url}/alertConfigs",
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=(10, 60),
            verify=self._verify,
        )
        return self._json(response)

    def get_alert(self, alert_id: str) -> dict[str, Any]:
        safe_id = quote(alert_id, safe="")
        response = self._session.get(
            f"{self._project_url}/alertConfigs/{safe_id}",
            headers={"Accept": "application/json"},
            timeout=(10, 60),
            verify=self._verify,
        )
        return self._json(response)

    def delete_alert(self, alert_id: str) -> None:
        safe_id = quote(alert_id, safe="")
        response = self._session.delete(
            f"{self._project_url}/alertConfigs/{safe_id}",
            headers={"Accept": "application/json"},
            timeout=(10, 60),
            verify=self._verify,
        )
        response.raise_for_status()


def _client(
    config: dict[str, Any],
    provider: LocalConfigProvider,
    *,
    ca_file: str | bool,
    client_factory: type[OpsManagerClient] = OpsManagerClient,
) -> OpsManagerClient:
    ops = config["ops_manager"]
    base_url = provider.get_parameter(ops["base_url_parameter"])
    project_id = provider.get_parameter(ops["project_id_parameter"])
    secret_id = ops["api_key_secret"]
    api_key = require_secret_fields(
        provider.get_secret_json(secret_id), secret_id, ("publicKey", "privateKey")
    )
    return client_factory(
        base_url,
        project_id,
        api_key["publicKey"],
        api_key["privateKey"],
        ca_file=ca_file,
    )


def apply_role(
    config: dict[str, Any], provider: LocalConfigProvider, *, ca_file: str | bool
) -> dict[str, Any]:
    client = _client(config, provider, ca_file=ca_file)
    current = client.get_automation_config(no_secrets=True)
    version = current.get("version")
    if not isinstance(version, int):
        raise OpsManagerChangeError("Automation configuration has no integer version")
    role = desired_role(config)
    updated, changed = add_role(current, role)
    if not changed:
        return {"status": "unchanged", "role": role["role"]}
    client.put_automation_config(updated, no_secrets=True, expected_version=version)
    client.wait_for_goal_state()
    _, would_change = add_role(client.get_automation_config(no_secrets=True), role)
    if would_change:
        raise OpsManagerChangeError("Role verification failed")
    return {"status": "changed", "role": role["role"]}


def rollback_role(
    config: dict[str, Any], provider: LocalConfigProvider, *, ca_file: str | bool
) -> dict[str, Any]:
    client = _client(config, provider, ca_file=ca_file)
    current = client.get_automation_config(no_secrets=True)
    version = current.get("version")
    if not isinstance(version, int):
        raise OpsManagerChangeError("Automation configuration has no integer version")
    role = desired_role(config)
    updated, changed = remove_role(current, role)
    if not changed:
        return {"status": "unchanged", "role": role["role"]}
    client.put_automation_config(updated, no_secrets=True, expected_version=version)
    client.wait_for_goal_state()
    _, still_changed = remove_role(client.get_automation_config(no_secrets=True), role)
    if still_changed:
        raise OpsManagerChangeError("Role rollback verification failed")
    return {"status": "rolled_back", "role": role["role"]}


def _managed_user(config: dict[str, Any], provider: LocalConfigProvider) -> dict[str, Any]:
    secret_id = config["ops_manager"]["managed_user_secret"]
    secret = require_secret_fields(
        provider.get_secret_json(secret_id), secret_id, ("username", "password")
    )
    return desired_user(config, secret)


def apply_user(
    config: dict[str, Any], provider: LocalConfigProvider, *, ca_file: str | bool
) -> dict[str, Any]:
    client = _client(config, provider, ca_file=ca_file)
    current = client.get_automation_config(no_secrets=False)
    version = current.get("version")
    if not isinstance(version, int):
        raise OpsManagerChangeError("Automation configuration has no integer version")
    user = _managed_user(config, provider)
    updated, changed = add_user(current, user)
    if not changed:
        return {"status": "unchanged", "user": user["user"]}
    client.put_automation_config(updated, no_secrets=False, expected_version=version)
    client.wait_for_goal_state()
    _, would_change = add_user(client.get_automation_config(no_secrets=True), user)
    if would_change:
        raise OpsManagerChangeError("User verification failed")
    return {"status": "changed", "user": user["user"]}


def rollback_user(
    config: dict[str, Any], provider: LocalConfigProvider, *, ca_file: str | bool
) -> dict[str, Any]:
    client = _client(config, provider, ca_file=ca_file)
    current = client.get_automation_config(no_secrets=True)
    version = current.get("version")
    if not isinstance(version, int):
        raise OpsManagerChangeError("Automation configuration has no integer version")
    user = _managed_user(config, provider)
    updated, changed = remove_user(current, user)
    if not changed:
        return {"status": "unchanged", "user": user["user"]}
    client.put_automation_config(updated, no_secrets=True, expected_version=version)
    client.wait_for_goal_state()
    _, still_changed = remove_user(client.get_automation_config(no_secrets=True), user)
    if still_changed:
        raise OpsManagerChangeError("User rollback verification failed")
    return {"status": "rolled_back", "user": user["user"]}


def _alert_state_path(config: dict[str, Any]) -> Path:
    environment = config["environment"]
    return local_path(f"state/{environment}/005-host-down-alert.json")


def apply_host_down_alert(
    config: dict[str, Any], provider: LocalConfigProvider, *, ca_file: str | bool
) -> dict[str, Any]:
    client = _client(config, provider, ca_file=ca_file)
    desired = desired_alert(config)
    fingerprint = alert_fingerprint(desired)
    matches = [item for item in client.list_alerts() if alert_fingerprint(item) == fingerprint]
    if len(matches) > 1:
        raise OpsManagerChangeError("Multiple equivalent HOST_DOWN alerts already exist")
    if matches:
        created = matches[0]
        status = "unchanged"
    else:
        same_event = [
            item
            for item in client.list_alerts()
            if item.get("eventTypeName") == desired["eventTypeName"]
            and item.get("matchers", []) == desired.get("matchers", [])
        ]
        if same_event:
            raise OpsManagerChangeError(
                "A HOST_DOWN alert exists with different settings; refusing a duplicate"
            )
        created = client.create_alert(desired)
        status = "changed"
    alert_id = created.get("id")
    if not isinstance(alert_id, str):
        raise OpsManagerChangeError("Ops Manager did not return an alert configuration ID")
    verified = client.get_alert(alert_id)
    if alert_fingerprint(verified) != fingerprint:
        raise OpsManagerChangeError("Created alert does not match the requested configuration")
    state_path = _alert_state_path(config)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"alertId": alert_id, "fingerprint": fingerprint}, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"status": status, "alertId": alert_id, "eventTypeName": "HOST_DOWN"}


def rollback_host_down_alert(
    config: dict[str, Any], provider: LocalConfigProvider, *, ca_file: str | bool
) -> dict[str, Any]:
    client = _client(config, provider, ca_file=ca_file)
    desired = desired_alert(config)
    fingerprint = alert_fingerprint(desired)
    state_path = _alert_state_path(config)
    alert_id: str | None = None
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("fingerprint") != fingerprint:
            raise OpsManagerChangeError("Saved alert state does not match the current script")
        alert_id = state.get("alertId")
    if not alert_id:
        matches = [item for item in client.list_alerts() if alert_fingerprint(item) == fingerprint]
        if not matches:
            return {"status": "unchanged", "eventTypeName": "HOST_DOWN"}
        if len(matches) != 1:
            raise OpsManagerChangeError("Cannot uniquely identify the alert to roll back")
        alert_id = matches[0].get("id")
    if not isinstance(alert_id, str):
        raise OpsManagerChangeError("Alert state contains an invalid ID")
    existing = client.get_alert(alert_id)
    if alert_fingerprint(existing) != fingerprint:
        raise OpsManagerChangeError("Refusing to delete an alert that was subsequently modified")
    client.delete_alert(alert_id)
    if any(item.get("id") == alert_id for item in client.list_alerts()):
        raise OpsManagerChangeError("Alert rollback verification failed")
    if state_path.exists():
        state_path.unlink()
    return {"status": "rolled_back", "alertId": alert_id, "eventTypeName": "HOST_DOWN"}
