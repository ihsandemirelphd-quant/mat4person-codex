from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError, validate_payload
from pipeline.io import atomic_write_json, load_json
from pipeline.shards import validate_shard


DRAFT_NOTE_PREFIX = "DRAFT ONLY; not human-reviewed"
MECHANICAL_STATUSES = {"exact_match", "normalized_match"}
EXPECTED_RELEASE_STATUS = {
    "source:v2_ikeda_koc_life_devoted_2003_pdf": (
        "blocked_publisher_byte_reconciliation"
    ),
    "source:v2_fge_research_staff_pdf": "blocked_rights_review",
}
VERDICT_BY_STATUS = {
    "accepted": "accept",
    "rejected": "reject",
    "review": "review",
}


def _unique_by(
    rows: list[dict[str, Any]], field: str, label: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        identifier = row[field]
        if identifier in result:
            raise ContractError(f"Duplicate {label}: {identifier}")
        result[identifier] = row
    return result


def _require_model_role(record: dict[str, Any], role: str) -> None:
    values = (
        str(record.get("model", "")),
        str(record.get("prompt_version", "")),
        str(record.get("worker_id", "")),
    )
    folded = " ".join(values).casefold()
    if "luna" in folded:
        raise ContractError("Luna execution records are forbidden before the gold gate")
    if role.casefold() not in folded:
        raise ContractError(f"Execution record is not bound to the {role} role")


def _manifest_sources(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_payload("pilot-source-manifest", manifest)
    return _unique_by(manifest["sources"], "source_id", "manifest source ID")


def _validate_gold_draft(
    gold_draft: list[dict[str, Any]],
    manifest_by_id: dict[str, dict[str, Any]],
    expected_source_ids: set[str],
) -> tuple[dict[str, str], Counter[str]]:
    if not isinstance(gold_draft, list):
        raise ContractError("Gold draft must be a JSON array")
    for item in gold_draft:
        validate_payload("gold-item", item)

    _unique_by(gold_draft, "case_id", "gold case ID")
    actual_source_ids = {item["source_id"] for item in gold_draft}
    if actual_source_ids != expected_source_ids:
        missing = sorted(expected_source_ids - actual_source_ids)
        foreign = sorted(actual_source_ids - expected_source_ids)
        raise ContractError(
            f"Gold source set mismatch; missing={missing}, foreign={foreign}"
        )

    split_by_source: dict[str, str] = {}
    counts: Counter[str] = Counter()
    for item in gold_draft:
        source_id = item["source_id"]
        manifest_source = manifest_by_id.get(source_id)
        if manifest_source is None:
            raise ContractError(f"Gold item references foreign source {source_id}")
        if item["source_sha256"] != manifest_source["drive"]["raw_sha256"]:
            raise ContractError(f"Gold item has a stale source hash for {source_id}")
        previous = split_by_source.setdefault(source_id, item["split"])
        if previous != item["split"]:
            raise ContractError(f"Source-level split leakage: {source_id}")
        if not item.get("note", "").startswith(DRAFT_NOTE_PREFIX):
            raise ContractError(
                f"Gold item {item['case_id']} is not marked as an AI-only draft"
            )
        if any(not value.startswith("ai-") for value in item["annotators"]):
            raise ContractError(
                f"Gold item {item['case_id']} contains a non-AI annotator"
            )
        counts[source_id] += 1
    return split_by_source, counts


def _derive_public_rows(
    config: dict[str, Any],
    reviewed_shards: list[dict[str, Any]],
    gold_draft: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    validate_payload("run", config)
    manifest_by_id = _manifest_sources(manifest)
    expected_source_ids = set(EXPECTED_RELEASE_STATUS)

    assignments = _unique_by(config["assignments"], "shard_id", "assignment shard ID")
    assignment_source_ids = [row["source_id"] for row in assignments.values()]
    if len(assignment_source_ids) != len(set(assignment_source_ids)):
        raise ContractError("Run assigns the same source more than once")
    if set(assignment_source_ids) != expected_source_ids:
        missing = sorted(expected_source_ids - set(assignment_source_ids))
        foreign = sorted(set(assignment_source_ids) - expected_source_ids)
        raise ContractError(
            f"Pilot review source set mismatch; missing={missing}, foreign={foreign}"
        )
    for assignment in assignments.values():
        source_id = assignment["source_id"]
        manifest_source = manifest_by_id.get(source_id)
        if manifest_source is None:
            raise ContractError(f"Run references foreign manifest source {source_id}")
        if assignment["source_sha256"] != manifest_source["drive"]["raw_sha256"]:
            raise ContractError(f"Run has a stale source hash for {source_id}")

    shard_by_id = _unique_by(reviewed_shards, "shard_id", "reviewed shard ID")
    if set(shard_by_id) != set(assignments):
        missing = sorted(set(assignments) - set(shard_by_id))
        foreign = sorted(set(shard_by_id) - set(assignments))
        raise ContractError(
            f"Reviewed shard set mismatch; missing={missing}, foreign={foreign}"
        )

    split_by_source, gold_counts = _validate_gold_draft(
        gold_draft, manifest_by_id, expected_source_ids
    )
    rows: list[dict[str, Any]] = []
    for shard in reviewed_shards:
        validate_shard(shard, config)
        source_id = shard["source_id"]
        manifest_source = manifest_by_id[source_id]
        if shard["source_sha256"] != manifest_source["drive"]["raw_sha256"]:
            raise ContractError(f"Reviewed shard has a stale source hash for {source_id}")

        evidence_by_id = _unique_by(shard["evidence"], "evidence_id", "evidence ID")
        mechanical_ids = {
            evidence_id
            for evidence_id, evidence in evidence_by_id.items()
            if evidence["verification"]["status"] in MECHANICAL_STATUSES
        }
        status_counts: Counter[str] = Counter()
        mechanically_located = 0
        for relation in shard["relations"]:
            status = relation["status"]
            if status not in VERDICT_BY_STATUS:
                raise ContractError(
                    f"Relation {relation['relation_id']} lacks an independent verdict"
                )
            verifier = relation["verifier"]
            if verifier is None or verifier.get("verdict") != VERDICT_BY_STATUS[status]:
                raise ContractError(
                    f"Relation {relation['relation_id']} has an inconsistent verdict"
                )
            if verifier["worker_id"] == relation["extractor"]["worker_id"]:
                raise ContractError(
                    f"Relation {relation['relation_id']} was self-reviewed"
                )
            _require_model_role(relation["extractor"], "Terra")
            _require_model_role(verifier, "Sol")
            if set(relation["evidence_ids"]).issubset(mechanical_ids):
                mechanically_located += 1
            status_counts[status] += 1

        candidates = len(shard["relations"])
        if mechanically_located != candidates:
            raise ContractError(
                f"Source {source_id} contains a candidate without mechanically located evidence"
            )
        if len(evidence_by_id) != candidates:
            raise ContractError(
                f"Source {source_id} must bind exactly one evidence record per candidate"
            )
        rows.append(
            {
                "source_id": source_id,
                "source_sha256": shard["source_sha256"],
                "source_split": split_by_source[source_id],
                "candidates_proposed": candidates,
                "mechanically_located": mechanically_located,
                "accepted_private_review": status_counts["accepted"],
                "held_for_entity_review": status_counts["review"],
                "rejected": status_counts["rejected"],
                "draft_gold_cases": gold_counts[source_id],
                "public_release_status": EXPECTED_RELEASE_STATUS[source_id],
            }
        )

    rows.sort(key=lambda row: row["source_id"])
    counts = {
        "sources": len(rows),
        "candidates_proposed": sum(row["candidates_proposed"] for row in rows),
        "mechanically_located": sum(row["mechanically_located"] for row in rows),
        "accepted_private_review": sum(
            row["accepted_private_review"] for row in rows
        ),
        "held_for_entity_review": sum(
            row["held_for_entity_review"] for row in rows
        ),
        "rejected": sum(row["rejected"] for row in rows),
        "draft_gold_cases": len(gold_draft),
        "human_gold_cases": 0,
        "luna_gate_runs": 0,
        "published_evidence_claims": 0,
        "published_relations": 0,
    }
    return rows, counts


def validate_pilot_candidate_review_report(
    report: dict[str, Any],
    config: dict[str, Any],
    reviewed_shards: list[dict[str, Any]],
    gold_draft: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> dict[str, int]:
    """Validate a counts-only public report against all private research inputs."""

    validate_payload("pilot-candidate-review-report", report)
    rows, counts = _derive_public_rows(config, reviewed_shards, gold_draft, manifest)
    if report["run_id"] != config["run_id"]:
        raise ContractError("Pilot candidate report belongs to another run")
    if report["sources"] != rows:
        raise ContractError("Pilot candidate report source rows do not reproduce inputs")
    if report["counts"] != counts:
        raise ContractError("Pilot candidate report counts do not reproduce inputs")
    return counts


def build_pilot_candidate_review_report(
    config: dict[str, Any],
    reviewed_shards: list[dict[str, Any]],
    gold_draft: list[dict[str, Any]],
    manifest: dict[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build the public report without copying private names, text, or relations."""

    rows, counts = _derive_public_rows(config, reviewed_shards, gold_draft, manifest)
    report = {
        "report_version": "pilot-candidate-review-v1",
        "generated_at": generated_at,
        "run_id": config["run_id"],
        "review_method": "isolated-extraction-independent-review-v1",
        "model_routing": {
            "extraction_role": "Terra",
            "review_role": "Sol",
            "backend_model_identifier_status": "not_exposed_by_runtime",
            "luna_used": False,
        },
        "content_boundary": {
            "contains_names": False,
            "contains_quotes": False,
            "contains_source_locators": False,
            "contains_raw_text": False,
            "contains_relation_records": False,
        },
        "sources": rows,
        "counts": counts,
    }
    validate_pilot_candidate_review_report(
        report, config, reviewed_shards, gold_draft, manifest
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a strict, counts-only public pilot candidate review report"
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("reviewed_shards", type=Path)
    parser.add_argument("gold_draft", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    reviewed_shards = [
        load_json(path) for path in sorted(args.reviewed_shards.glob("*.json"))
    ]
    report = build_pilot_candidate_review_report(
        load_json(args.config),
        reviewed_shards,
        load_json(args.gold_draft),
        load_json(args.manifest),
        generated_at=args.generated_at,
    )
    atomic_write_json(args.output, report)
    print(
        "Pilot candidate review report: "
        f"{report['counts']['candidates_proposed']} located, "
        f"{report['counts']['accepted_private_review']} accepted privately, "
        f"{report['counts']['published_relations']} published"
    )


if __name__ == "__main__":
    main()
