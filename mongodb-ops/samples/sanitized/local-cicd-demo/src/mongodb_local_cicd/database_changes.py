"""Idempotent MongoDB collection and index changes with paired rollback."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pymongo import MongoClient

from .local_config import LocalConfigProvider, require_secret_fields
from .migrations import apply_migration, rollback_migration


class DatabaseChangeError(RuntimeError):
    """Raised when a database change or rollback would be unsafe."""


def _client(
    config: dict[str, Any],
    provider: LocalConfigProvider,
    client_factory: Callable[..., Any] = MongoClient,
) -> Any:
    mongodb = config["mongodb"]
    uri = provider.get_parameter(mongodb["uri_parameter"])
    secret_id = mongodb["deployment_secret"]
    secret = require_secret_fields(
        provider.get_secret_json(secret_id),
        secret_id,
        ("username", "password", "authenticationDatabase"),
    )
    return client_factory(
        uri,
        username=secret["username"],
        password=secret["password"],
        authSource=secret["authenticationDatabase"],
        serverSelectionTimeoutMS=10_000,
        appname="mongodb-local-cicd-demo",
    )


def apply_customers_collection(
    config: dict[str, Any],
    provider: LocalConfigProvider,
    *,
    apply_script: Path,
    client_factory: Callable[..., Any] = MongoClient,
) -> dict[str, Any]:
    client = _client(config, provider, client_factory)
    mongodb = config["mongodb"]
    database = client[mongodb["database"]]
    collection_name = mongodb["collection"]
    try:
        client.admin.command("ping")

        def change() -> dict[str, Any]:
            existing = database.list_collection_names(filter={"name": collection_name})
            if existing:
                return {"created": False, "collection": collection_name}
            database.create_collection(collection_name)
            return {"created": True, "collection": collection_name}

        def verify() -> None:
            if collection_name not in database.list_collection_names(
                filter={"name": collection_name}
            ):
                raise DatabaseChangeError(f"Collection was not created: {collection_name}")

        return apply_migration(
            database,
            ledger_name=mongodb["migration_collection"],
            change_id="001-create-customers-collection",
            description="Create the customers collection",
            apply_script=apply_script,
            change=change,
            verify=verify,
        )
    finally:
        client.close()


def rollback_customers_collection(
    config: dict[str, Any],
    provider: LocalConfigProvider,
    *,
    apply_script: Path,
    rollback_script: Path,
    client_factory: Callable[..., Any] = MongoClient,
) -> dict[str, Any]:
    client = _client(config, provider, client_factory)
    mongodb = config["mongodb"]
    database = client[mongodb["database"]]
    collection_name = mongodb["collection"]
    try:
        client.admin.command("ping")

        def rollback(details: dict[str, Any]) -> dict[str, Any]:
            if not details.get("created"):
                return {"dropped": False, "reason": "collection pre-existed"}
            if collection_name not in database.list_collection_names(
                filter={"name": collection_name}
            ):
                return {"dropped": False, "reason": "already absent"}
            collection = database[collection_name]
            if collection.estimated_document_count() != 0:
                raise DatabaseChangeError("Refusing to drop a nonempty collection")
            unexpected = set(collection.index_information()) - {"_id_"}
            if unexpected:
                raise DatabaseChangeError(
                    f"Refusing to drop collection with indexes: {', '.join(sorted(unexpected))}"
                )
            collection.drop()
            return {"dropped": True, "collection": collection_name}

        def verify() -> None:
            existing = database[mongodb["migration_collection"]].find_one(
                {"_id": "001-create-customers-collection"}
            )
            created = bool((existing or {}).get("details", {}).get("created"))
            if created and collection_name in database.list_collection_names(
                filter={"name": collection_name}
            ):
                raise DatabaseChangeError(f"Collection still exists: {collection_name}")

        return rollback_migration(
            database,
            ledger_name=mongodb["migration_collection"],
            change_id="001-create-customers-collection",
            apply_script=apply_script,
            rollback_script=rollback_script,
            rollback=rollback,
            verify=verify,
        )
    finally:
        client.close()


def _desired_index(config: dict[str, Any]) -> tuple[str, list[tuple[str, int]], bool]:
    index = config["mongodb"]["index"]
    keys = [(item["field"], int(item["direction"])) for item in index["keys"]]
    return index["name"], keys, bool(index.get("unique", False))


def _matching_index(collection: Any, name: str, keys: list[tuple[str, int]], unique: bool) -> bool:
    existing = collection.index_information().get(name)
    if not existing:
        return False
    existing_keys = [tuple(item) for item in existing.get("key", [])]
    if existing_keys != keys or bool(existing.get("unique", False)) != unique:
        raise DatabaseChangeError(f"Index {name} exists with a conflicting definition")
    return True


def apply_customers_email_index(
    config: dict[str, Any],
    provider: LocalConfigProvider,
    *,
    apply_script: Path,
    client_factory: Callable[..., Any] = MongoClient,
) -> dict[str, Any]:
    client = _client(config, provider, client_factory)
    mongodb = config["mongodb"]
    database = client[mongodb["database"]]
    collection_name = mongodb["collection"]
    name, keys, unique = _desired_index(config)
    try:
        client.admin.command("ping")
        if collection_name not in database.list_collection_names(filter={"name": collection_name}):
            raise DatabaseChangeError("Customers collection must exist before creating its index")
        collection = database[collection_name]

        def change() -> dict[str, Any]:
            if _matching_index(collection, name, keys, unique):
                return {"created": False, "index": name}
            collection.create_index(keys, name=name, unique=unique)
            return {"created": True, "index": name}

        def verify() -> None:
            if not _matching_index(collection, name, keys, unique):
                raise DatabaseChangeError(f"Index was not created: {name}")

        return apply_migration(
            database,
            ledger_name=mongodb["migration_collection"],
            change_id="002-create-customers-email-index",
            description="Create the unique customers email index",
            apply_script=apply_script,
            change=change,
            verify=verify,
        )
    finally:
        client.close()


def rollback_customers_email_index(
    config: dict[str, Any],
    provider: LocalConfigProvider,
    *,
    apply_script: Path,
    rollback_script: Path,
    client_factory: Callable[..., Any] = MongoClient,
) -> dict[str, Any]:
    client = _client(config, provider, client_factory)
    mongodb = config["mongodb"]
    database = client[mongodb["database"]]
    collection = database[mongodb["collection"]]
    name, keys, unique = _desired_index(config)
    try:
        client.admin.command("ping")

        def rollback(details: dict[str, Any]) -> dict[str, Any]:
            if not details.get("created"):
                return {"dropped": False, "reason": "index pre-existed"}
            if name not in collection.index_information():
                return {"dropped": False, "reason": "already absent"}
            _matching_index(collection, name, keys, unique)
            collection.drop_index(name)
            return {"dropped": True, "index": name}

        def verify() -> None:
            existing = database[mongodb["migration_collection"]].find_one(
                {"_id": "002-create-customers-email-index"}
            )
            created = bool((existing or {}).get("details", {}).get("created"))
            if created and name in collection.index_information():
                raise DatabaseChangeError(f"Index still exists: {name}")

        return rollback_migration(
            database,
            ledger_name=mongodb["migration_collection"],
            change_id="002-create-customers-email-index",
            apply_script=apply_script,
            rollback_script=rollback_script,
            rollback=rollback,
            verify=verify,
        )
    finally:
        client.close()

