# Local MongoDB Change Promotion Demo

This sanitized project demonstrates a complete `DEV -> SAT -> PROD` MongoDB
change lifecycle from a local shell. It intentionally contains no GitLab
pipeline, runner, Harness, Jenkins, or other CI/CD executor.

It demonstrates:

1. Local files that mimic AWS Systems Manager Parameter Store and AWS Secrets
   Manager.
2. A local MongoDB deployment with three databases representing DEV, SAT, and
   PROD.
3. Explicit database change and rollback scripts for a collection and index.
4. Explicit Ops Manager change and rollback scripts for an authoritative
   custom role, managed user, and missing `HOST_DOWN` alert.
5. Idempotent execution, dry-run plans, verification, environment gates, and a
   `_schema_migrations` audit collection.

## Important Safety Boundary

The MongoDB databases in this sample are local simulations. The Ops Manager
scripts call the real Ops Manager URL configured in the local parameter file.
Point them only at an approved lower-environment project.

When `auth.authoritativeSet` is `true`, Ops Manager synchronizes its managed
MongoDB users and roles to every managed deployment in the project. The role
and user scripts refuse to run unless that setting is already `true`.

Ops Manager Automation Configuration updates replace the complete
configuration. The scripts re-read and compare its version before each PUT,
change only the intended object, redact output, and wait for goal state.

## Layout

```text
local-cicd-demo/
├── bin/
│   ├── deploy.sh
│   └── initialize_local_demo.sh
├── config/
│   ├── environments/{dev,sat,prod}.yml
│   └── local/*.example
├── scripts/
│   ├── database/
│   │   ├── 001_create_customers_collection.py
│   │   ├── 001_rollback_customers_collection.py
│   │   ├── 002_create_customers_email_index.py
│   │   └── 002_rollback_customers_email_index.py
│   └── ops_manager/
│       ├── 003_create_customer_reader_role.py
│       ├── 003_rollback_customer_reader_role.py
│       ├── 004_create_demo_application_user.py
│       ├── 004_rollback_demo_application_user.py
│       ├── 005_create_host_down_alert.py
│       └── 005_rollback_host_down_alert.py
├── src/mongodb_local_cicd/
├── tests/
└── docker-compose.yml
```

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

./bin/initialize_local_demo.sh
docker compose --env-file .local/docker.env up -d
```

Edit these ignored local files before calling a real Ops Manager:

```text
.local/parameter-store.json
.local/secrets-manager.json
```

The parameter file contains MongoDB URIs, Ops Manager URLs, and project IDs.
The secrets file contains MongoDB credentials and Ops Manager programmatic API
keys. No secret value belongs in an environment YAML file or log.

If Ops Manager uses a private CA, set:

```bash
export OPS_MANAGER_CA_FILE=/absolute/path/to/ca.pem
```

TLS verification cannot be disabled by this sample.

## Dry-Run Plans

All scripts default to a secret-free plan:

```bash
python scripts/database/001_create_customers_collection.py --environment dev
python scripts/ops_manager/005_create_host_down_alert.py --environment dev
```

Or plan the complete ordered change set:

```bash
./bin/deploy.sh dev plan all
```

## Apply DEV, SAT, and PROD

Database-only demonstration:

```bash
./bin/deploy.sh dev apply database
./bin/deploy.sh sat apply database
./bin/deploy.sh prod apply database --confirm PROD
```

Ops Manager lower-environment demonstration:

```bash
./bin/deploy.sh dev apply ops-manager
```

Run all changes only after both local MongoDB and the selected Ops Manager
project are configured:

```bash
./bin/deploy.sh dev apply all
```

The ordered apply sequence is collection, index, role, user, and host-down
alert. A failure stops the sequence.

## Rollback

Rollback runs in reverse dependency order:

```bash
./bin/deploy.sh dev rollback all
```

This removes the alert, removes the managed user, removes the role, drops the
index, and finally drops the empty collection. Collection rollback refuses to
drop a nonempty collection or one with unexpected indexes.

Production-simulation rollback requires confirmation:

```bash
./bin/deploy.sh prod rollback database --confirm PROD
```

## Migration History

Each environment database contains its own `_schema_migrations` collection.
Successful database apply and rollback operations record:

- change ID and description
- apply-script SHA-256 checksum
- status: `applied` or `rolled_back`
- timestamps and execution identity
- whether the change actually created the object
- rollback-script checksum and result

An applied change whose script checksum has changed is rejected.

## Validation

```bash
ruff check .
pytest
```

## Demonstration Notes

- The example MongoDB password is local-only and must not be reused.
- Replace all Ops Manager placeholder values locally.
- The `HOST_DOWN` alert sends project notifications to `GROUP_OWNER` after a
  five-minute delay. Adjust the lower-environment recipient policy before
  applying it.
- The alert rollback stores its exact returned configuration ID under
  `.local/state/<environment>/` and verifies the configuration fingerprint
  before deletion.
- This project is a teaching sample, not a production deployment specification.

