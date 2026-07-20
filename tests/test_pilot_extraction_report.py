from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError
from pipeline.io import load_json
from pipeline.pilot_inventory import validate_pilot_extraction_report


ROOT = Path(__file__).resolve().parents[1]


class PilotExtractionReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_json(
            ROOT / "data" / "research" / "pilot-source-manifest.json"
        )
        cls.report = load_json(
            ROOT / "data" / "research" / "pilot-extraction-report.json"
        )

    def validate(self, report: dict[str, Any] | None = None) -> dict[str, int]:
        return validate_pilot_extraction_report(
            report if report is not None else self.report,
            self.manifest,
        )

    def test_reviewed_report_is_complete_and_claim_free(self) -> None:
        counts = self.validate()
        self.assertEqual(counts["sources"], 10)
        self.assertEqual(counts["pages"], 162)
        self.assertEqual(counts["nonempty_pages"], 162)
        self.assertEqual(counts["visually_reviewed_sources"], 10)
        self.assertEqual(counts["ocr_required_sources"], 0)
        self.assertEqual(counts["evidence_claims"], 0)
        self.assertEqual(counts["relationship_claims"], 0)

    def test_stale_source_hash_is_rejected(self) -> None:
        report = copy.deepcopy(self.report)
        report["sources"][0]["source_sha256"] = "0" * 64
        with self.assertRaises(ContractError):
            self.validate(report)

    def test_duplicate_text_artifact_is_rejected(self) -> None:
        report = copy.deepcopy(self.report)
        report["sources"][1]["text_artifact_sha256"] = report["sources"][0]["text_artifact_sha256"]
        with self.assertRaises(ContractError):
            self.validate(report)

    def test_low_text_pages_must_be_reviewed(self) -> None:
        report = copy.deepcopy(self.report)
        ikeda = next(
            row
            for row in report["sources"]
            if row["source_id"] == "source:v2_ikeda_koc_life_devoted_2003_pdf"
        )
        ikeda["representative_pages_reviewed"] = [1]
        with self.assertRaises(ContractError):
            self.validate(report)

    def test_reported_counts_must_reproduce_rows(self) -> None:
        report = copy.deepcopy(self.report)
        report["sources"][0]["page_count"] += 1
        with self.assertRaises(ContractError):
            self.validate(report)


if __name__ == "__main__":
    unittest.main()
