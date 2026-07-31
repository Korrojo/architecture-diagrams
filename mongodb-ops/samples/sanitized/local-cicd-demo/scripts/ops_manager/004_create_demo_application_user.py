#!/usr/bin/env python3
"""Create the authoritative demonstration MongoDB user through Ops Manager Automation."""

from mongodb_local_cicd.cli import guarded_main, ops_manager_ca_file, run_change_script
from mongodb_local_cicd.ops_manager import apply_user


def main() -> int:
    return run_change_script(
        description=__doc__ or "Create demonstration application user",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "create_authoritative_mongodb_user",
            "authenticationDatabase": config["ops_manager"]["authentication_database"],
            "usernameSource": config["ops_manager"]["managed_user_secret"],
            "assignedRole": config["ops_manager"]["role"]["name"],
            "warning": "The full Automation Configuration is updated in memory only",
        },
        executor=lambda config, provider: apply_user(
            config, provider, ca_file=ops_manager_ca_file()
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

