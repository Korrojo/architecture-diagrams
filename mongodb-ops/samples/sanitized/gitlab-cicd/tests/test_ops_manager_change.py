import pytest

from mongodb_cicd.ops_manager_change import (
    OpsManagerChangeError,
    build_collection_reader_change,
)


def automation_config() -> dict[str, object]:
    return {
        "version": 12,
        "roles": [],
        "auth": {
            "disabled": False,
            "authoritativeSet": True,
            "usersWanted": [],
        },
    }


def apply_to(config: dict[str, object]) -> tuple[dict[str, object], bool]:
    return build_collection_reader_change(
        config,
        database="sample_app_dev",
        collection="orders",
        role_name="ordersCollectionReader",
        username="orders_reader",
        authentication_database="sample_app_dev",
        initial_password="not-a-real-password",
    )


def test_build_change_adds_custom_role_and_user() -> None:
    updated, changed = apply_to(automation_config())
    assert changed is True
    assert updated["roles"][0]["privileges"][0] == {
        "resource": {"db": "sample_app_dev", "collection": "orders"},
        "actions": ["find"],
    }
    assert updated["auth"]["usersWanted"][0]["roles"] == [
        {"db": "sample_app_dev", "role": "ordersCollectionReader"}
    ]
    assert "initPwd" in updated["auth"]["usersWanted"][0]


def test_build_change_is_idempotent() -> None:
    once, changed = apply_to(automation_config())
    assert changed is True
    twice, changed_again = apply_to(once)
    assert changed_again is False
    assert twice == once


def test_existing_user_with_other_roles_fails() -> None:
    config = automation_config()
    config["auth"]["usersWanted"].append(
        {
            "user": "orders_reader",
            "db": "sample_app_dev",
            "roles": [{"db": "sample_app_dev", "role": "readWrite"}],
        }
    )
    with pytest.raises(OpsManagerChangeError, match="different roles"):
        apply_to(config)


def test_sample_will_not_enable_authentication() -> None:
    config = automation_config()
    config["auth"]["disabled"] = True
    with pytest.raises(OpsManagerChangeError, match="disabled"):
        apply_to(config)
