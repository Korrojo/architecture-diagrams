"""Unit tests for collection-inventory cleanup helpers."""

from __future__ import annotations

import importlib.util
import io
import logging
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import datetime, timedelta, timezone
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
SCRIPT_CANDIDATES = (
    # Layout in this public package.
    TEST_FILE.parents[1] / "collection_inventory.py",
    # Layout after deployment to the mongodb-ops repository.
    TEST_FILE.parents[3]
    / "scripts"
    / "collection-inventory"
    / "collection_inventory.py",
)
SCRIPT_PATH = next((path for path in SCRIPT_CANDIDATES if path.is_file()), None)
if SCRIPT_PATH is None:
    searched = "\n".join(f"- {path}" for path in SCRIPT_CANDIDATES)
    raise FileNotFoundError(
        "collection_inventory.py was not found in a supported layout:\n"
        f"{searched}"
    )

SPEC = importlib.util.spec_from_file_location("collection_inventory", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Unable to create an import specification for {SCRIPT_PATH}")

inventory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = inventory
SPEC.loader.exec_module(inventory)

UTC = timezone.utc


class InventoryHelpersTest(unittest.TestCase):
    """Verify pure helper behavior without connecting to MongoDB."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = inventory.load_cleanup_config(
            SCRIPT_PATH.with_name("cleanup_patterns.json")
        )

    def test_safe_name_rejects_path_traversal(self) -> None:
        with self.assertRaises(ValueError):
            inventory.safe_name("../PROD")

    def test_temp_does_not_match_template(self) -> None:
        self.assertEqual(
            inventory.match_patterns("document_template", self.config.patterns), []
        )

    def test_backup_name_matches_marker_and_date(self) -> None:
        matches = inventory.match_patterns(
            "customer_backup_20260701", self.config.patterns
        )
        self.assertEqual(
            {match.name for match in matches},
            {"backup_marker", "compact_numeric_date"},
        )

    def test_extended_temporary_collection_patterns(self) -> None:
        examples = {
            "__mongodb_migrator_tmp__1741719028811": (
                "mongodb_migrator_temporary"
            ),
            "ordersBkp04072025": "embedded_backup_suffix",
            "ordersTestV2": "camel_case_test_suffix",
            "orders_before_schemachanges": "schema_change_marker",
            "comparison-results": "comparison_or_results",
            "orders_12172025": "compact_numeric_date",
            "16Jan2026Orders": "named_month_date",
            "new": "generic_placeholder_name",
        }
        for collection_name, expected_pattern in examples.items():
            with self.subTest(collection_name=collection_name):
                matched_names = {
                    match.name
                    for match in inventory.match_patterns(
                        collection_name, self.config.patterns
                    )
                }
                self.assertIn(expected_pattern, matched_names)

    def test_test_suffix_does_not_match_ordinary_words(self) -> None:
        for collection_name in ("latest", "contest", "document_template"):
            with self.subTest(collection_name=collection_name):
                matched_names = {
                    match.name
                    for match in inventory.match_patterns(
                        collection_name, self.config.patterns
                    )
                }
                self.assertNotIn("camel_case_test_suffix", matched_names)
                self.assertNotIn("test_marker", matched_names)

    def test_removed_columns_are_not_exported(self) -> None:
        self.assertNotIn("inventory_timestamp_utc", inventory.CSV_COLUMNS)
        self.assertNotIn("index_sizes_json", inventory.CSV_COLUMNS)
        self.assertNotIn("oplog_created_at_utc", inventory.CSV_COLUMNS)
        self.assertNotIn("oplog_last_renamed_at_utc", inventory.CSV_COLUMNS)

    def test_oplog_option_is_not_available(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            inventory.parse_args([
                "--environment", "DEV",
                "--cluster", "example-cluster",
                "--check-oplog",
            ])

    def test_source_name_is_inferred(self) -> None:
        source = inventory.find_source_collection(
            "customer_backup_20260701",
            ["customer", "customer_backup_20260701"],
            self.config.patterns,
        )
        self.assertEqual(source, "customer")

    def test_size_tolerance(self) -> None:
        self.assertTrue(inventory.approximately_equal(100, 91, 10.0))
        self.assertFalse(inventory.approximately_equal(100, 89, 10.0))

    def test_log_uses_utc_format_and_restricted_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "inventory.log"
            inventory.configure_logging(log_path, "INFO")
            logging.info("inventory test message")
            for handler in logging.getLogger().handlers:
                handler.flush()

            self.assertEqual(stat.S_IMODE(log_path.stat().st_mode), 0o600)
            self.assertRegex(
                log_path.read_text(encoding="utf-8"),
                (
                    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z "
                    r"INFO inventory test message\n$"
                ),
            )

    def test_candidate_scoring(self) -> None:
        now = datetime.now(UTC)
        rows = [
            {
                "database": "example",
                "collection": "customer",
                "namespace": "example.customer",
                "document_count": 100,
                "logical_data_size_bytes": 1_000,
                "_creation_datetime": now - timedelta(days=300),
                "_statistics_available": True,
            },
            {
                "database": "example",
                "collection": "customer_backup_20260701",
                "namespace": "example.customer_backup_20260701",
                "document_count": 100,
                "logical_data_size_bytes": 990,
                "_creation_datetime": now - timedelta(days=5),
                "_statistics_available": True,
            },
        ]
        inventory.assign_candidate_metadata(
            rows, self.config, recent_cutoff=now - timedelta(days=90)
        )
        candidate = rows[1]
        self.assertTrue(candidate["matches_cleanup_pattern"])
        self.assertEqual(candidate["suspected_source_collection"], "customer")
        self.assertTrue(candidate["document_count_matches_source"])
        self.assertTrue(candidate["size_approximately_matches_source"])
        self.assertEqual(candidate["candidate_score"], 10)

    def test_candidate_storage_estimates_are_logged_by_database_and_total(self) -> None:
        candidates = [
            {
                "database": "orders",
                "total_size_bytes": 1_073_741_824,
                "_statistics_available": True,
            },
            {
                "database": "orders",
                "total_size_bytes": 536_870_912,
                "_statistics_available": True,
            },
            {
                "database": "customers",
                "total_size_bytes": 268_435_456,
                "_statistics_available": True,
            },
            {
                "database": "customers",
                "total_size_bytes": 0,
                "_statistics_available": False,
            },
        ]

        with self.assertLogs(level="INFO") as captured:
            inventory.log_candidate_storage_estimates(candidates)

        self.assertEqual(
            captured.output,
            [
                "INFO:root:===============================================",
                "INFO:root:CLEANUP CANDIDATE STORAGE ESTIMATE",
                "INFO:root:===============================================",
                "INFO:root:DATABASE                  BYTES             GiB",
                "INFO:root:-----------------------------------------------",
                "INFO:root:customers             268435456        0.250000",
                "INFO:root:orders               1610612736        1.500000",
                "INFO:root:-----------------------------------------------",
                "INFO:root:GRAND TOTAL            1879048192        1.750000",
                "INFO:root:Candidates: 4 | Statistics unavailable: 1",
                "INFO:root:===============================================",
            ],
        )


if __name__ == "__main__":
    unittest.main()
