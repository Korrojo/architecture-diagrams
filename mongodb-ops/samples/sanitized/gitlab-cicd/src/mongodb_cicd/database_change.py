"""Idempotent MongoDB index deployment."""

from __future__ import annotations

from typing import Any, Callable

from pymongo import MongoClient

from .aws_config import AwsConfigProvider, require_secret_fields


class DatabaseChangeError(RuntimeError):
    """Raised when applying the database change would be unsafe."""


def index_plan(config: dict[str, Any]) -> dict[str, Any]:
    """Return a secret-free description of the intended MongoDB change."""
    mongodb = config["mongodb"]
    return {
        "environment": config["environment"],
        "operation": "create_index",
        "database": mongodb["database"],
        "collection": mongodb["collection"],
        "index": {
            "name": mongodb["index"]["name"],
            "keys": mongodb["index"]["keys"],
            "unique": bool(mongodb["index"].get("unique", False)),
        },
        "configurationSources": {
            "uriParameter": mongodb["uri_parameter"],
            "credentialSecret": mongodb["deployment_secret"],
        },
    }


def evaluate_existing_index(
    index_information: dict[str, Any],
    name: str,
    desired_keys: list[tuple[str, int]],
    desired_unique: bool,
) -> str:
    """Return create/unchanged, or fail when a same-name index conflicts."""
    existing = index_information.get(name)
    if existing is None:
        return "create"
    existing_keys = [tuple(item) for item in existing.get("key", [])]
    existing_unique = bool(existing.get("unique", False))
    if existing_keys == desired_keys and existing_unique == desired_unique:
        return "unchanged"
    raise DatabaseChangeError(
        f"Index {name!r} already exists with a different definition; refusing to replace it"
    )


def apply_index(
    config: dict[str, Any],
    aws: AwsConfigProvider,
    client_factory: Callable[..., Any] = MongoClient,
) -> dict[str, str]:
    """Create the configured index if it does not already exist."""
    mongodb = config["mongodb"]
    uri = aws.get_parameter(mongodb["uri_parameter"])
    secret_id = mongodb["deployment_secret"]
    credentials = require_secret_fields(
        aws.get_secret_json(secret_id),
        secret_id,
        ("username", "password", "authenticationDatabase"),
    )

    client = client_factory(
        uri,
        username=credentials["username"],
        password=credentials["password"],
        authSource=credentials["authenticationDatabase"],
        serverSelectionTimeoutMS=10_000,
        appname="mongodb-gitlab-cicd-sample",
    )
    try:
        client.admin.command("ping")
        database = client[mongodb["database"]]
        collection_name = mongodb["collection"]
        if collection_name not in database.list_collection_names(
            filter={"name": collection_name}
        ):
            raise DatabaseChangeError(
                f"Collection {mongodb['database']}.{collection_name} does not exist; "
                "refusing to create it implicitly"
            )

        collection = database[collection_name]
        index = mongodb["index"]
        keys = [(item["field"], int(item["direction"])) for item in index["keys"]]
        unique = bool(index.get("unique", False))
        action = evaluate_existing_index(
            collection.index_information(), index["name"], keys, unique
        )
        if action == "create":
            collection.create_index(keys, name=index["name"], unique=unique)
            return {"status": "changed", "index": index["name"]}
        return {"status": "unchanged", "index": index["name"]}
    finally:
        client.close()
