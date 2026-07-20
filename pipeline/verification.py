from __future__ import annotations

import argparse
import copy
import re
import unicodedata
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError, validate_payload
from pipeline.io import atomic_write_json, load_json, sha256_text


NORMALIZATION_PROFILE = "nfkc-whitespace-v1"
MECHANICAL_VERIFIER = "code:verify-quotes-v1"


def normalize_for_match(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()


def _count_occurrences(haystack: str, needle: str) -> list[int]:
    positions: list[int] = []
    start = 0
    while needle and (position := haystack.find(needle, start)) >= 0:
        positions.append(position)
        start = position + max(1, len(needle))
    return positions


def unverified(reason: str) -> dict[str, Any]:
    return {
        "status": "unverified",
        "method": "none",
        "normalization_profile_version": None,
        "page_number": None,
        "char_start": None,
        "char_end": None,
        "match_count": 0,
        "matched_text_sha256": None,
        "verifier": MECHANICAL_VERIFIER,
        "reason": reason,
    }


def verify_evidence(
    evidence: dict[str, Any], source_text: dict[str, Any]
) -> dict[str, Any]:
    result = copy.deepcopy(evidence)
    quote = result.get("quote", "")
    if not quote.strip():
        raise ContractError("Evidence quote must contain non-whitespace text")
    if result["source_id"] != source_text["source_id"]:
        raise ContractError("Evidence and text artifact source_id differ")

    result["source_sha256"] = source_text["source_sha256"]
    result["text_artifact_sha256"] = source_text["artifact_sha256"]
    result["quote_sha256"] = sha256_text(quote)
    pages = source_text["pages"]
    if result["page_status"] == "exact":
        start = result["page_start"]
        end = result["page_end"]
        pages = [page for page in pages if start <= page["page_number"] <= end]

    exact_matches: list[tuple[int, int, int]] = []
    for page in pages:
        for start in _count_occurrences(page["text"], quote):
            exact_matches.append((page["page_number"], start, start + len(quote)))
    if exact_matches:
        page_number, char_start, char_end = exact_matches[0]
        result["verification"] = {
            "status": "exact_match",
            "method": "exact-v1",
            "normalization_profile_version": None,
            "page_number": page_number,
            "char_start": char_start,
            "char_end": char_end,
            "match_count": len(exact_matches),
            "matched_text_sha256": sha256_text(quote),
            "verifier": MECHANICAL_VERIFIER,
            "reason": None,
        }
        validate_payload("evidence", result)
        return result

    normalized_quote = normalize_for_match(quote)
    normalized_matches: list[int] = []
    for page in pages:
        positions = _count_occurrences(normalize_for_match(page["text"]), normalized_quote)
        normalized_matches.extend([page["page_number"]] * len(positions))
    if normalized_matches:
        result["verification"] = {
            "status": "normalized_match",
            "method": NORMALIZATION_PROFILE,
            "normalization_profile_version": NORMALIZATION_PROFILE,
            "page_number": normalized_matches[0],
            "char_start": None,
            "char_end": None,
            "match_count": len(normalized_matches),
            "matched_text_sha256": sha256_text(normalized_quote),
            "verifier": MECHANICAL_VERIFIER,
            "reason": None,
        }
    else:
        result["verification"] = unverified("quote_not_found")
    validate_payload("evidence", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Locate evidence quotations in a source text artifact")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("source_text", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = load_json(args.evidence)
    items = payload if isinstance(payload, list) else [payload]
    source_text = load_json(args.source_text)
    verified = [verify_evidence(item, source_text) for item in items]
    atomic_write_json(args.output, verified if isinstance(payload, list) else verified[0])
    print(f"Verified {len(verified)} evidence record(s)")


if __name__ == "__main__":
    main()
