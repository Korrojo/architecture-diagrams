# MongoDB Collection Inventory and Cleanup Candidate Report

## Purpose

This read-only Python utility inventories collections across a self-managed MongoDB deployment and produces CSV reports for preliminary database-cleanup analysis. It highlights names that resemble backups, copies, temporary collections, archives, restores, snapshots, or date-stamped duplicates.

The report provides evidence for review. The script never drops, renames, updates, inserts, or deletes anything. A candidate score is not approval to delete a collection.

## Package contents

| File | Purpose |
| --- | --- |
| `collection_inventory.py` | Main command-line inventory and analysis program. |
| `cleanup_patterns.json` | Configurable naming rules, comparison tolerance, and scoring weights. |
| `requirements.txt` | Runtime Python dependencies. |
| `tests/test_collection_inventory.py` | Unit tests for validation, matching, inference, comparison, and scoring. |

## Existing workspace conventions

The utility follows the same environment and cluster conventions as `wsl-db-workspace/export_users_roles.py`.

Credential file selected by `--environment` and `--cluster`:

```text
~/.config/work/mongodb/<ENVIRONMENT>/<CLUSTER>.env
```

CSV output:

```text
~/work/data/mongodb/<ENVIRONMENT>/<CLUSTER>/
```

Log output:

```text
~/work/logs/mongodb/<ENVIRONMENT>/<CLUSTER>/
```

The output and log directories are created automatically. Credentials, reports, and logs remain outside Git. CSV and log files are restricted to permission mode `600`.

Log filename:

```text
collection_inventory_YYYYMMDD_HHMMSS.log
```

The filename and every log-record timestamp use UTC. Log records use:

```text
YYYY-MM-DDTHH:MM:SS.mmmZ LEVEL Message
```

Example:

```text
2026-07-23T14:25:30.118Z INFO Starting inventory environment=PROD cluster=example-cluster
```

The final log entries show estimated potential space freed for each database
containing candidates, followed by a grand total:

```text
2026-07-23T14:26:12.441Z INFO Estimated potential space freed database=application_database bytes=1610612736 gib=1.500000
2026-07-23T14:26:12.441Z INFO Estimated potential space freed grand_total bytes=1610612736 gib=1.500000 candidates=3 statistics_unavailable=0
```

The estimate sums `total_size_bytes`, which includes allocated collection and
index storage. It excludes candidates whose collection statistics failed.
`free_storage_size_bytes` is already part of allocated storage and is not added
again. The estimate is intended for cleanup planning and does not guarantee the
exact filesystem space returned after a collection is dropped.

## Recommended location in the operations repository

Copy the executable and supporting files to:

```text
~/work/repos/mongodb-ops/scripts/collection-inventory/
```

Place the test in the repository's central test structure:

```text
~/work/repos/mongodb-ops/tests/unit/collection-inventory/test_collection_inventory.py
```

## Requirements

- Python 3.10 or later.
- MongoDB 6.2 or later is recommended because the script uses `$collStats`.
- Network connectivity from WSL to MongoDB.
- Permission to list visible databases and collections, run collection statistics, and query collection `_id` values.

## Installation

From the MongoDB operations repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install \
  -r scripts/collection-inventory/requirements.txt
```

On a managed network, use only the organization's approved proxy, certificate, or internal package mirror. The existing `wsl-db-workspace/APT_AND_PIP.md` contains the established WSL guidance.

## Environment file

Create the cluster file outside Git:

```text
~/.config/work/mongodb/DEV/example-cluster.env
```

Example:

```bash
MONGODB_URI='mongodb://username:password@host1,host2,host3/?authSource=admin&replicaSet=exampleReplicaSet'
```

Secure it:

```bash
chmod 600 ~/.config/work/mongodb/DEV/example-cluster.env
```

The URI is never written to a report or log. Use the organization's approved authentication and secrets-management method where available.

## Basic use

Inventory every non-system database visible to the account:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment DEV \
  --cluster example-cluster
```

The default run excludes `admin`, `config`, and `local` and writes:

```text
collection_inventory_<UTC timestamp>.csv
cleanup_candidates_<UTC timestamp>.csv
```

Both CSV files are created with permission mode `600`.

The terminal prints every generated location:

