from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError
from pipeline.io import load_json
from pipeline.source_inventory import validate_source_inventory


ROOT = Path(__file__).resolve().parents[1]


class SourceInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = load_json(ROOT / "data" / "research" / "source-candidates.json")
        cls.entities = load_json(ROOT / "data" / "registry" / "entities.json")
        cls.presentation = load_json(ROOT / "data" / "registry" / "presentation.json")

    def validate(
        self,
        records: list[dict[str, Any]] | None = None,
        sun_ids: list[str] | None = None,
    ) -> dict[str, int]:
        return validate_source_inventory(
            records if records is not None else self.records,
            self.entities,
            sun_ids if sun_ids is not None else self.presentation["sun_ids"],
        )

    def test_four_sun_queue_is_claim_free(self) -> None:
        summary = self.validate()
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["anchors"], 4)
        self.assertEqual(summary["license_ready"], 1)
        self.assertEqual(summary["evidence_claims"], 0)
        self.assertEqual(summary["relationship_claims"], 0)

    def test_missing_sun_is_rejected(self) -> None:
        with self.assertRaises(ContractError):
            self.validate(copy.deepcopy(self.records[:-1]))

    def test_duplicate_candidate_id_is_rejected(self) -> None:
        records = copy.deepcopy(self.records)
        records[1]["source_candidate_id"] = records[0]["source_candidate_id"]
        with self.assertRaises(ContractError):
            self.validate(records)

    def test_stale_anchor_name_is_rejected(self) -> None:
        records = copy.deepcopy(self.records)
        records[0]["anchor_name"] = "Wrong person"
        with self.assertRaises(ContractError):
            self.validate(records)

    def test_uncleared_source_cannot_be_marked_ready(self) -> None:
        records = copy.deepcopy(self.records)
        records[0]["ingestion_status"] = "license_ready_download_pending"
        with self.assertRaises(ContractError):
            self.validate(records)

    def test_ready_source_requires_https_rights_reference(self) -> None:
        records = copy.deepcopy(self.records)
        records[3]["rights_url"] = None
        with self.assertRaises(ContractError):
            self.validate(records)

    def test_claim_counts_are_frozen_at_zero(self) -> None:
        for field in ("evidence_claims", "relationship_claims"):
            records = copy.deepcopy(self.records)
            records[0][field] = 1
            with self.subTest(field=field), self.assertRaises(ContractError):
                self.validate(records)

    def test_extra_fields_are_rejected(self) -> None:
        records = copy.deepcopy(self.records)
        records[0]["imported_quote"] = "not allowed"
        with self.assertRaises(ContractError):
            self.validate(records)

    def test_sun_configuration_must_contain_four_unique_ids(self) -> None:
        sun_ids = self.presentation["sun_ids"]
        corrupt_configurations = [
            [],
            sun_ids[:-1],
            [*sun_ids, sun_ids[0]],
            [sun_ids[0], sun_ids[0], sun_ids[2], sun_ids[3]],
        ]
        for configuration in corrupt_configurations:
            with self.subTest(configuration=configuration), self.assertRaises(ContractError):
                self.validate(sun_ids=configuration)


if __name__ == "__main__":
    unittest.main()
