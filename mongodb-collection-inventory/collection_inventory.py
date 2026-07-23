#!/usr/bin/env python3
"""Export a read-only MongoDB collection inventory and cleanup candidates.

Credentials are loaded from:
    ~/.config/work/mongodb/<ENVIRONMENT>/<CLUSTER>.env

Reports are written outside Git under:
    ~/work/data/mongodb/<ENVIRONMENT>/<CLUSTER>/
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from bson import ObjectId
from bson.timestamp import Timestamp
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError


SYSTEM_DATABASES = frozenset({"admin", "config", "local"})
UTC = timezone.utc
DEFAULT_PATTERNS_FILE = Path(__file__).with_name("cleanup_patterns.json")
CSV_COLUMNS = (
    "environment", "cluster", "database", "collection", "namespace",
    "collection_type", "collection_uuid", "server_hosts", "sharded", "capped",
    "document_count", "logical_data_size_bytes", "logical_data_size_gib",
    "storage_size_bytes", "storage_size_gib", "free_storage_size_bytes",
    "free_storage_percent", "average_document_size_bytes", "index_count",
    "index_size_bytes", "index_size_gib", "total_size_bytes", "total_size_gib",
    "index_sizes_json", "oldest_objectid_date_utc", "newest_objectid_date_utc",
    "oplog_created_at_utc", "oplog_last_renamed_at_utc", "creation_date_utc",
    "creation_date_source", "creation_date_confidence",
    "matches_cleanup_pattern", "matched_patterns", "suspected_source_collection",
    "source_collection_exists", "document_count_matches_source",
    "size_approximately_matches_source", "candidate_score",
    "inventory_timestamp_utc", "error",
)


@dataclass(frozen=True)
class CleanupPattern:
    """A named regular expression and its candidate-score weight."""

    name: str
    expression: str
    weight: int
    compiled: re.Pattern[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "compiled", re.compile(self.expression, re.IGNORECASE))


@dataclass(frozen=True)
class CleanupConfig:
    """Validated naming and comparison rules loaded from JSON."""

    patterns: tuple[CleanupPattern, ...]
    source_match_weight: int = 2
    count_match_weight: int = 1
    size_match_weight: int = 1
    recent_weight: int = 1
    size_tolerance_percent: float = 10.0


@dataclass(frozen=True)
class OplogEvent:
    """Retained collection DDL timestamps found in the replica-set oplog."""

    created_at: datetime | None = None
    renamed_at: datetime | None = None


class UTCFormatter(logging.Formatter):
    """Format every log timestamp in UTC rather than host-local time."""

    converter = time.gmtime


def positive_int(value: str) -> int:
    """Validate a positive integer supplied to argparse."""

    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def non_negative_int(value: str) -> int:
    """Validate a non-negative integer supplied to argparse."""

    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value cannot be negative")
    return parsed


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line filters and report options."""

    parser = argparse.ArgumentParser(
        description="Export MongoDB collection statistics and cleanup candidates to CSV."
    )
    parser.add_argument(
        "--environment", required=True, choices=("DEV", "SAT", "PROD"),
        help="Environment directory containing the cluster .env file.",
    )
    parser.add_argument(
        "--cluster", required=True,
        help="Cluster name and .env filename without the .env extension.",
    )
    parser.add_argument(
        "--database", action="append", dest="databases", metavar="NAME",
        help="Inventory only this database; repeat for multiple databases.",
    )
    parser.add_argument(
        "--include-system-databases", action="store_true",
        help="Include admin, config, and local (excluded by default).",
    )
    parser.add_argument(
        "--collection-regex",
        help="Inventory only collection names matching this regular expression.",
    )
    parser.add_argument(
        "--candidates-only", action="store_true",
        help="Write only cleanup_candidates CSV.",
    )
    parser.add_argument(
        "--check-oplog", action="store_true",
        help="Use retained create/rename oplog entries when authorized.",
    )
    parser.add_argument(
        "--skip-document-dates", action="store_true",
        help="Skip indexed earliest/latest ObjectId timestamp queries.",
    )
    parser.add_argument(
        "--patterns-file", type=Path, default=DEFAULT_PATTERNS_FILE,
        help=f"Cleanup-rule JSON file (default: {DEFAULT_PATTERNS_FILE}).",
    )
    parser.add_argument(
        "--recent-days", type=positive_int, default=90,
        help="Recent-collection score window (default: 90).",
    )
    parser.add_argument(
        "--score-threshold", type=non_negative_int, default=3,
        help="Minimum cleanup-candidate score (default: 3).",
    )
    parser.add_argument(
        "--max-time-ms", type=positive_int, default=15_000,
        help="Limit for each ObjectId boundary query (default: 15000).",
    )
    parser.add_argument(
        "--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO", help="Console/file logging level (default: INFO).",
    )
    return parser.parse_args(argv)


