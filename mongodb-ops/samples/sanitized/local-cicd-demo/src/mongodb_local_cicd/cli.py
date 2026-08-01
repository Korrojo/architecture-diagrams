"""Shared command-line behavior for explicit change scripts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from typing import Any

from .config import load_environment_config, resolve_environment
from .local_config import LocalConfigProvider


def parser(description: str) -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--environment", choices=("dev", "test", "perf", "prod"))
    result.add_argument(
        "--apply",
        action="store_true",
        help="Execute this script; without --apply only a redacted plan is printed",
    )
    result.add_argument(
        "--confirm",
        help="Required value PROD when executing against the prod simulation",
    )
    return result


def require_environment_confirmation(environment: str, apply: bool, confirm: str | None) -> None:
    if apply and environment == "prod" and confirm != "PROD":
        raise ValueError("Production simulation requires --confirm PROD")


def run_change_script(
    *,
    description: str,
    plan_builder: Callable[[dict[str, Any]], dict[str, Any]],
    executor: Callable[[dict[str, Any], LocalConfigProvider], dict[str, Any]],
) -> int:
    """Run a default-dry-run change script with redacted JSON output."""
    args = parser(description).parse_args()
    environment = resolve_environment(args.environment)
    require_environment_confirmation(environment, args.apply, args.confirm)
    config = load_environment_config(environment)
    if not args.apply:
        print(json.dumps({"mode": "plan", **plan_builder(config)}, indent=2))
        return 0
    result = executor(config, LocalConfigProvider())
    print(json.dumps({"environment": environment, **result}, indent=2))
    return 0


def ops_manager_ca_file() -> str | bool:
    """Return the CA bundle path while always retaining TLS verification."""
    return os.getenv("OPS_MANAGER_CA_FILE", "").strip() or True


def guarded_main(main: Callable[[], int]) -> int:
    """Convert a change failure into a concise nonzero shell result."""
    try:
        return main()
    except Exception as exc:
        print(f"Change failed: {exc}", file=sys.stderr)
        return 1
