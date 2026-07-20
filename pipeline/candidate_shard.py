from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError, validate_payload
from pipeline.io import atomic_write_json, load_json
from pipeline.shards import run_config_digest, validate_shard
from pipeline.verification import unverified, verify_evidence


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ContractError(f"Candidate specification contains a duplicate {label}")


def build_candidate_shard(
    *,
    config: dict[str, Any],
    source: dict[str, Any],
    source_text: dict[str, Any],
    registry: list[dict[str, Any]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    """Turn one isolated model proposal into a mechanically verified shard."""

    validate_payload("run", config)
    validate_payload("candidate-spec", spec)
    if source["source_id"] != spec["source_id"]:
        raise ContractError("Candidate specification and source differ")
    if source["sha256"] != spec["source_sha256"]:
        raise ContractError("Candidate specification has a stale source hash")
    if source_text["source_id"] != source["source_id"]:
        raise ContractError("Candidate source text belongs to another source")
    if source_text["source_sha256"] != source["sha256"]:
        raise ContractError("Candidate source text has a stale source hash")

    matches = [
        row for row in config["assignments"] if row["source_id"] == source["source_id"]
    ]
    if len(matches) != 1:
        raise ContractError("Run must assign the candidate source exactly once")
    assignment = matches[0]
    worker = spec["worker"]
    if worker["worker_id"] != assignment["worker_id"]:
        raise ContractError("Candidate worker violates the run assignment")
    if assignment["source_sha256"] != source["sha256"]:
        raise ContractError("Run assignment has a stale source hash")

    entity_by_id = {row["entity_id"]: row for row in registry}
    if len(entity_by_id) != len(registry):
        raise ContractError("Registry contains duplicate entity IDs")
    relation_ids = [row["relation_id"] for row in spec["relations"]]
    evidence_ids = [
        evidence["evidence_id"]
        for relation in spec["relations"]
        for evidence in relation["evidence"]
    ]
    _unique(relation_ids, "relation ID")
    _unique(evidence_ids, "evidence ID")

    entities: dict[str, dict[str, Any]] = {}
    evidence_rows: list[dict[str, Any]] = []
    relation_rows: list[dict[str, Any]] = []
    for proposed in spec["relations"]:
        source_entity_id = proposed["source_entity_id"]
        target_entity_id = proposed["target_entity_id"]
        if source_entity_id == target_entity_id:
            raise ContractError(f"Relation {proposed['relation_id']} is a self-loop")
        for entity_id in (source_entity_id, target_entity_id):
            entity = entity_by_id.get(entity_id)
            if entity is None:
                raise ContractError(
                    f"Relation {proposed['relation_id']} references unknown entity {entity_id}"
                )
            entities[entity_id] = entity
        if proposed["direction"] == "undirected" and source_entity_id > target_entity_id:
            raise ContractError(
                f"Undirected relation {proposed['relation_id']} is not canonically ordered"
            )

        relation_evidence_ids: list[str] = []
        for candidate in proposed["evidence"]:
            draft = {
                "evidence_id": candidate["evidence_id"],
                "source_id": source["source_id"],
                "source_sha256": source["sha256"],
                "text_artifact_sha256": source_text["artifact_sha256"],
                "quote": candidate["quote"],
                "quote_sha256": "0" * 64,
                "page_status": candidate["page_status"],
                "page_start": candidate["page_start"],
                "page_end": candidate["page_end"],
                "verification": unverified("awaiting_mechanical_location"),
                "note": candidate.get("note", "Fresh isolated candidate evidence."),
            }
            verified = verify_evidence(draft, source_text)
            if verified["verification"]["status"] == "unverified":
                raise ContractError(
                    f"Evidence {candidate['evidence_id']} could not be mechanically located"
                )
            evidence_rows.append(verified)
            relation_evidence_ids.append(verified["evidence_id"])

        relation_rows.append(
            {
                "relation_id": proposed["relation_id"],
                "source_entity_id": source_entity_id,
                "target_entity_id": target_entity_id,
                "relation_type": proposed["relation_type"],
                "member_subtype": proposed["member_subtype"],
                "direction": proposed["direction"],
                "confidence": proposed["confidence"],
                "evidence_ids": relation_evidence_ids,
                "status": "candidate",
                "extractor": worker,
                "verifier": None,
                "note": proposed.get("note", "Fresh isolated candidate; not yet reviewed."),
            }
        )

    shard = {
        "schema_version": "shard-v1",
        "run_id": config["run_id"],
        "config_sha256": run_config_digest(config),
        "shard_id": assignment["shard_id"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "worker_id": worker["worker_id"],
        "status": "READY",
        "source": source,
        "source_text": source_text,
        "entities": sorted(entities.values(), key=lambda row: row["entity_id"]),
        "evidence": sorted(evidence_rows, key=lambda row: row["evidence_id"]),
        "relations": sorted(relation_rows, key=lambda row: row["relation_id"]),
        "error": None,
    }
    validate_shard(shard, config)
    return shard


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build one hash-bound, mechanically located candidate shard"
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("source_text", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    shard = build_candidate_shard(
        config=load_json(args.config),
        source=load_json(args.source),
        source_text=load_json(args.source_text),
        registry=load_json(args.registry),
        spec=load_json(args.spec),
    )
    atomic_write_json(args.output, shard)
    print(
        f"Built {shard['shard_id']}: {len(shard['relations'])} candidates, "
        f"{len(shard['evidence'])} located evidence records"
    )


if __name__ == "__main__":
    main()
