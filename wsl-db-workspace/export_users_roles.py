#!/usr/bin/env python3
"""Export MongoDB users, assigned roles, and inherited privileges to CSV."""

import argparse
import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


def json_cell(value):
    """Serialize nested MongoDB values safely for a CSV cell."""
    return json.dumps(value or [], default=str, sort_keys=True)


def safe_name(value):
    """Reject values that could escape the expected directory structure."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError(f"Invalid environment or cluster name: {value}")
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export MongoDB users and their assigned roles to CSV."
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["DEV", "SAT", "PROD"],
        help="Environment directory containing the cluster .env file.",
    )
    parser.add_argument(
        "--cluster",
        required=True,
        help="Cluster name and .env filename without the .env extension.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    environment = safe_name(args.environment)
    cluster = safe_name(args.cluster)

    env_file = (
        Path.home()
        / ".config"
        / "work"
        / "mongodb"
        / environment
        / f"{cluster}.env"
    )

    if not env_file.is_file():
        raise FileNotFoundError(f"Credential file not found: {env_file}")

    load_dotenv(env_file, override=True)

    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise RuntimeError(f"MONGODB_URI is missing from {env_file}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = (
        Path.home()
        / "work"
        / "data"
        / "mongodb"
        / environment
        / cluster
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"users_roles_{timestamp}.csv"

    columns = [
        "environment",
        "cluster",
        "username",
        "user_database",
        "direct_role",
        "role_database",
        "mechanisms",
        "inherited_roles",
        "inherited_privileges",
        "authentication_restrictions",
    ]

    with MongoClient(
        mongodb_uri,
        appname="mongodb-user-role-inventory",
        serverSelectionTimeoutMS=15000,
    ) as client:
        client.admin.command("ping")

        # MongoDB does not allow showPrivileges with the all-users form.
        summary_result = client.admin.command(
            {
                "usersInfo": {"forAllDBs": True},
                "showCredentials": False,
            }
        )

        users = sorted(
            summary_result.get("users", []),
            key=lambda item: (item.get("db", ""), item.get("user", "")),
        )

        with output_file.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=columns)
            writer.writeheader()

            for summary in users:
                username = summary["user"]
                user_database = summary["db"]

                detail_result = client[user_database].command(
                    {
                        "usersInfo": {
                            "user": username,
                            "db": user_database,
                        },
                        "showCredentials": False,
                        "showPrivileges": True,
                        "showAuthenticationRestrictions": True,
                    }
                )

                detailed_users = detail_result.get("users", [])
                if not detailed_users:
                    continue

                user = detailed_users[0]
                direct_roles = user.get("roles") or [{}]

                for role in direct_roles:
                    writer.writerow(
                        {
                            "environment": environment,
                            "cluster": cluster,
                            "username": username,
                            "user_database": user_database,
                            "direct_role": role.get("role", ""),
                            "role_database": role.get("db", ""),
                            "mechanisms": json_cell(user.get("mechanisms")),
                            "inherited_roles": json_cell(
                                user.get("inheritedRoles")
                            ),
                            "inherited_privileges": json_cell(
                                user.get("inheritedPrivileges")
                            ),
                            "authentication_restrictions": json_cell(
                                user.get("authenticationRestrictions")
                            ),
                        }
                    )

    os.chmod(output_file, 0o600)
    print(f"Exported {len(users)} users to {output_file}")


if __name__ == "__main__":
    main()

