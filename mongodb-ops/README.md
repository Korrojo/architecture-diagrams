# MongoDB Ops

## Purpose

This repository contains day-to-day operational scripts and documentation for self-managed MongoDB Enterprise deployments managed through MongoDB Ops Manager.

The repository is organized by operational responsibility so that routine checks, troubleshooting tools, performance analysis, and state-changing maintenance are not mixed together.

## Structure

| Path | Purpose |
| --- | --- |
| [`scripts/`](scripts/README.md) | Operational scripts grouped by function, with placement and safety guidance. |
| `ops_manager/api/` | Ops Manager API clients and reusable utilities. |
| `ops_manager/automation/` | Automation configuration inspection and controlled updates. |
| `ops_manager/monitoring/` | Monitoring configuration and status utilities. |
| `ops_manager/backup/` | Ops Manager backup configuration and status utilities. |
| `src/mongodb_ops/` | Reusable Python modules shared by operational scripts. |
| `provisioning/` | Optional Ansible or Terraform for MongoDB and Ops Manager provisioning. |
| `tests/unit/` | Fast tests for individual functions and modules. |
| `tests/integration/` | Tests requiring a controlled MongoDB environment. |
| `samples/sanitized/` | Generic example inputs and outputs only. |
| `docs/runbooks/` | Operational procedures, decisions, recovery instructions, and change runbooks. |

See [`scripts/README.md`](scripts/README.md) for the distinction among health checks, diagnostics, performance analysis, maintenance, inventory, and other script categories.

## Organization principles

- Organize scripts by their primary operational purpose, not every purpose they could potentially serve.
- Keep routine health reporting separate from incident evidence collection.
- Keep analysis and recommendations separate from state-changing maintenance.
- Put reusable connection, validation, output, and reporting logic under `src/mongodb_ops/` instead of copying it among scripts.
- Keep unit and integration tests under the repository-level `tests/` directory.
- Keep generated reports, logs, credentials, and real environment data outside Git.

## Local setup

```bash
cd ~/work/repos/mongodb-ops
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Project-wide dependencies should be declared in the repository's Python project configuration when shared packaging is introduced. A self-contained script package may temporarily retain a local `requirements.txt` when it must be copied or installed independently.

## Environment and credentials

Cluster environment files are stored outside the repository:

```text
~/.config/work/mongodb/<ENVIRONMENT>/<CLUSTER>.env
```

Example command convention:

```bash
python scripts/<area>/<script>.py \
  --environment DEV \
  --cluster example-cluster
```

Requirements:

- Prefer OIDC, short-lived credentials, or the organization-approved secrets manager.
- Restrict unavoidable local environment files to the owning user.
- Never commit MongoDB URIs, passwords, certificates, private keys, internal hostnames, or Ops Manager API keys.

## Generated output

Generated files must remain outside the repository:

```text
~/work/data/mongodb/<ENVIRONMENT>/<CLUSTER>/
~/work/logs/mongodb/<ENVIRONMENT>/<CLUSTER>/
```

## Repository rules

- Operational scripts default to read-only behavior.
- State-changing operations require explicit target and action arguments.
- Production changes require the applicable approval and change-management process.
- Scripts must not silently continue against a different environment or cluster.
- Examples and test fixtures must be sanitized and contain no identifying system information.
- Do not commit generated inventories, diagnostic bundles, database exports, or application data.
