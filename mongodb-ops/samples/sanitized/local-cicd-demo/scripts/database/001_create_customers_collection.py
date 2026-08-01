#!/usr/bin/env python3
"""Create the customers collection and record migration 001 in the selected database."""

from pathlib import Path

from mongodb_local_cicd.cli import guarded_main, run_change_script
from mongodb_local_cicd.database_changes import apply_customers_collection


def main() -> int:
    script = Path(__file__).resolve()
    return run_change_script(
        description=__doc__ or "Create customers collection",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "create_collection",
            "database": config["mongodb"]["database"],
            "collection": config["mongodb"]["collection"],
            "migrationId": "001-create-customers-collection",
        },
        executor=lambda config, provider: apply_customers_collection(
            config, provider, apply_script=script
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

