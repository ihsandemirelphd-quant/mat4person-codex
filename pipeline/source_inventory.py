from __future__ import annotations

from typing import Any

from pipeline.contracts import ContractError, validate_payload


def validate_source_inventory(
    records: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    sun_ids: list[str],
) -> dict[str, int]:
    """Validate the metadata-only pilot queue without creating source claims."""

    if len(sun_ids) != 4 or len(set(sun_ids)) != 4:
        raise ContractError("Presentation must configure exactly four unique Sun IDs")

    entity_by_id = {row["entity_id"]: row for row in entities}
    if len(entity_by_id) != len(entities):
        raise ContractError("Registry contains duplicate entity IDs")

    candidate_ids: set[str] = set()
    anchors: set[str] = set()
    for record in records:
        validate_payload("source-candidate", record)
        candidate_id = record["source_candidate_id"]
        if candidate_id in candidate_ids:
            raise ContractError(f"Duplicate source candidate {candidate_id}")
        candidate_ids.add(candidate_id)

        anchor_id = record["anchor_entity_id"]
        entity = entity_by_id.get(anchor_id)
        if entity is None or entity["kind"] != "person":
            raise ContractError(f"Source candidate references unknown person {anchor_id}")
        if record["anchor_name"] != entity["canonical_name"]:
            raise ContractError(f"Source candidate has stale anchor name for {anchor_id}")
        anchors.add(anchor_id)

        if (
            record["ingestion_status"] == "license_ready_download_pending"
            and (
                record["rights_status"] != "cc_by_4_0"
                or not isinstance(record["rights_url"], str)
                or not record["rights_url"].startswith("https://")
            )
        ):
            raise ContractError(
                f"Source candidate {candidate_id} is marked ready without a reusable licence reference"
            )

    expected_anchors = set(sun_ids)
    if anchors != expected_anchors:
        missing = sorted(expected_anchors - anchors)
        extra = sorted(anchors - expected_anchors)
        raise ContractError(
            f"Source queue must cover each Sun exactly once; missing={missing}, extra={extra}"
        )
    if len(records) != len(expected_anchors):
        raise ContractError("Source queue must contain one record per Sun")

    return {
        "records": len(records),
        "anchors": len(anchors),
        "license_ready": sum(
            row["ingestion_status"] == "license_ready_download_pending"
            for row in records
        ),
        "evidence_claims": sum(row["evidence_claims"] for row in records),
        "relationship_claims": sum(row["relationship_claims"] for row in records),
    }
