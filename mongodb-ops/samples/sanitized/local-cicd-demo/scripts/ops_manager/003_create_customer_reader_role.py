#!/usr/bin/env python3
"""Create the authoritative collection-scoped customer reader role through Ops Manager."""

from mongodb_local_cicd.cli import guarded_main, ops_manager_ca_file, run_change_script
from mongodb_local_cicd.ops_manager import apply_role, desired_role


def main() -> int:
    return run_change_script(
        description=__doc__ or "Create customer reader role",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "create_authoritative_mongodb_role",
            "role": desired_role(config),
            "projectIdSource": config["ops_manager"]["project_id_parameter"],
            "requires": "auth.authoritativeSet=true",
        },
        executor=lambda config, provider: apply_role(
            config, provider, ca_file=ops_manager_ca_file()
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

