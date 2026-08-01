import pytest

from mongodb_local_cicd.config import load_environment_config
from mongodb_local_cicd.ops_manager import (
    OpsManagerChangeError,
    add_role,
    add_user,
    alert_fingerprint,
    desired_alert,
    desired_role,
    desired_user,
    remove_role,
    remove_user,
)


def automation_config() -> dict[str, object]:
    return {
        "version": 12,
        "roles": [],
        "auth": {
            "disabled": False,
            "authoritativeSet": True,
            "usersWanted": [],
            "usersDeleted": [],
        },
    }


def test_role_apply_and_rollback_are_idempotent() -> None:
    role = desired_role(load_environment_config("dev"))
    applied, changed = add_role(automation_config(), role)
    assert changed is True
    _, changed_again = add_role(applied, role)
    assert changed_again is False
    rolled_back, removed = remove_role(applied, role)
    assert removed is True
    _, removed_again = remove_role(rolled_back, role)
    assert removed_again is False


def test_role_rollback_refuses_while_user_depends_on_it() -> None:
    config = load_environment_config("dev")
    role = desired_role(config)
    applied, _ = add_role(automation_config(), role)
    user = desired_user(config, {"username": "demo", "password": "secret"})
    with_user, _ = add_user(applied, user)
    with pytest.raises(OpsManagerChangeError, match="Remove users"):
        remove_role(with_user, role)


def test_user_apply_and_rollback_adds_deletion_marker() -> None:
    config = load_environment_config("dev")
    user = desired_user(config, {"username": "demo", "password": "secret"})
    applied, changed = add_user(automation_config(), user)
    assert changed is True
    assert applied["auth"]["usersWanted"][0]["initPwd"] == "secret"
    rolled_back, removed = remove_user(applied, user)
    assert removed is True
    assert rolled_back["auth"]["usersWanted"] == []
    assert rolled_back["auth"]["usersDeleted"] == [
        {"user": "demo", "dbs": ["cicd_demo_dev"]}
    ]


def test_non_authoritative_project_is_rejected() -> None:
    config = automation_config()
    config["auth"]["authoritativeSet"] = False
    with pytest.raises(OpsManagerChangeError, match="authoritativeSet"):
        add_role(config, desired_role(load_environment_config("dev")))


def test_alert_fingerprint_ignores_server_generated_fields() -> None:
    desired = desired_alert(load_environment_config("dev"))
    returned = {
        **desired,
        "id": "alert-id",
        "groupId": "project-id",
        "notifications": [
            {**desired["notifications"][0], "id": "notification-id", "groupName": "Demo"}
        ],
    }
    assert alert_fingerprint(returned) == alert_fingerprint(desired)