```text
Inventory: /home/user/work/data/mongodb/DEV/example-cluster/collection_inventory_20260723_142530.csv (185 collections)
Candidates: /home/user/work/data/mongodb/DEV/example-cluster/cleanup_candidates_20260723_142530.csv (11 collections)
Log folder: /home/user/work/logs/mongodb/DEV/example-cluster
Log file: /home/user/work/logs/mongodb/DEV/example-cluster/collection_inventory_20260723_142530.log
```

## Filtering and diagnostic options

Inventory one database:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment SAT \
  --cluster example-cluster \
  --database application_database
```

Repeat `--database` for several databases:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment SAT \
  --cluster example-cluster \
  --database application_one \
  --database application_two
```

Limit collection names using a regular expression:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment PROD \
  --cluster example-cluster \
  --collection-regex '(?i)(backup|bak|bkp|copy|clone|temp|tmp|archive|old)'
```

Write only the candidate report:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment PROD \
  --cluster example-cluster \
  --candidates-only
```

Include system databases explicitly:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment DEV \
  --cluster example-cluster \
  --include-system-databases
```

Skip earliest/latest ObjectId lookups for the fastest metadata-only run:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment DEV \
  --cluster example-cluster \
  --skip-document-dates
```

Other controls:

```text
--patterns-file PATH       Use an approved custom JSON rules file.
--recent-days NUMBER       Recent-collection scoring window; default 90.
--score-threshold NUMBER   Candidate CSV minimum score; default 3.
--max-time-ms NUMBER       Each ObjectId boundary query limit; default 15000.
--log-level LEVEL          DEBUG, INFO, WARNING, or ERROR.
```

Display the complete CLI help:

```bash
python scripts/collection-inventory/collection_inventory.py --help
```

## CSV fields

### Identity and topology

| Columns | Meaning |
| --- | --- |
| `environment`, `cluster` | Values supplied on the command line. |
| `database`, `collection`, `namespace` | MongoDB object identity. |
| `collection_type` | Collection, view, time-series, or other server-reported type. |
| `collection_uuid` | UUID returned by `listCollections`, when available. |
| `server_hosts` | Nodes or shards returning collection statistics. |
| `sharded`, `capped` | Server-reported collection characteristics. |

### Volume and storage

| Columns | Meaning |
| --- | --- |
| `document_count` | Metadata-based document count returned by `$collStats`. |
| `logical_data_size_bytes`, `logical_data_size_gib` | Logical document data before storage-engine compression. |
| `storage_size_bytes`, `storage_size_gib` | Allocated collection storage. |
| `free_storage_size_bytes`, `free_storage_percent` | Reusable space within allocated storage. |
| `average_document_size_bytes` | Average logical BSON document size. |
| `index_count` | Number of unique index names. |
| `index_size_bytes`, `index_size_gib` | Total allocated index storage. |
| `total_size_bytes`, `total_size_gib` | Collection storage plus index storage. |

Byte columns are authoritative. GiB values are rounded to six decimal places.

### Date evidence

| Column | Meaning |
| --- | --- |
| `oldest_objectid_date_utc` | Generation time in the smallest surviving ObjectId. |
| `newest_objectid_date_utc` | Generation time in the largest surviving ObjectId. |
| `creation_date_utc` | Oldest surviving ObjectId timestamp estimate, when available. |
| `creation_date_source` | `earliest_objectid` or blank. |
| `creation_date_confidence` | `low` or blank. |

MongoDB does not normally expose a durable collection creation timestamp. An ObjectId timestamp describes when the identifier was generated, not necessarily when its collection was created or its document inserted. Restores, copies, deletions, custom `_id` values, and pre-generated ObjectIds can make the estimate inaccurate. Collections without surviving ObjectId `_id` values have blank date fields.

### Candidate analysis

| Column | Meaning |
| --- | --- |
| `matches_cleanup_pattern` | Whether a configured naming rule matched. |
| `matched_patterns` | Comma-separated matching rule names. |
| `suspected_source_collection` | Candidate name after configured markers are removed. |
| `source_collection_exists` | Whether the inferred source exists in the same selected database. |
| `document_count_matches_source` | Exact count comparison when both statistics succeeded. |
| `size_approximately_matches_source` | Logical-size comparison using configured tolerance. |
| `candidate_score` | Evidence-weight sum for review prioritization. |
| `error` | Per-collection failures; partial metadata remains in the row. |

