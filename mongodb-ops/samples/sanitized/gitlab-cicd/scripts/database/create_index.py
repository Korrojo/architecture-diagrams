#!/usr/bin/env python3
"""Dry-run or apply the sample MongoDB index change."""

from __future__ import annotations

import argparse
import json
import sys

from mongodb_cicd.aws_config import AwsConfigProvider
from mongodb_cicd.config import aws_region, load_environment_config, resolve_environment
from mongodb_cicd.database_change import apply_index, index_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=("dev", "sat", "prod"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Contact AWS and MongoDB and apply the change; default is dry-run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        environment = resolve_environment(args.environment)
        config = load_environment_config(environment)
        if not args.apply:
            print(json.dumps({"mode": "dry-run", **index_plan(config)}, indent=2))
            return 0

        result = apply_index(config, AwsConfigProvider(aws_region(config)))
        print(json.dumps({"environment": environment, **result}))
        return 0
    except Exception as exc:
        print(f"Database change failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
