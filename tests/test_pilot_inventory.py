from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError
from pipeline.io import load_json
from pipeline.pilot_inventory import validate_pilot_source_manifest


ROOT = Path(__file__).resolve().parents[1]


class PilotInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_json(
            ROOT / "data" / "research" / "pilot-source-manifest.json"
        )
        cls.entities = load_json(ROOT / "data" / "registry" / "entities.json")
        cls.presentation = load_json(ROOT / "data" / "registry" / "presentation.json")

    def validate(self, manifest: dict[str, Any] | None = None) -> dict[str, int]:
        return validate_pilot_source_manifest(
            manifest if manifest is not None else self.manifest,
            self.entities,
            self.presentation["sun_ids"],
        )

    def test_authorized_pilot_is_hashed_and_claim_free(self) -> None:
        summary = self.validate()
        self.assertEqual(summary["sources"], 10)
        self.assertEqual(summary["bytes"], 18_475_323)
        self.assertEqual(summary["sun_coverage"], 3)
        self.assertEqual(summary["license_verified"], 1)
        self.assertEqual(summary["rights_review_required"], 9)
        self.assertEqual(summary["extraction_pending"], 10)
        self.assertEqual(summary["evidence_claims"], 0)
        self.assertEqual(summary["relationship_claims"], 0)

    def test_duplicate_drive_file_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sources"][1]["drive"]["file_locator_sha256"] = manifest["sources"][0]["drive"]["file_locator_sha256"]
        with self.assertRaises(ContractError):
            self.validate(manifest)

    def test_duplicate_raw_hash_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sources"][1]["drive"]["raw_sha256"] = manifest["sources"][0]["drive"]["raw_sha256"]
        with self.assertRaises(ContractError):
            self.validate(manifest)

    def test_ai_output_title_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sources"][0]["title"] = "Four Suns GPT results WITH sources"
        with self.assertRaises(ContractError):
            self.validate(manifest)

    def test_unknown_scope_entity_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sources"][0]["scope_entity_ids"] = ["person:not_in_registry"]
        with self.assertRaises(ContractError):
            self.validate(manifest)

    def test_source_set_drift_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sources"][0]["source_id"] = "source:replacement"
        with self.assertRaises(ContractError):
            self.validate(manifest)

    def test_publication_clearance_requires_licence_metadata(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sources"][0]["publication_status"] = "license_verified_extraction_pending"
        with self.assertRaises(ContractError):
            self.validate(manifest)

    def test_claim_counts_and_extra_fields_are_rejected(self) -> None:
        for mutation in ("evidence_claims", "relationship_claims", "extracted_quote"):
            manifest = copy.deepcopy(self.manifest)
            manifest["sources"][0][mutation] = 1 if mutation != "extracted_quote" else "not allowed"
            with self.subTest(mutation=mutation), self.assertRaises(ContractError):
                self.validate(manifest)

    def test_verified_missing_baseline_file_is_frozen(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["baseline_reconciliation"]["missing_files"] = ["different.ppt"]
        with self.assertRaises(ContractError):
            self.validate(manifest)


if __name__ == "__main__":
    unittest.main()