def safe_name(value: str) -> str:
    """Reject values capable of escaping the expected directory structure."""

    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError(f"Invalid environment or cluster name: {value}")
    return value


def utc_text(value: datetime | None) -> str:
    """Format an optional datetime as ISO-8601 UTC text."""

    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def gib(value: int | float | None) -> float:
    """Convert bytes to GiB, rounded for convenient CSV reading."""

    return round(float(value or 0) / (1024**3), 6)


def percentage(numerator: int | float, denominator: int | float) -> float:
    """Calculate a percentage without dividing by zero."""

    return round(float(numerator) / float(denominator) * 100, 2) if denominator else 0.0


def json_cell(value: Any) -> str:
    """Serialize a nested value deterministically into one CSV cell."""

    return json.dumps(value if value is not None else {}, default=str, sort_keys=True)


def load_cleanup_config(path: Path) -> CleanupConfig:
    """Load naming rules and scoring values from a JSON configuration file."""

    with path.expanduser().open(encoding="utf-8") as config_file:
        raw = json.load(config_file)
    items = raw.get("patterns")
    if not isinstance(items, list) or not items:
        raise ValueError("patterns must be a non-empty JSON array")
    patterns = tuple(
        CleanupPattern(str(item["name"]), str(item["expression"]), int(item["weight"]))
        for item in items
    )
    scoring = raw.get("scoring", {})
    return CleanupConfig(
        patterns=patterns,
        source_match_weight=int(scoring.get("source_match_weight", 2)),
        count_match_weight=int(scoring.get("count_match_weight", 1)),
        size_match_weight=int(scoring.get("size_match_weight", 1)),
        recent_weight=int(scoring.get("recent_weight", 1)),
        size_tolerance_percent=float(scoring.get("size_tolerance_percent", 10.0)),
    )


