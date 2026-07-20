from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pipeline.io import atomic_write_json, load_json
from pipeline.pdf_ingest import ingest_pdf


def ingest_pilot_batch(
    manifest_path: Path,
    raw_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    rows: list[dict[str, Any]] = []
    for record in manifest["sources"]:
        stem = record["source_id"].removeprefix("source:")
        raw_path = raw_dir / f"{stem}.pdf"
        source, source_text, qa = ingest_pdf(
            raw_path,
            pilot_record=record,
            output_dir=output_dir / stem,
        )
        rows.append(
            {
                "source_id": record["source_id"],
                "source_sha256": source["sha256"],
                "text_artifact_sha256": source_text["artifact_sha256"],
                "ingest_version": source["ingest_version"],
                "page_count": qa["page_count"],
                "nonempty_pages": qa["nonempty_pages"],
                "low_text_pages": qa["low_text_pages"],
                "requires_ocr_review": qa["requires_ocr_review"],
            }
        )
    summary = {
        "report_version": "pilot-pdf-extraction-v1",
        "sources": rows,
        "counts": {
            "sources": len(rows),
            "pages": sum(row["page_count"] for row in rows),
            "nonempty_pages": sum(row["nonempty_pages"] for row in rows),
            "ocr_review_sources": sum(row["requires_ocr_review"] for row in rows),
            "evidence_claims": 0,
            "relationship_claims": 0,
        },
    }
    atomic_write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract all hash-bound PDFs in the controlled pilot"
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    summary = ingest_pilot_batch(args.manifest, args.raw_dir, args.output_dir)
    print(
        f"Extracted {summary['counts']['sources']} sources and "
        f"{summary['counts']['pages']} physical pages; "
        f"OCR review sources={summary['counts']['ocr_review_sources']}"
    )


if __name__ == "__main__":
    main()
