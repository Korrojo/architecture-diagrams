#!/usr/bin/env python3
"""Create the missing HOST_DOWN alert configuration in the selected Ops Manager project."""

from mongodb_local_cicd.cli import guarded_main, ops_manager_ca_file, run_change_script
from mongodb_local_cicd.ops_manager import apply_host_down_alert, desired_alert


def main() -> int:
    return run_change_script(
        description=__doc__ or "Create host-down alert",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "create_ops_manager_alert",
            "alert": desired_alert(config),
            "projectIdSource": config["ops_manager"]["project_id_parameter"],
        },
        executor=lambda config, provider: apply_host_down_alert(
            config, provider, ca_file=ops_manager_ca_file()
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

