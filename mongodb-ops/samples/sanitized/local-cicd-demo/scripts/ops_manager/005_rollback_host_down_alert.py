#!/usr/bin/env python3
"""Rollback only the exact HOST_DOWN alert created by the paired creation script."""

from mongodb_local_cicd.cli import guarded_main, ops_manager_ca_file, run_change_script
from mongodb_local_cicd.ops_manager import desired_alert, rollback_host_down_alert


def main() -> int:
    return run_change_script(
        description=__doc__ or "Rollback host-down alert",
        plan_builder=lambda config: {
            "environment": config["environment"],
            "operation": "rollback_ops_manager_alert",
            "alert": desired_alert(config),
            "safety": "Delete only the saved ID after fingerprint verification",
        },
        executor=lambda config, provider: rollback_host_down_alert(
            config, provider, ca_file=ops_manager_ca_file()
        ),
    )


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))