def configure_logging(path: Path, level_name: str) -> None:
    """Configure UTC console/file logging and secure the log file to mode 0600."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600, exist_ok=True)
    os.chmod(path, 0o600)

    formatter = UTCFormatter(
        fmt="%(asctime)s.%(msecs)03dZ %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(path, encoding="utf-8")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=getattr(logging, level_name),
        handlers=(console_handler, file_handler),
        force=True,
    )


def selected_databases(client: MongoClient[Any], args: argparse.Namespace) -> list[str]:
    """Return visible database names after applying command-line selection."""

    available = set(client.list_database_names())
    if args.databases:
        requested = set(args.databases)
        missing = sorted(requested - available)
        if missing:
            raise ValueError(f"Database(s) not found or not visible: {', '.join(missing)}")
        available = requested
    if not args.include_system_databases:
        available -= SYSTEM_DATABASES
    return sorted(available, key=str.casefold)


def extract_uuid(info: Mapping[str, Any]) -> str:
    """Convert an optional listCollections UUID into stable text."""

    value = info.get("info", {}).get("uuid")
    if value is None:
        return ""
    try:
        return str(value.as_uuid())
    except (AttributeError, ValueError):
        return str(value)


def collection_stats(collection: Collection[Any]) -> dict[str, Any]:
    """Combine one or more per-shard ``$collStats`` results."""

    documents = list(collection.aggregate([
        {"$collStats": {"storageStats": {"scale": 1}, "count": {}}}
    ]))
    if not documents:
        raise RuntimeError("$collStats returned no documents")

    totals: defaultdict[str, int] = defaultdict(int)
    index_sizes: defaultdict[str, int] = defaultdict(int)
    hosts: set[str] = set()
    capped = False
    average_numerator = 0.0
    for document in documents:
        storage = document.get("storageStats", {})
        count = int(document.get("count", storage.get("count", 0)) or 0)
        totals["document_count"] += count
        totals["logical_data_size_bytes"] += int(storage.get("size", 0) or 0)
        totals["storage_size_bytes"] += int(storage.get("storageSize", 0) or 0)
        totals["free_storage_size_bytes"] += int(storage.get("freeStorageSize", 0) or 0)
        totals["index_size_bytes"] += int(storage.get("totalIndexSize", 0) or 0)
        totals["total_size_bytes"] += int(storage.get("totalSize", 0) or 0)
        average_numerator += float(storage.get("avgObjSize", 0) or 0) * count
        capped = capped or bool(storage.get("capped", False))
        if document.get("host"):
            hosts.add(str(document["host"]))
        for name, size in storage.get("indexSizes", {}).items():
            index_sizes[str(name)] += int(size or 0)

    count = totals["document_count"]
    return {
        **totals,
        "average_document_size_bytes": round(average_numerator / count, 2) if count else 0.0,
        "index_count": len(index_sizes),
        "index_sizes": dict(sorted(index_sizes.items())),
        "server_hosts": sorted(hosts),
        "sharded": any("shard" in document for document in documents),
        "capped": capped,
    }


def objectid_time(document: Mapping[str, Any] | None) -> datetime | None:
    """Extract the generation time from a projected ObjectId document."""

    identifier = document.get("_id") if document else None
    return identifier.generation_time if isinstance(identifier, ObjectId) else None


def objectid_boundary_dates(
    collection: Collection[Any], max_time_ms: int
) -> tuple[datetime | None, datetime | None]:
    """Use the built-in ``_id`` index to find surviving ObjectId boundaries."""

    query = {"_id": {"$type": "objectId"}}
    projection = {"_id": 1}
    oldest = collection.find_one(
        query, projection, sort=[("_id", ASCENDING)], max_time_ms=max_time_ms
    )
    newest = collection.find_one(
        query, projection, sort=[("_id", DESCENDING)], max_time_ms=max_time_ms
    )
    return objectid_time(oldest), objectid_time(newest)


def timestamp_time(value: Any) -> datetime | None:
    """Convert a BSON oplog timestamp to an aware UTC datetime."""

    return value.as_datetime().replace(tzinfo=UTC) if isinstance(value, Timestamp) else None


def load_oplog_events(client: MongoClient[Any]) -> dict[str, OplogEvent]:
    """Read retained create/rename DDL events once; requires optional oplog access."""

    query = {"op": "c", "$or": [
        {"o.create": {"$exists": True}},
        {"o.renameCollection": {"$exists": True}},
    ]}
    mutable: dict[str, dict[str, datetime | None]] = defaultdict(
        lambda: {"created_at": None, "renamed_at": None}
    )
    cursor = client.local["oplog.rs"].find(query, {"ts": 1, "ns": 1, "o": 1})
    for entry in cursor.sort("$natural", 1):
        command = entry.get("o", {})
        event_time = timestamp_time(entry.get("ts"))
        database = str(entry.get("ns", "")).removesuffix(".$cmd")
        if event_time and database and command.get("create"):
            mutable[f"{database}.{command['create']}"]["created_at"] = event_time
        if event_time and command.get("renameCollection") and command.get("to"):
            mutable[str(command["to"])]["renamed_at"] = event_time
    return {name: OplogEvent(**values) for name, values in mutable.items()}


def match_patterns(name: str, patterns: Iterable[CleanupPattern]) -> list[CleanupPattern]:
    """Return every configured rule matching a collection name."""

    return [pattern for pattern in patterns if pattern.compiled.search(name)]


def infer_source_name(name: str, patterns: Iterable[CleanupPattern]) -> str:
    """Remove backup/date markers to infer the possible original collection."""

    inferred = name
    for pattern in patterns:
        inferred = pattern.compiled.sub("_", inferred)
    return re.sub(r"[._-]{2,}", "_", inferred).strip("._-")


def find_source_collection(
    candidate: str, available_names: Iterable[str], patterns: Iterable[CleanupPattern]
) -> str:
    """Resolve the inferred source name case-insensitively in the same database."""

    inferred = infer_source_name(candidate, patterns)
    if not inferred or inferred.casefold() == candidate.casefold():
        return ""
    return {name.casefold(): name for name in available_names}.get(inferred.casefold(), "")


def approximately_equal(left: int, right: int, tolerance_percent: float) -> bool:
    """Compare sizes using the larger nonzero value as the baseline."""

    if left < 0 or right < 0:
        return False
    if left == right:
        return True
    baseline = max(left, right)
    return bool(baseline and abs(left - right) / baseline * 100 <= tolerance_percent)


def assign_candidate_metadata(
    rows: list[dict[str, Any]], config: CleanupConfig, recent_cutoff: datetime
) -> None:
    """Calculate naming evidence, source comparisons, and review score in place."""

    names_by_database: defaultdict[str, list[str]] = defaultdict(list)
    by_namespace: dict[str, dict[str, Any]] = {}
    for row in rows:
        names_by_database[row["database"]].append(row["collection"])
        by_namespace[row["namespace"]] = row

    for row in rows:
        matches = match_patterns(row["collection"], config.patterns)
        source_name = find_source_collection(
            row["collection"], names_by_database[row["database"]], config.patterns
        )
        source = by_namespace.get(f"{row['database']}.{source_name}")
        statistics_available = bool(row.get("_statistics_available", False))
        source_statistics_available = bool(source and source.get("_statistics_available", False))
        count_matches = bool(
            source and statistics_available and source_statistics_available
            and int(row["document_count"]) == int(source["document_count"])
        )
        size_matches = bool(
            source and statistics_available and source_statistics_available
            and approximately_equal(
                int(row["logical_data_size_bytes"]),
                int(source["logical_data_size_bytes"]),
                config.size_tolerance_percent,
            )
        )
        score = sum(pattern.weight for pattern in matches)
        if source:
            score += config.source_match_weight
        if count_matches:
            score += config.count_match_weight
        if size_matches:
            score += config.size_match_weight
        creation_date = row.pop("_creation_datetime", None)
        if matches and creation_date and creation_date >= recent_cutoff:
            score += config.recent_weight
        row.update({
            "matches_cleanup_pattern": bool(matches),
            "matched_patterns": ",".join(pattern.name for pattern in matches),
            "suspected_source_collection": source_name,
            "source_collection_exists": bool(source),
            "document_count_matches_source": count_matches,
            "size_approximately_matches_source": size_matches,
            "candidate_score": score,
        })

    # Internal calculation keys are never written to CSV.
    for row in rows:
        row.pop("_statistics_available", None)


def empty_row(
    environment: str, cluster: str, database: str,
    info: Mapping[str, Any], inventory_time: datetime,
) -> dict[str, Any]:
    """Build a complete default row before optional metrics are populated."""

    collection = str(info["name"])
    row = {column: "" for column in CSV_COLUMNS}
    row.update({
        "environment": environment, "cluster": cluster, "database": database,
        "collection": collection, "namespace": f"{database}.{collection}",
        "collection_type": info.get("type", "collection"),
        "collection_uuid": extract_uuid(info),
        "sharded": False, "capped": bool(info.get("options", {}).get("capped", False)),
        "document_count": 0, "logical_data_size_bytes": 0,
        "logical_data_size_gib": 0.0, "storage_size_bytes": 0,
        "storage_size_gib": 0.0, "free_storage_size_bytes": 0,
        "free_storage_percent": 0.0, "average_document_size_bytes": 0.0,
        "index_count": 0, "index_size_bytes": 0, "index_size_gib": 0.0,
        "total_size_bytes": 0, "total_size_gib": 0.0,
        "index_sizes_json": "{}", "matches_cleanup_pattern": False,
        "source_collection_exists": False, "document_count_matches_source": False,
        "size_approximately_matches_source": False, "candidate_score": 0,
        "inventory_timestamp_utc": utc_text(inventory_time),
        "_statistics_available": False,
    })
    return row


def inventory_collection(
    database: Database[Any], info: Mapping[str, Any], environment: str, cluster: str,
    inventory_time: datetime, oplog_event: OplogEvent,
    skip_document_dates: bool, max_time_ms: int,
) -> dict[str, Any]:
    """Collect one row and preserve partial results when one operation fails."""

    row = empty_row(environment, cluster, database.name, info, inventory_time)
    collection = database[row["collection"]]
    errors: list[str] = []

    # Views have no independent storage and reject storageStats.
    if row["collection_type"] != "view":
        try:
            stats = collection_stats(collection)
            storage_size = stats["storage_size_bytes"]
            free_storage = stats["free_storage_size_bytes"]
            row.update({
                "server_hosts": ",".join(stats["server_hosts"]),
                "sharded": stats["sharded"], "capped": stats["capped"],
                "document_count": stats["document_count"],
                "logical_data_size_bytes": stats["logical_data_size_bytes"],
                "logical_data_size_gib": gib(stats["logical_data_size_bytes"]),
                "storage_size_bytes": storage_size, "storage_size_gib": gib(storage_size),
                "free_storage_size_bytes": free_storage,
                "free_storage_percent": percentage(free_storage, storage_size),
                "average_document_size_bytes": stats["average_document_size_bytes"],
                "index_count": stats["index_count"],
                "index_size_bytes": stats["index_size_bytes"],
                "index_size_gib": gib(stats["index_size_bytes"]),
                "total_size_bytes": stats["total_size_bytes"],
                "total_size_gib": gib(stats["total_size_bytes"]),
                "index_sizes_json": json_cell(stats["index_sizes"]),
                "_statistics_available": True,
            })
        except (PyMongoError, RuntimeError, TypeError, ValueError) as exc:
            errors.append(f"statistics: {type(exc).__name__}: {exc}")

    oldest: datetime | None = None
    newest: datetime | None = None
    if not skip_document_dates and row["collection_type"] == "collection":
        try:
            oldest, newest = objectid_boundary_dates(collection, max_time_ms)
        except PyMongoError as exc:
            errors.append(f"document_dates: {type(exc).__name__}: {exc}")

    # Oplog create time is exact while retained; ObjectId time is only an estimate.
    creation_date = oplog_event.created_at or oldest
    source = "oplog_create_event" if oplog_event.created_at else ""
    confidence = "high" if oplog_event.created_at else ""
    if not source and oldest:
        source, confidence = "earliest_objectid", "low"
    row.update({
        "oldest_objectid_date_utc": utc_text(oldest),
        "newest_objectid_date_utc": utc_text(newest),
        "oplog_created_at_utc": utc_text(oplog_event.created_at),
        "oplog_last_renamed_at_utc": utc_text(oplog_event.renamed_at),
        "creation_date_utc": utc_text(creation_date),
        "creation_date_source": source, "creation_date_confidence": confidence,
        "_creation_datetime": creation_date, "error": " | ".join(errors),
    })
    return row


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    """Write a restricted-permission CSV and return the number of data rows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})
            count += 1
    os.chmod(path, 0o600)
    return count


