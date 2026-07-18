#!/usr/bin/env bash

set -euo pipefail

WORK_ROOT="${HOME}/work"
REPOS_ROOT="${WORK_ROOT}/repos"
MIGRATION_REPO="${REPOS_ROOT}/oracle-to-mongodb-glue"
MONGODB_OPS_REPO="${REPOS_ROOT}/mongodb-enterprise-ops"

create_file_if_missing() {
    local target="$1"
    if [[ -e "$target" ]]; then
        printf 'Preserved existing file: %s\n' "$target"
        return
    fi
    cat > "$target"
    printf 'Created file: %s\n' "$target"
}

create_directories() {
    mkdir -p \
        "${WORK_ROOT}/scratch" \
        "${WORK_ROOT}/data" \
        "${WORK_ROOT}/logs" \
        "${MIGRATION_REPO}/glue_jobs/full_load" \
        "${MIGRATION_REPO}/glue_jobs/cdc" \
        "${MIGRATION_REPO}/glue_jobs/validation" \
        "${MIGRATION_REPO}/glue_jobs/reconciliation" \
        "${MIGRATION_REPO}/src/oracle_to_mongodb/extraction" \
        "${MIGRATION_REPO}/src/oracle_to_mongodb/transformation" \
        "${MIGRATION_REPO}/src/oracle_to_mongodb/loading" \
        "${MIGRATION_REPO}/src/oracle_to_mongodb/validation" \
        "${MIGRATION_REPO}/src/oracle_to_mongodb/reconciliation" \
        "${MIGRATION_REPO}/src/oracle_to_mongodb/common" \
        "${MIGRATION_REPO}/sql/oracle/source_discovery" \
        "${MIGRATION_REPO}/sql/oracle/validation" \
        "${MIGRATION_REPO}/sql/oracle/reconciliation" \
        "${MIGRATION_REPO}/mongodb/collection_designs" \
        "${MIGRATION_REPO}/mongodb/indexes" \
        "${MIGRATION_REPO}/mongodb/validation" \
        "${MIGRATION_REPO}/mappings/tables_to_collections" \
        "${MIGRATION_REPO}/mappings/field_mappings" \
        "${MIGRATION_REPO}/tests/unit" \
        "${MIGRATION_REPO}/tests/integration" \
        "${MIGRATION_REPO}/samples/sanitized" \
        "${MIGRATION_REPO}/docs/architecture" \
        "${MIGRATION_REPO}/docs/migration_runbooks" \
        "${MIGRATION_REPO}/docs/decisions" \
        "${MONGODB_OPS_REPO}/scripts/health_checks" \
        "${MONGODB_OPS_REPO}/scripts/replica_sets" \
        "${MONGODB_OPS_REPO}/scripts/users_and_roles" \
        "${MONGODB_OPS_REPO}/scripts/indexes" \
        "${MONGODB_OPS_REPO}/scripts/performance" \
        "${MONGODB_OPS_REPO}/scripts/backups" \
        "${MONGODB_OPS_REPO}/scripts/maintenance" \
        "${MONGODB_OPS_REPO}/scripts/diagnostics" \
        "${MONGODB_OPS_REPO}/ops_manager/api" \
        "${MONGODB_OPS_REPO}/ops_manager/automation" \
        "${MONGODB_OPS_REPO}/ops_manager/monitoring" \
        "${MONGODB_OPS_REPO}/ops_manager/backup" \
        "${MONGODB_OPS_REPO}/src/mongodb_ops/connections" \
        "${MONGODB_OPS_REPO}/src/mongodb_ops/reporting" \
        "${MONGODB_OPS_REPO}/src/mongodb_ops/common" \
        "${MONGODB_OPS_REPO}/provisioning/ansible" \
        "${MONGODB_OPS_REPO}/provisioning/terraform" \
        "${MONGODB_OPS_REPO}/tests/unit" \
        "${MONGODB_OPS_REPO}/tests/integration" \
        "${MONGODB_OPS_REPO}/samples/sanitized" \
        "${MONGODB_OPS_REPO}/docs/runbooks"
}

create_python_package_markers() {
    local directory
    while IFS= read -r directory; do
        touch "${directory}/__init__.py"
    done < <(find "${MIGRATION_REPO}/src/oracle_to_mongodb" \
                   "${MONGODB_OPS_REPO}/src/mongodb_ops" \
                   -type d -print)
}

