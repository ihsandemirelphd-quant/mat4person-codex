from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pypdf import PdfReader, __version__ as pypdf_version

from pipeline.contracts import ContractError, validate_payload
from pipeline.io import atomic_write_json, load_json, sha256_file, sha256_text
from pipeline.source_text import OFFSET_UNIT, artifact_digest


INGEST_VERSION = f"pdf-pypdf-{pypdf_version}-v1"


def _normalize_text(value: str | None) -> str:
    return (value or "").replace("\r\n", "\n").replace("\r", "\n")


def ingest_pdf(
    input_path: Path,
    *,
    pilot_record: dict[str, Any],
    output_dir: Path,
    language: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Create deterministic physical-page text from one hash-bound pilot PDF."""

    expected_sha256 = pilot_record["drive"]["raw_sha256"]
    actual_sha256 = sha256_file(input_path)
    if actual_sha256 != expected_sha256:
        raise ContractError(
            f"PDF {pilot_record['source_id']} does not match its pilot manifest hash"
        )

    reader = PdfReader(input_path, strict=True)
    if reader.is_encrypted:
        raise ContractError(f"PDF {pilot_record['source_id']} is encrypted")

    pages: list[dict[str, Any]] = []
    character_counts: list[int] = []
    extraction_errors: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = _normalize_text(page.extract_text())
        except Exception as error:  # pypdf exposes parser-specific failures
            text = ""
            extraction_errors.append(
                {"page_number": page_number, "error": type(error).__name__}
            )
        character_counts.append(len(text.strip()))
        pages.append(
            {
                "page_number": page_number,
                "printed_label": None,
                "text": text,
                "text_sha256": sha256_text(text),
            }
        )

    if not pages:
        raise ContractError(f"PDF {pilot_record['source_id']} has no physical pages")

    canonical_url = pilot_record["origin"]["canonical_url"]
    rights_note = pilot_record["origin"]["rights_note"]
    source: dict[str, Any] = {
        "source_id": pilot_record["source_id"],
        "title": pilot_record["title"],
        "source_type": "pdf",
        "access": {"kind": "private", "uri": None},
        "sha256": actual_sha256,
        "language": language or pilot_record["language"],
        "page_count": len(pages),
        "content_kind": "pdf_text",
        "ingest_version": INGEST_VERSION,
        "citation": (
            f"{pilot_record['origin']['publisher']}. {canonical_url}"
            if canonical_url
            else pilot_record["origin"]["publisher"]
        ),
        "rights_note": rights_note,
    }
    source_text: dict[str, Any] = {
        "source_id": pilot_record["source_id"],
        "source_sha256": actual_sha256,
        "artifact_sha256": "0" * 64,
        "ingest_version": INGEST_VERSION,
        "offset_unit": OFFSET_UNIT,
        "pages": pages,
    }
    source_text["artifact_sha256"] = artifact_digest(source_text)
    validate_payload("source", source)
    validate_payload("source-text", source_text)

    low_text_pages = [
        page_number
        for page_number, count in enumerate(character_counts, start=1)
        if count < 40
    ]
    qa = {
        "source_id": pilot_record["source_id"],
        "source_sha256": actual_sha256,
        "text_artifact_sha256": source_text["artifact_sha256"],
        "ingest_version": INGEST_VERSION,
        "page_count": len(pages),
        "nonempty_pages": sum(count > 0 for count in character_counts),
        "low_text_pages": low_text_pages,
        "requires_ocr_review": bool(low_text_pages or extraction_errors),
        "page_character_counts": character_counts,
        "extraction_errors": extraction_errors,
    }
    atomic_write_json(output_dir / "source.json", source)
    atomic_write_json(output_dir / "source-text.json", source_text)
    atomic_write_json(output_dir / "qa.json", qa)
    return source, source_text, qa


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract deterministic page text from a hash-bound pilot PDF"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--language")
    args = parser.parse_args()
    manifest = load_json(args.manifest)
    matches = [row for row in manifest["sources"] if row["source_id"] == args.source_id]
    if len(matches) != 1:
        raise ContractError(f"Pilot manifest has no unique source {args.source_id}")
    _, _, qa = ingest_pdf(
        args.input,
        pilot_record=matches[0],
        output_dir=args.output,
        language=args.language,
    )
    print(
        f"Extracted {qa['source_id']}: {qa['page_count']} pages; "
        f"OCR review={qa['requires_ocr_review']}"
    )


if __name__ == "__main__":
    main()
