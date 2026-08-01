"""Migration ledger for local MongoDB database changes."""

from __future__ import annotations

import getpass
import hashlib
import socket
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class MigrationError(RuntimeError):
    """Raised when migration history makes a change unsafe."""


def script_checksum(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _actor() -> str:
    return f"{getpass.getuser()}@{socket.gethostname()}"


def apply_migration(
    database: Any,
    *,
    ledger_name: str,
    change_id: str,
    description: str,
    apply_script: Path,
    change: Callable[[], dict[str, Any]],
    verify: Callable[[], None],
) -> dict[str, Any]:
    """Apply, verify, and record an idempotent database change."""
    ledger = database[ledger_name]
    checksum = script_checksum(apply_script)
    existing = ledger.find_one({"_id": change_id})
    if existing and existing.get("status") == "applied":
        if existing.get("applyChecksum") != checksum:
            raise MigrationError(f"Applied migration {change_id} has a different checksum")
        verify()
        return {"status": "unchanged", "changeId": change_id}

    execution_id = str(uuid.uuid4())
    started_at = datetime.now(UTC)
    ledger.update_one(
        {"_id": change_id},
        {
            "$set": {
                "description": description,
                "applyScript": apply_script.name,
                "applyChecksum": checksum,
                "status": "running",
                "startedAt": started_at,
                "appliedBy": _actor(),
                "executionId": execution_id,
            }
        },
        upsert=True,
    )
    try:
        details = change()
        verify()
        ledger.update_one(
            {"_id": change_id},
            {
                "$set": {
                    "status": "applied",
                    "appliedAt": datetime.now(UTC),
                    "details": details,
                },
                "$unset": {"error": ""},
            },
        )
        return {"status": "changed", "changeId": change_id, "details": details}
    except Exception as exc:
        ledger.update_one(
            {"_id": change_id},
            {"$set": {"status": "failed", "failedAt": datetime.now(UTC), "error": str(exc)}},
        )
        raise


def rollback_migration(
    database: Any,
    *,
    ledger_name: str,
    change_id: str,
    apply_script: Path,
    rollback_script: Path,
    rollback: Callable[[dict[str, Any]], dict[str, Any]],
    verify: Callable[[], None],
) -> dict[str, Any]:
    """Rollback an applied change without erasing its audit record."""
    ledger = database[ledger_name]
    existing = ledger.find_one({"_id": change_id})
    if not existing or existing.get("status") == "rolled_back":
        verify()
        return {"status": "unchanged", "changeId": change_id}
    if existing.get("status") != "applied":
        raise MigrationError(f"Migration {change_id} is not in applied state")
    if existing.get("applyChecksum") != script_checksum(apply_script):
        raise MigrationError(f"Apply script checksum changed for {change_id}")

    details = rollback(existing.get("details", {}))
    verify()
    ledger.update_one(
        {"_id": change_id},
        {
            "$set": {
                "status": "rolled_back",
                "rolledBackAt": datetime.now(UTC),
                "rolledBackBy": _actor(),
                "rollbackScript": rollback_script.name,
                "rollbackChecksum": script_checksum(rollback_script),
                "rollbackDetails": details,
            }
        },
    )
    return {"status": "rolled_back", "changeId": change_id, "details": details}

