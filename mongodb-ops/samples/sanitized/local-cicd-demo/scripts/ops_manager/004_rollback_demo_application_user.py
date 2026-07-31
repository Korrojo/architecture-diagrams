#!/usr/bin/env python3
"""Rollback the exact authoritative demonstration MongoDB user through Ops Manager."""

from mongodb_local_cicd.cli import guarded_main, ops_manager_ca_file, run_change_script
from mongodb_local_cicd.ops_manager import rollback_user


def main() -> int:
    return run_change_script(
        description=__doc__ or "Rollback demonstration application user",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "rollback_authoritative_mongodb_user",
            "authenticationDatabase": config["ops_manager"]["authentication_database"],
            "usernameSource": config["ops_manager"]["managed_user_secret"],
            "result": "Remove from usersWanted and add to usersDeleted",
        },
        executor=lambda config, provider: rollback_user(
            config, provider, ca_file=ops_manager_ca_file()
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

