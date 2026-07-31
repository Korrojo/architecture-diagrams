#!/usr/bin/env python3
"""Rollback the exact authoritative customer reader role after its users are removed."""

from mongodb_local_cicd.cli import guarded_main, ops_manager_ca_file, run_change_script
from mongodb_local_cicd.ops_manager import desired_role, rollback_role


def main() -> int:
    return run_change_script(
        description=__doc__ or "Rollback customer reader role",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "rollback_authoritative_mongodb_role",
            "role": desired_role(config),
            "dependency": "Managed user rollback must complete first",
        },
        executor=lambda config, provider: rollback_role(
            config, provider, ca_file=ops_manager_ca_file()
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

