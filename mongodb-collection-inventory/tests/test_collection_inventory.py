"""Unit tests for collection-inventory cleanup helpers."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
import collection_inventory as inventory  # noqa: E402

UTC = timezone.utc


class InventoryHelpersTest(unittest.TestCase):
    """Verify pure helper behavior without connecting to MongoDB."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = inventory.load_cleanup_config(PROJECT_DIR / "cleanup_patterns.json")

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
            {match.name for match in matches}, {"backup_marker", "date_suffix"}
        )

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


if __name__ == "__main__":
    unittest.main()
