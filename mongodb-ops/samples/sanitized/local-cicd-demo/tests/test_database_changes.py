import pytest

from mongodb_local_cicd.database_changes import DatabaseChangeError, _matching_index


class Collection:
    def __init__(self, indexes: dict[str, object]) -> None:
        self._indexes = indexes

    def index_information(self) -> dict[str, object]:
        return self._indexes


def test_matching_index_accepts_identical_definition() -> None:
    collection = Collection(
        {"ux_customers_email": {"key": [("email", 1)], "unique": True}}
    )
    assert _matching_index(collection, "ux_customers_email", [("email", 1)], True) is True


def test_matching_index_rejects_conflict() -> None:
    collection = Collection(
        {"ux_customers_email": {"key": [("email", -1)], "unique": True}}
    )
    with pytest.raises(DatabaseChangeError, match="conflicting"):
        _matching_index(collection, "ux_customers_email", [("email", 1)], True)


def test_missing_index_returns_false() -> None:
    assert _matching_index(Collection({}), "ux_customers_email", [("email", 1)], True) is False

