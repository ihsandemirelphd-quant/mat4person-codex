from __future__ import annotations

import base64
import copy
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from pipeline.contracts import ContractError, validate_bundle
from pipeline.io import sha256_bytes
from pipeline.materialize_raw import materialize_base64
from pipeline.pdf_ingest import ingest_pdf


class PdfIngestTests(unittest.TestCase):
    def test_materializer_rejects_hash_and_path_drift(self) -> None:
        raw = b"pilot bytes"
        encoded = base64.b64encode(raw)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                materialize_base64(
                    encoded,
                    root / "outside.pdf",
                    expected_sha256=sha256_bytes(raw),
                    expected_size=len(raw),
                    allowed_root=root / "allowed",
                )
            with self.assertRaises(ValueError):
                materialize_base64(
                    encoded,
                    root / "allowed" / "bad.pdf",
                    expected_sha256="0" * 64,
                    expected_size=len(raw),
                    allowed_root=root / "allowed",
                )

    def test_pdf_ingest_binds_raw_hash_and_physical_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "input.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            writer.add_blank_page(width=200, height=200)
            with pdf.open("wb") as handle:
                writer.write(handle)
            raw_sha256 = sha256_bytes(pdf.read_bytes())
            record = {
                "source_id": "source:test_pdf",
                "title": "Test PDF",
                "drive": {"raw_sha256": raw_sha256},
                "origin": {
                    "publisher": "Test publisher",
                    "canonical_url": None,
                    "rights_note": "Synthetic test input.",
                },
            }
            source, source_text, qa = ingest_pdf(
                pdf,
                pilot_record=record,
                output_dir=root / "output",
                language="en",
            )
            self.assertEqual(source["page_count"], 2)
            self.assertEqual([page["page_number"] for page in source_text["pages"]], [1, 2])
            self.assertTrue(qa["requires_ocr_review"])
            validate_bundle(
                sources=[source],
                entities=[],
                source_texts=[source_text],
                evidence=[],
                relations=[],
            )

            tampered = copy.deepcopy(record)
            tampered["drive"]["raw_sha256"] = "0" * 64
            with self.assertRaises(ContractError):
                ingest_pdf(
                    pdf,
                    pilot_record=tampered,
                    output_dir=root / "tampered",
                    language="en",
                )


if __name__ == "__main__":
    unittest.main()
