#!/usr/bin/env python3
"""Create the unique customers email index and record migration 002."""

from pathlib import Path

from mongodb_local_cicd.cli import guarded_main, run_change_script
from mongodb_local_cicd.database_changes import apply_customers_email_index


def main() -> int:
    script = Path(__file__).resolve()
    return run_change_script(
        description=__doc__ or "Create customers email index",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "create_index",
            "database": config["mongodb"]["database"],
            "collection": config["mongodb"]["collection"],
            "index": config["mongodb"]["index"],
            "migrationId": "002-create-customers-email-index",
        },
        executor=lambda config, provider: apply_customers_email_index(
            config, provider, apply_script=script
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

