import pytest

from mongodb_cicd.config import load_environment_config
from mongodb_cicd.database_change import (
    DatabaseChangeError,
    evaluate_existing_index,
    index_plan,
)


def test_index_plan_contains_no_secret_value() -> None:
    plan = index_plan(load_environment_config("dev"))
    assert plan["operation"] == "create_index"
    assert plan["index"]["name"] == "ix_customerId"
    assert "password" not in str(plan).lower()


def test_missing_index_requires_create() -> None:
    assert evaluate_existing_index({}, "ix_customerId", [("customerId", 1)], False) == "create"


def test_matching_index_is_unchanged() -> None:
    existing = {
        "ix_customerId": {
            "key": [("customerId", 1)],
            "v": 2,
        }
    }
    assert (
        evaluate_existing_index(
            existing, "ix_customerId", [("customerId", 1)], False
        )
        == "unchanged"
    )


def test_conflicting_index_fails() -> None:
    existing = {
        "ix_customerId": {
            "key": [("customerId", -1)],
            "v": 2,
        }
    }
    with pytest.raises(DatabaseChangeError, match="different definition"):
        evaluate_existing_index(
            existing, "ix_customerId", [("customerId", 1)], False
        )
