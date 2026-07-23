# MongoDB Operations Scripts

## Purpose

The `scripts` directory contains executable MongoDB operational utilities grouped by their primary responsibility. This guide defines what belongs in each folder and prevents overlap among routine monitoring, incident diagnostics, performance work, and maintenance.

## Folder guide

| Folder | Primary purpose | Typical execution | State behavior |
| --- | --- | --- | --- |
| `backups/` | Backup status, configuration validation, restore preparation, and recovery utilities. | Scheduled checks or recovery-driven | Read-only by default; restore actions require explicit approval. |
| `cluster-sizing/` | Workload-data collection, storage calculations, growth projections, and sizing analysis. | Planning or periodic review | Read-only. |
| `collection-inventory/` | Collection metadata, storage inventory, redundancy indicators, and cleanup-candidate analysis. | Periodic governance review | Read-only; it must not drop collections. |
| `diagnostics/` | On-demand evidence collection for a specific incident or unexplained condition. | Incident-driven | Read-only by default. |
| `health-checks/` | Repeatable availability, replication, storage, capacity, and configuration checks with clear status results. | Scheduled, daily, or pre-change | Read-only. |
| `indexes/` | Index inventory, comparison, recommendations, definitions, and controlled index changes. | Periodic analysis or approved change | Mixed; create/drop operations require explicit action arguments. |
| `maintenance/` | Planned operational actions such as controlled cleanup, stepdown, compaction, or rolling procedures. | Approved maintenance window | Usually state-changing. |
| `performance/` | Slow-query, profiler, query-plan, workload, cache, and resource-efficiency analysis. | Periodic or investigation-driven | Read-only analysis by default. |
| `replica-sets/` | Replica-set inspection, member analysis, configuration reporting, and controlled administration. | Routine operations or approved change | Mixed; reconfiguration and stepdown are state-changing. |
| `users-and-roles/` | User and role inventory, privilege analysis, and controlled access administration. | Periodic review or approved access change | Mixed; inventory is read-only and grants/revocations are state-changing. |

## Category boundaries

### Health checks

Health checks answer whether a known condition is currently acceptable and normally produce a concise status:

- Is every expected replica-set member available?
- Is replication lag below the defined limit?
- Is disk utilization below the warning threshold?
- Are backup and monitoring agents reporting normally?

Place repeatable scheduled checks under `health-checks/`.

### Diagnostics

Diagnostics collect evidence needed to determine why a problem occurred. They normally produce a detailed evidence bundle rather than a simple healthy/unhealthy result:

- Current operations and lock information.
- `serverStatus` and replica-set evidence snapshots.
- Replication lag history and member-state details.
- Connection and authentication evidence.
- Configuration differences among members or clusters.
- Sanitized log evidence for a defined time window.

Place incident-oriented evidence collectors under `diagnostics/`.

### Performance

Performance utilities explain workload efficiency and support tuning decisions:

- Slow-query and profiler analysis.
- Query-plan and execution-statistics review.
- Index usage and redundancy analysis.
- WiredTiger cache and workload-pattern analysis.
- Before-and-after performance comparisons.

Place analysis under `performance/`. Put an approved index definition or index change under `indexes/`, and put a broader state-changing operational procedure under `maintenance/`.

### Maintenance

Maintenance utilities perform or coordinate planned actions that can change database state or availability:

- Controlled member stepdown.
- Rolling restart procedures.
- Approved cleanup or compaction operations.
- Maintenance-mode transitions.
- Post-maintenance verification and rollback support.

Maintenance scripts must identify the target explicitly, display the intended action, and require deliberate confirmation or an automation-safe approval flag.

### Inventory

Inventory utilities document what exists and identify objects requiring review. The collection inventory belongs in `collection-inventory/`, not `diagnostics/`, because its primary purpose is periodic governance and cleanup analysis rather than incident troubleshooting.

## Placement rule

Choose the folder that represents the script's primary outcome:

| Primary outcome | Folder |
| --- | --- |
| Routine status result | `health-checks/` |
| Incident evidence package | `diagnostics/` |
| Workload or query optimization analysis | `performance/` |
| Planned state-changing operation | `maintenance/` |
| Collection governance inventory | `collection-inventory/` |
| Index-specific inventory or change | `indexes/` |
| Replica-set-specific administration | `replica-sets/` |
| Access inventory or administration | `users-and-roles/` |

Do not place identical copies of one script in several folders. Shared implementation belongs under `src/mongodb_ops/`; each executable entry point remains in its primary folder.

## Standard script-package layout

A multi-file utility can remain self-contained within its functional folder:

```text
scripts/<area>/
├── README.md
├── <utility>.py
├── <configuration>.json
└── requirements.txt       # Only when independently installed
```

Tests remain centralized:

```text
tests/
├── unit/<area>/
└── integration/<area>/
```

Reusable Python code belongs under:

```text
src/mongodb_ops/
├── connections/
├── reporting/
└── common/
```

## Common requirements

Every operational script should:

- Default to read-only behavior.
- Accept `--environment` and `--cluster` when it connects to MongoDB.
- Load credentials from `~/.config/work`, never from the repository.
- Validate environment and cluster arguments before building file paths.
- Set a descriptive MongoDB application name.
- Use connection and operation timeouts.
- Write reports under `~/work/data/mongodb/<ENVIRONMENT>/<CLUSTER>/`.
- Write logs under `~/work/logs/mongodb/<ENVIRONMENT>/<CLUSTER>/`.
- Return a nonzero exit status on failure.
- Record per-object errors when a partial inventory can safely continue.
- Exclude credentials and sensitive document contents from logs and reports.
- Document permissions, performance impact, output fields, and examples in its README.

State-changing scripts must additionally:

- Require an explicit action rather than changing state by default.
- Identify the exact target before execution.
- Support a dry-run or preview mode when practical.
- Document prerequisites, rollback, and verification steps.
- Follow the applicable approval and change-management process.