create_git_placeholders() {
    local directory
    while IFS= read -r directory; do
        if [[ -z "$(find "$directory" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
            touch "${directory}/.gitkeep"
        fi
    done < <(find "$MIGRATION_REPO" "$MONGODB_OPS_REPO" -type d -print)
}

create_migration_readme() {
    create_file_if_missing "${MIGRATION_REPO}/README.md" <<'EOF'
# Oracle-to-MongoDB Migration with AWS Glue

## Purpose

This repository contains AWS Glue Python/PySpark code used to migrate Oracle data to a self-managed MongoDB Enterprise deployment on AWS EC2.

The repository supports:

- One-time full loads.
- Temporary CDC processing during the migration window.
- Relational-to-document transformations, including embedding data from multiple Oracle tables.
- Source-to-target validation and reconciliation.
- MongoDB collection design and index definitions required by the migration.

It does not contain general Oracle database administration or infrastructure-as-code for AWS resources.

## Structure

| Path | Purpose |
| --- | --- |
| `glue_jobs/full_load` | AWS Glue entry-point jobs for initial loads. |
| `glue_jobs/cdc` | AWS Glue entry-point jobs for change processing. |
| `glue_jobs/validation` | Jobs that validate source and target results. |
| `glue_jobs/reconciliation` | Jobs that compare counts, keys, and business totals. |
| `src/oracle_to_mongodb` | Reusable Python/PySpark migration modules. |
| `sql/oracle/source_discovery` | Oracle metadata and source-discovery SQL. |
| `sql/oracle/validation` | Oracle-side validation SQL. |
| `sql/oracle/reconciliation` | Oracle-side reconciliation SQL. |
| `mongodb/collection_designs` | Target document models and design notes. |
| `mongodb/indexes` | MongoDB index definitions and deployment scripts. |
| `mongodb/validation` | MongoDB-side validation queries and scripts. |
| `mappings` | Table-to-collection and field-level mappings. |
| `tests` | Unit and integration tests. |
| `samples/sanitized` | Small sanitized test inputs only. |
| `docs` | Architecture decisions and migration runbooks. |

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Add project dependencies to `pyproject.toml` when the initial Glue job is created.

## Credentials

- Use the AWS CLI configuration under `~/.aws` for local AWS access.
- Use AWS IAM roles or SSO instead of long-lived access keys where available.
- Retrieve Oracle and MongoDB credentials from AWS Secrets Manager when Glue runs.
- If local credential files are unavoidable, keep them under `~/.config/db-work`, restrict them to mode `600`, and never commit them.

## Repository rules

- Never commit production data, connection strings, passwords, certificates, or AWS keys.
- Keep Glue entry points small; reusable logic belongs under `src/oracle_to_mongodb`.
- Store only sanitized and non-sensitive examples under `samples/sanitized`.
- Name migration artifacts for their source schema/table and target database/collection where practical.
EOF
}

create_mongodb_ops_readme() {
    create_file_if_missing "${MONGODB_OPS_REPO}/README.md" <<'EOF'
# MongoDB Enterprise Operations

## Purpose

This repository contains day-to-day operational scripts for self-managed MongoDB Enterprise servers running on AWS EC2 and managed through MongoDB Ops Manager.

It covers MongoDB and Ops Manager administration only. It does not contain Oracle administration or Oracle-to-MongoDB migration code.

## Structure

| Path | Purpose |
| --- | --- |
| `scripts/health_checks` | Availability, replication, storage, and capacity checks. |
| `scripts/replica_sets` | Replica-set inspection and administration. |
| `scripts/users_and_roles` | MongoDB user and role reporting or administration. |
| `scripts/indexes` | Index inventory, analysis, and maintenance. |
| `scripts/performance` | Profiling, slow-query, and performance analysis. |
| `scripts/backups` | Backup status and recovery-related utilities. |
| `scripts/maintenance` | Controlled operational maintenance tasks. |
| `scripts/diagnostics` | Evidence collection for troubleshooting. |
| `ops_manager/api` | Ops Manager API clients and utilities. |
| `ops_manager/automation` | Automation configuration inspection and controlled updates. |
| `ops_manager/monitoring` | Monitoring configuration and status utilities. |
| `ops_manager/backup` | Ops Manager backup configuration and status utilities. |
| `src/mongodb_ops` | Reusable Python modules shared by operational scripts. |
| `provisioning` | Optional future Ansible or Terraform for MongoDB/Ops Manager provisioning. |
| `tests` | Unit and integration tests. |
| `samples/sanitized` | Sanitized example inputs and outputs only. |
| `docs/runbooks` | Operational procedures and recovery runbooks. |

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Add project dependencies to `pyproject.toml` when the first reusable Python utility is created.

## Credentials

- Prefer OIDC, short-lived credentials, or the organization-approved secrets manager.
- If a local environment file is unavoidable, store it under `~/.config/db-work`, set mode `600`, and source it only for the required session.
- Never store MongoDB URIs, Ops Manager API keys, TLS private keys, or production hostnames in this repository.

## Repository rules

- Operational scripts should default to read-only behavior.
- Any script that changes production state must require explicit arguments identifying the target and action.
- Reusable connection, output, and reporting logic belongs under `src/mongodb_ops`.
- Never place diagnostic output or production exports in the repository; use `~/work/logs` or `~/work/data`.
- Infrastructure code under `provisioning` is optional and should be added only when that work begins.
EOF
}

create_migration_gitignore() {
    create_file_if_missing "${MIGRATION_REPO}/.gitignore" <<'EOF'
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
build/
dist/
*.egg-info/
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.jks
credentials*
secrets*
*.log
data/
output/
.idea/
.vscode/
EOF
}

create_mongodb_ops_gitignore() {
    create_file_if_missing "${MONGODB_OPS_REPO}/.gitignore" <<'EOF'
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
build/
dist/
*.egg-info/
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.jks
credentials*
secrets*
*.log
diagnostics-output/
exports/
.idea/
.vscode/
EOF
}

main() {
    create_directories
    create_python_package_markers
    create_migration_readme
    create_mongodb_ops_readme
    create_migration_gitignore
    create_mongodb_ops_gitignore
    create_git_placeholders

    printf '\nWorkspace created under %s\n' "$WORK_ROOT"
    printf 'Migration repository: %s\n' "$MIGRATION_REPO"
    printf 'MongoDB operations repository: %s\n' "$MONGODB_OPS_REPO"
}

main "$@"

