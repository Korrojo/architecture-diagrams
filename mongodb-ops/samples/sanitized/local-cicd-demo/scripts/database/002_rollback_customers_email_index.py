#!/usr/bin/env python3
"""Rollback migration 002 by dropping only the exact index created by that change."""

from pathlib import Path

from mongodb_local_cicd.cli import guarded_main, run_change_script
from mongodb_local_cicd.database_changes import rollback_customers_email_index


def main() -> int:
    script = Path(__file__).resolve()
    apply_script = script.with_name("002_create_customers_email_index.py")
    return run_change_script(
        description=__doc__ or "Rollback customers email index",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "rollback_index",
            "database": config["mongodb"]["database"],
            "collection": config["mongodb"]["collection"],
            "index": config["mongodb"]["index"]["name"],
            "migrationId": "002-create-customers-email-index",
        },
        executor=lambda config, provider: rollback_customers_email_index(
            config,
            provider,
            apply_script=apply_script,
            rollback_script=script,
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