## Default rules and scoring

Rules cover separator-delimited markers, camel-case suffixes, migration artifacts, schema-change copies, comparison outputs, and several common date encodings. Case-sensitive rules are used where necessary to avoid ordinary-name false positives. For example, `ordersTestV2` is flagged while `latest` is not.

| Evidence | Weight |
| --- | ---: |
| MongoDB Relational Migrator temporary name such as `__mongodb_migrator_tmp__1234567890` | 5 |
| `_backup`, `-bak`, `.bkp` marker | 3 |
| Embedded backup suffix such as `ordersBkp04072025` or `orders_backuptest` | 4 |
| `_copy` or `-clone` marker | 3 |
| `_temp` or `-tmp` marker | 3 |
| Test prefix or separator-delimited test marker | 3 |
| Camel-case test suffix such as `ordersTestV2` | 3 |
| `_archive`, `_old`, `_restore`, or `_snapshot` marker | 3 |
| Migration, migrator, migration-job, migration-collection, `mig`, or dump marker | 3 |
| Comparison, compare, or results marker | 3 |
| Legacy marker | 3 |
| Delta marker | 2 |
| `before_schemachanges` or `newschema` marker | 4 |
| Exact placeholder name `new` or `collection` | 3 |
| Compact `YYYYMMDD` or `MMDDYYYY` date embedded in a name | 2 |
| Named-month date such as `16Jan2026` or `Jan2026` | 2 |
| Segmented month/year such as `_02_24` or `-5-27` | 1 |
| Inferred source collection exists | 2 |
| Document count equals source | 1 |
| Logical size is within 10% of source | 1 |
| Matched collection appears created within `--recent-days` | 1 |

The default candidate threshold is `3`. A date suffix alone therefore remains in the full inventory but is not a candidate unless supported by additional evidence.

## Custom rules

Edit a controlled copy of `cleanup_patterns.json`, then supply it:

```bash
python scripts/collection-inventory/collection_inventory.py \
  --environment DEV \
  --cluster example-cluster \
  --patterns-file /approved/path/cleanup_patterns.json
```

Each rule requires `name`, a Python-compatible regular-expression `expression`, and an integer `weight`. The optional `case_sensitive` field defaults to `false`. Test additions against legitimate collection names to limit false positives.

## Processing and performance

- `list_database_names()` discovers databases visible to the account.
- `list_collections()` retrieves names, types, options, and UUIDs.
- `$collStats` retrieves counts and storage measurements without scanning all documents.
- Earliest/latest ObjectId queries use the `_id` index and a configurable time limit.
- Views are listed but do not receive storage-statistics requests.
- Failures are captured per collection so the remaining inventory continues.
- WiredTiger diagnostic internals, document bodies, credentials, and URIs are excluded.

On a sharded cluster, `$collStats` can return one result per shard. The script sums byte and count measurements, combines index sizes by name, and marks the row as sharded.

When `--collection-regex` is used, inferred-source comparison is limited to collections included by that filter. Run the full inventory for the strongest comparison results.

## Review procedure

1. Preserve the full inventory CSV as the baseline.
2. Review candidates in descending `candidate_score` order.
3. Compare candidate and suspected-source names, counts, sizes, indexes, ownership, and application dependencies.
4. Confirm retention, legal hold, backup, restore, and change-management requirements.
5. Obtain application-owner and DBA approval before any separate cleanup operation.

This package intentionally contains no automated drop operation.

## Testing

After installing the requirements:

```bash
python -m unittest discover \
  -s tests/unit/collection-inventory \
  -v
```

The tests do not connect to MongoDB.

Syntax-only validation:

```bash
python -m py_compile \
  scripts/collection-inventory/collection_inventory.py
```

## Security and sanitization

- Keep `.env` files under `~/.config/work`, never under `~/work/repos`.
- Keep generated CSV and logs under `~/work/data` and `~/work/logs`.
- Generated inventories contain real database, collection, host, and index names; treat them as internal operational data.
- Never publish generated reports, URIs, hostnames, usernames, certificates, or credentials.
- This public package contains only generic names and values.
