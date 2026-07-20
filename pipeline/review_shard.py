from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError, validate_payload
from pipeline.io import atomic_write_json, load_json
from pipeline.shards import validate_shard


STATUS_BY_VERDICT = {
    "accept": "accepted",
    "reject": "rejected",
    "review": "review",
}


def review_candidate_shard(
    shard: dict[str, Any],
    config: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    """Apply one complete, independent verdict set to a candidate shard."""

    validate_shard(shard, config)
    validate_payload("review-decisions", review)
    if review["run_id"] != shard["run_id"]:
        raise ContractError("Review decisions belong to another run")
    reviewer = review["reviewer"]
    if reviewer["worker_id"] == shard["worker_id"]:
        raise ContractError("Extraction worker cannot review its own shard")
    relation_ids = {row["relation_id"] for row in shard["relations"]}
    decision_ids = [row["relation_id"] for row in review["decisions"]]
    if len(decision_ids) != len(set(decision_ids)):
        raise ContractError("Review decisions contain a duplicate relation ID")
    missing = relation_ids - set(decision_ids)
    foreign = set(decision_ids) - relation_ids
    if missing or foreign:
        raise ContractError(
            f"Review decision set mismatch; missing={sorted(missing)}, foreign={sorted(foreign)}"
        )
    decision_by_id = {row["relation_id"]: row for row in review["decisions"]}

    result = copy.deepcopy(shard)
    for relation in result["relations"]:
        if relation["status"] != "candidate" or relation["verifier"] is not None:
            raise ContractError(
                f"Relation {relation['relation_id']} is not an unreviewed candidate"
            )
        decision = decision_by_id[relation["relation_id"]]
        verdict = decision["verdict"]
        relation["status"] = STATUS_BY_VERDICT[verdict]
        relation["verifier"] = {**reviewer, "verdict": verdict}
        if decision.get("note"):
            relation["note"] = decision["note"]

    validate_shard(result, config)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply an independent, complete review to one candidate shard"
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("shard", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = review_candidate_shard(
        load_json(args.shard),
        load_json(args.config),
        load_json(args.review),
    )
    atomic_write_json(args.output, result)
    counts = {
        status: sum(row["status"] == status for row in result["relations"])
        for status in ("accepted", "rejected", "review")
    }
    print(f"Reviewed {result['shard_id']}: {counts}")


if __name__ == "__main__":
    main()
