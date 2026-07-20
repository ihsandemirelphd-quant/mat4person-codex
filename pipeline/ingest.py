from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pipeline.contracts import validate_payload
from pipeline.io import atomic_write_json, sha256_bytes, sha256_text
from pipeline.source_text import INGEST_VERSION, OFFSET_UNIT, artifact_digest


def ingest_text(
    input_path: Path,
    *,
    source_id: str,
    title: str,
    language: str,
    output_dir: Path,
    content_kind: str = "plain_text",
    access_kind: str = "local",
    uri: str | None = None,
    citation: str | None = None,
    rights_note: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = input_path.read_bytes()
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    source_sha256 = sha256_bytes(raw)
    has_explicit_pages = "\f" in text
    page_texts = text.split("\f")
    pages = [
        {
            "page_number": index,
            "printed_label": None,
            "text": page,
            "text_sha256": sha256_text(page),
        }
        for index, page in enumerate(page_texts, start=1)
    ]
    source: dict[str, Any] = {
        "source_id": source_id,
        "title": title,
        "source_type": "other",
        "access": {"kind": access_kind, "uri": uri},
        "sha256": source_sha256,
        "language": language,
        "page_count": len(pages) if has_explicit_pages else None,
        "content_kind": content_kind,
        "ingest_version": INGEST_VERSION,
    }
    if citation:
        source["citation"] = citation
    if rights_note:
        source["rights_note"] = rights_note

    source_text: dict[str, Any] = {
        "source_id": source_id,
        "source_sha256": source_sha256,
        "artifact_sha256": "0" * 64,
        "ingest_version": INGEST_VERSION,
        "offset_unit": OFFSET_UNIT,
        "pages": pages,
    }
    source_text["artifact_sha256"] = artifact_digest(source_text)
    validate_payload("source", source)
    validate_payload("source-text", source_text)
    atomic_write_json(output_dir / "source.json", source)
    atomic_write_json(output_dir / "source-text.json", source_text)
    return source, source_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest UTF-8 text into an immutable source revision")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--language", default="en")
    parser.add_argument("--content-kind", default="plain_text")
    parser.add_argument("--access-kind", choices=["public", "private", "local"], default="local")
    parser.add_argument("--uri")
    parser.add_argument("--citation")
    parser.add_argument("--rights-note")
    args = parser.parse_args()
    ingest_text(
        args.input,
        source_id=args.source_id,
        title=args.title,
        language=args.language,
        output_dir=args.output,
        content_kind=args.content_kind,
        access_kind=args.access_kind,
        uri=args.uri,
        citation=args.citation,
        rights_note=args.rights_note,
    )
    print(f"Ingested {args.source_id} into {args.output}")


if __name__ == "__main__":
    main()
