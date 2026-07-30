#!/usr/bin/env python3
"""Dry-run or create a collection-scoped MongoDB reader through Ops Manager."""

from __future__ import annotations

import argparse
import json
import os
import sys

from mongodb_cicd.aws_config import AwsConfigProvider
from mongodb_cicd.config import aws_region, load_environment_config, resolve_environment
from mongodb_cicd.ops_manager_change import apply_collection_reader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=("dev", "sat", "prod"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Contact AWS and Ops Manager and apply the change; default is dry-run",
    )
    return parser.parse_args()


def dry_run_plan(config: dict[str, object]) -> dict[str, object]:
    ops = config["ops_manager"]
    assert isinstance(ops, dict)
    return {
        "mode": "dry-run",
        "environment": config["environment"],
        "operation": "create_collection_scoped_reader",
        "database": ops["database"],
        "collection": ops["collection"],
        "role": ops["role_name"],
        "actions": ["find"],
        "usernameSource": ops["new_user_secret"],
        "configurationSources": {
            "baseUrlParameter": ops["base_url_parameter"],
            "projectIdParameter": ops["project_id_parameter"],
            "apiKeySecret": ops["api_key_secret"],
        },
        "warning": "Apply replaces the full Ops Manager project Automation config.",
    }


def main() -> int:
    args = parse_args()
    try:
        environment = resolve_environment(args.environment)
        config = load_environment_config(environment)
        if not args.apply:
            print(json.dumps(dry_run_plan(config), indent=2))
            return 0

        ca_file: str | bool = os.getenv("OPS_MANAGER_CA_FILE", "").strip() or True
        result = apply_collection_reader(
            config,
            AwsConfigProvider(aws_region(config)),
            ca_file=ca_file,
        )
        print(json.dumps({"environment": environment, **result}))
        return 0
    except Exception as exc:
        print(f"Ops Manager change failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
