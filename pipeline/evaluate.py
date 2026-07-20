from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError, validate_payload
from pipeline.io import atomic_write_json, load_json


def relation_key(
    source_id: str,
    source_entity_id: str,
    target_entity_id: str,
    relation_type: str,
    member_subtype: str | None,
    direction: str,
) -> tuple[Any, ...]:
    endpoints = [source_entity_id, target_entity_id]
    if direction == "undirected":
        endpoints.sort()
    return (source_id, endpoints[0], endpoints[1], relation_type, member_subtype, direction)


def evaluate(
    gold: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    gate: dict[str, float],
) -> dict[str, Any]:
    for item in gold:
        validate_payload("gold-item", item)
    split_by_source: dict[str, str] = {}
    for item in gold:
        previous = split_by_source.setdefault(item["source_id"], item["split"])
        if previous != item["split"]:
            raise ContractError(f"Source-level split leakage: {item['source_id']}")
    gold_keys = {
        relation_key(
            item["source_id"], item["source_entity_id"], item["target_entity_id"],
            item["relation_type"], item["member_subtype"], item["direction"]
        ): item["label"]
        for item in gold
    }
    evidence_source = {item["evidence_id"]: item["source_id"] for item in evidence}
    predicted: set[tuple[Any, ...]] = set()
    for row in relations:
        if row["status"] != "accepted":
            continue
        sources = {evidence_source[value] for value in row["evidence_ids"] if value in evidence_source}
        for source_id in sources:
            predicted.add(
                relation_key(
                    source_id, row["source_entity_id"], row["target_entity_id"],
                    row["relation_type"], row["member_subtype"], row["direction"]
                )
            )
    positives = {key for key, label in gold_keys.items() if label == "positive"}
    negatives = {key for key, label in gold_keys.items() if label == "negative"}
    ambiguous = {key for key, label in gold_keys.items() if label == "ambiguous"}
    tp = len(predicted & positives)
    fp = len(predicted & negatives) + len(predicted - set(gold_keys))
    fn = len(positives - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    unresolved_rate = len(ambiguous) / len(gold_keys) if gold_keys else 0.0
    gate_pass = (
        precision >= gate["min_precision"]
        and recall >= gate["min_recall"]
        and unresolved_rate <= gate["max_unresolved_rate"]
    )
    return {
        "metric_version": "relation-exact-v1",
        "counts": {"tp": tp, "fp": fp, "fn": fn, "ambiguous": len(ambiguous)},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "unresolved_rate": unresolved_rate,
        "gate": gate,
        "gate_pass": gate_pass,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate accepted relations against source-level gold labels")
    parser.add_argument("gold", type=Path)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--min-precision", type=float, default=0.9)
    parser.add_argument("--min-recall", type=float, default=0.8)
    parser.add_argument("--max-unresolved-rate", type=float, default=0.1)
    args = parser.parse_args()
    result = evaluate(
        load_json(args.gold),
        load_json(args.bundle / "relations.json"),
        load_json(args.bundle / "evidence.json"),
        {
            "min_precision": args.min_precision,
            "min_recall": args.min_recall,
            "max_unresolved_rate": args.max_unresolved_rate,
        },
    )
    atomic_write_json(args.output, result)
    print(f"Gold evaluation gate: {'PASS' if result['gate_pass'] else 'FAIL'}")


if __name__ == "__main__":
    main()