def run(args: argparse.Namespace) -> tuple[Path | None, Path, int, int]:
    """Run discovery, collection, scoring, sorting, and CSV generation."""

    environment, cluster = safe_name(args.environment), safe_name(args.cluster)
    config = load_cleanup_config(args.patterns_file)
    env_file = Path.home() / ".config" / "work" / "mongodb" / environment / f"{cluster}.env"
    if not env_file.is_file():
        raise FileNotFoundError(f"Credential file not found: {env_file}")
    load_dotenv(env_file, override=True)
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise RuntimeError(f"MONGODB_URI is missing from {env_file}")

    inventory_time = datetime.now(UTC)
    timestamp = inventory_time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path.home() / "work" / "data" / "mongodb" / environment / cluster
    log_file = (
        Path.home() / "work" / "logs" / "mongodb" / environment / cluster
        / f"collection_inventory_{timestamp}.log"
    )
    configure_logging(log_file, args.log_level)
    logging.info("Starting inventory environment=%s cluster=%s", environment, cluster)
    collection_filter = re.compile(args.collection_regex) if args.collection_regex else None

    rows: list[dict[str, Any]] = []
    with MongoClient(
        mongodb_uri, appname="mongodb-collection-inventory",
        serverSelectionTimeoutMS=15_000, connectTimeoutMS=15_000,
    ) as client:
        client.admin.command("ping")
        oplog_events: dict[str, OplogEvent] = {}
        if args.check_oplog:
            try:
                oplog_events = load_oplog_events(client)
                logging.info("Loaded retained oplog DDL for %d namespaces", len(oplog_events))
            except PyMongoError as exc:
                logging.warning("Oplog lookup unavailable: %s: %s", type(exc).__name__, exc)

        for database_name in selected_databases(client, args):
            database = client[database_name]
            logging.info("Inventorying database=%s", database_name)
            infos = sorted(database.list_collections(), key=lambda item: str(item["name"]).casefold())
            for info in infos:
                collection_name = str(info["name"])
                if collection_filter and not collection_filter.search(collection_name):
                    continue
                namespace = f"{database_name}.{collection_name}"
                rows.append(inventory_collection(
                    database, info, environment, cluster, inventory_time,
                    oplog_events.get(namespace, OplogEvent()),
                    args.skip_document_dates, args.max_time_ms,
                ))

    assign_candidate_metadata(
        rows, config, inventory_time - timedelta(days=args.recent_days)
    )
    rows.sort(key=lambda row: (row["database"].casefold(), row["collection"].casefold()))
    candidates = [row for row in rows if int(row["candidate_score"]) >= args.score_threshold]
    candidates.sort(key=lambda row: (
        -int(row["candidate_score"]), row["database"].casefold(), row["collection"].casefold()
    ))

    inventory_path: Path | None = None
    if not args.candidates_only:
        inventory_path = output_dir / f"collection_inventory_{timestamp}.csv"
        write_csv(inventory_path, rows)
    candidate_path = output_dir / f"cleanup_candidates_{timestamp}.csv"
    write_csv(candidate_path, candidates)
    logging.info("Completed collections=%d candidates=%d", len(rows), len(candidates))
    return inventory_path, candidate_path, len(rows), len(candidates)


def main() -> int:
    """CLI entry point with concise errors and a nonzero failure status."""

    try:
        inventory_path, candidate_path, rows, candidates = run(parse_args())
    except (FileNotFoundError, ValueError, RuntimeError, OSError, PyMongoError, re.error) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if inventory_path:
        print(f"Inventory: {inventory_path} ({rows} collections)")
    print(f"Candidates: {candidate_path} ({candidates} collections)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
