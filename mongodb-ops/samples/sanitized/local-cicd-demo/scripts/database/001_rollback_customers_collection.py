#!/usr/bin/env python3
"""Rollback migration 001 by dropping only the empty collection created by that change."""

from pathlib import Path

from mongodb_local_cicd.cli import guarded_main, run_change_script
from mongodb_local_cicd.database_changes import rollback_customers_collection


def main() -> int:
    script = Path(__file__).resolve()
    apply_script = script.with_name("001_create_customers_collection.py")
    return run_change_script(
        description=__doc__ or "Rollback customers collection",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "rollback_collection",
            "database": config["mongodb"]["database"],
            "collection": config["mongodb"]["collection"],
            "safety": "Refuses a nonempty collection or unexpected indexes",
            "migrationId": "001-create-customers-collection",
        },
        executor=lambda config, provider: rollback_customers_collection(
            config,
            provider,
            apply_script=apply_script,
            rollback_script=script,
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

