from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from pipeline.io import load_json, sha256_text
from pipeline.source_text import artifact_digest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
UNDIRECTED_TYPES = {"academic_environment", "academic_output", "in_same_context"}
MEMBER_SUBTYPES = {
    "research_staff",
    "postdoc",
    "board",
    "director",
    "staff",
    "group_photo",
    "award",
}


class ContractError(ValueError):
    """Raised when a payload or bundle violates the frozen contracts."""


def load_schema(kind: str) -> dict[str, Any]:
    path = SCHEMA_DIR / f"{kind}.schema.json"
    if not path.exists():
        raise ContractError(f"Unknown contract kind: {kind}")
    return load_json(path)


def validate_payload(kind: str, payload: dict[str, Any]) -> None:
    validator = Draft202012Validator(
        load_schema(kind), format_checker=FormatChecker()
    )
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ContractError(f"Invalid {kind}: {details}")


def _unique(rows: list[dict[str, Any]], field: str, kind: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        identifier = row[field]
        if identifier in result:
            raise ContractError(f"Duplicate {kind} {identifier}")
        result[identifier] = row
    return result


def _validate_source_text(
    item: dict[str, Any], source: dict[str, Any]
) -> None:
    if item["source_sha256"] != source["sha256"]:
        raise ContractError(f"Text artifact for {item['source_id']} has a stale source hash")
    if item["artifact_sha256"] != artifact_digest(item):
        raise ContractError(f"Text artifact for {item['source_id']} has an invalid digest")
    pages = item["pages"]
    expected_numbers = list(range(1, len(pages) + 1))
    actual_numbers = [page["page_number"] for page in pages]
    if actual_numbers != expected_numbers:
        raise ContractError(f"Text artifact for {item['source_id']} has non-contiguous pages")
    if source["page_count"] is not None and source["page_count"] != len(pages):
        raise ContractError(f"Source {item['source_id']} page_count does not match its text artifact")
    for page in pages:
        if page["text_sha256"] != sha256_text(page["text"]):
            raise ContractError(
                f"Text artifact for {item['source_id']} has an invalid page digest"
            )


def _validate_evidence(
    item: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    texts: dict[str, dict[str, Any]],
) -> None:
    if not item["quote"].strip():
        raise ContractError(f"Evidence {item['evidence_id']} has a whitespace-only quote")
    if item["quote_sha256"] != sha256_text(item["quote"]):
        raise ContractError(f"Evidence {item['evidence_id']} has an invalid quote digest")
    source = sources.get(item["source_id"])
    if source is None:
        raise ContractError(
            f"Evidence {item['evidence_id']} references unknown source {item['source_id']}"
        )
    if item["source_sha256"] != source["sha256"]:
        raise ContractError(f"Evidence {item['evidence_id']} has a stale source hash")
    text = texts.get(item["source_id"])
    if text is None:
        raise ContractError(f"Evidence {item['evidence_id']} has no source text artifact")
    if item["text_artifact_sha256"] != text["artifact_sha256"]:
        raise ContractError(f"Evidence {item['evidence_id']} has a stale text artifact hash")

    page_start, page_end = item["page_start"], item["page_end"]
    if item["page_status"] == "exact":
        if source["page_count"] is None:
            raise ContractError(f"Evidence {item['evidence_id']} invents pagination for an unpaginated source")
        if page_start > page_end:
            raise ContractError(f"Evidence {item['evidence_id']} has reversed page bounds")
        if page_end > source["page_count"]:
            raise ContractError(f"Evidence {item['evidence_id']} exceeds source page_count")

    verification = item["verification"]
    status = verification["status"]
    char_start, char_end = verification["char_start"], verification["char_end"]
    if (char_start is None) != (char_end is None):
        raise ContractError(f"Evidence {item['evidence_id']} has a half-null character span")
    if char_start is not None and char_start >= char_end:
        raise ContractError(f"Evidence {item['evidence_id']} has an invalid character span")
    if status == "unverified":
        if verification["method"] != "none" or verification["match_count"] != 0:
            raise ContractError(f"Evidence {item['evidence_id']} has an inconsistent unverified record")
    elif status == "exact_match":
        page_number = verification["page_number"]
        if verification["method"] != "exact-v1" or char_start is None:
            raise ContractError(f"Evidence {item['evidence_id']} has an invalid exact match")
        if verification["match_count"] < 1 or verification["matched_text_sha256"] is None:
            raise ContractError(f"Evidence {item['evidence_id']} has an incomplete exact match")
        if page_number is None or page_number > len(text["pages"]):
            raise ContractError(f"Evidence {item['evidence_id']} has an invalid matched page")
        page_text = text["pages"][page_number - 1]["text"]
        if char_end > len(page_text) or page_text[char_start:char_end] != item["quote"]:
            raise ContractError(f"Evidence {item['evidence_id']} exact span does not reproduce its quote")
    elif status == "normalized_match":
        if verification["method"] != "nfkc-whitespace-v1":
            raise ContractError(f"Evidence {item['evidence_id']} has an unknown normalization profile")
        if verification["match_count"] < 1 or verification["page_number"] is None:
            raise ContractError(f"Evidence {item['evidence_id']} has an incomplete normalized match")
    elif status == "manual":
        if verification["method"] != "manual" or not verification["reason"]:
            raise ContractError(f"Evidence {item['evidence_id']} lacks a manual-review reason")


def _validate_relation(
    item: dict[str, Any],
    entities: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
) -> None:
    for field in ("source_entity_id", "target_entity_id"):
        if item[field] not in entities:
            raise ContractError(f"Relation {item['relation_id']} references unknown entity {item[field]}")
    unknown = set(item["evidence_ids"]) - set(evidence)
    if unknown:
        raise ContractError(
            f"Relation {item['relation_id']} references unknown evidence: {sorted(unknown)}"
        )
    if item["relation_type"] == "fg_member":
        if item["member_subtype"] not in MEMBER_SUBTYPES:
            raise ContractError(f"Relation {item['relation_id']} requires an FG member subtype")
    elif item["member_subtype"] is not None:
        raise ContractError(f"Relation {item['relation_id']} uses a member subtype outside fg_member")
    expected_direction = "undirected" if item["relation_type"] in UNDIRECTED_TYPES else "directed"
    if item["direction"] != expected_direction:
        raise ContractError(f"Relation {item['relation_id']} has invalid direction for its type")

    if item["status"] == "accepted":
        verifier = item["verifier"]
        if verifier is None or verifier.get("verdict") != "accept":
            raise ContractError(f"Accepted relation {item['relation_id']} lacks an accepting verdict")
        if verifier["worker_id"] == item["extractor"]["worker_id"]:
            raise ContractError(f"Relation {item['relation_id']} was self-verified")
        accepted_evidence = [evidence[value] for value in item["evidence_ids"]]
        if any(row["verification"]["status"] == "unverified" for row in accepted_evidence):
            raise ContractError(f"Accepted relation {item['relation_id']} uses unverified evidence")


def validate_bundle(
    *,
    sources: Iterable[dict[str, Any]],
    entities: Iterable[dict[str, Any]],
    source_texts: Iterable[dict[str, Any]],
    evidence: Iterable[dict[str, Any]],
    relations: Iterable[dict[str, Any]],
) -> None:
    source_rows = list(sources)
    entity_rows = list(entities)
    text_rows = list(source_texts)
    evidence_rows = list(evidence)
    relation_rows = list(relations)
    for kind, rows in (
        ("source", source_rows),
        ("entity", entity_rows),
        ("source-text", text_rows),
        ("evidence", evidence_rows),
        ("relation", relation_rows),
    ):
        for row in rows:
            validate_payload(kind, row)

    source_map = _unique(source_rows, "source_id", "source_id")
    entity_map = _unique(entity_rows, "entity_id", "entity_id")
    text_map = _unique(text_rows, "source_id", "source text")
    evidence_map = _unique(evidence_rows, "evidence_id", "evidence_id")
    _unique(relation_rows, "relation_id", "relation_id")

    for source_id, text in text_map.items():
        source = source_map.get(source_id)
        if source is None:
            raise ContractError(f"Text artifact references unknown source {source_id}")
        _validate_source_text(text, source)
    for row in evidence_rows:
        _validate_evidence(row, source_map, text_map)
    for row in relation_rows:
        _validate_relation(row, entity_map, evidence_map)
