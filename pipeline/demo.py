from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pipeline.evaluate import evaluate
from pipeline.ingest import ingest_text
from pipeline.io import atomic_write_json
from pipeline.shards import merge_shards, run_config_digest
from pipeline.verification import unverified, verify_evidence


def build_demo(root: Path) -> None:
    demo = root / "data" / "demo"
    source, source_text = ingest_text(
        demo / "input" / "synthetic-note.txt",
        source_id="source:synthetic_meridian_note",
        title="Synthetic Meridian Institute note",
        language="en",
        output_dir=demo / "ingested",
        rights_note="Original synthetic text released with this repository; not a historical source.",
    )
    entities = [
        {"entity_id": "person:aylin_demo", "kind": "person", "canonical_name": "Aylin Demo", "aliases": [], "registry_version": "demo-v1"},
        {"entity_id": "person:bora_example", "kind": "person", "canonical_name": "Bora Example", "aliases": [], "registry_version": "demo-v1"},
        {"entity_id": "person:cem_sample", "kind": "person", "canonical_name": "Cem Sample", "aliases": [], "registry_version": "demo-v1"},
        {"entity_id": "event:solstice_workshop", "kind": "event", "canonical_name": "Solstice Mathematics Workshop", "aliases": [], "registry_version": "demo-v1"},
    ]
    quotes = [
        ("evidence:synthetic_meridian_note:1", "Professor Bora Example supervised Aylin Demo's doctoral work."),
        ("evidence:synthetic_meridian_note:2", "Aylin Demo and Bora Example later co-authored the imaginary paper \"Gardens of Symmetry\"."),
        ("evidence:synthetic_meridian_note:3", "Aylin Demo and Cem Sample appeared together at the fictional Solstice Mathematics Workshop."),
    ]
    evidence: list[dict[str, Any]] = []
    for evidence_id, quote in quotes:
        evidence.append(
            verify_evidence(
                {
                    "evidence_id": evidence_id,
                    "source_id": source["source_id"],
                    "source_sha256": "0" * 64,
                    "text_artifact_sha256": "0" * 64,
                    "quote": quote,
                    "quote_sha256": "0" * 64,
                    "page_status": "not_paginated",
                    "page_start": None,
                    "page_end": None,
                    "verification": unverified("pending"),
                    "note": "Synthetic demonstration evidence; not a historical claim.",
                },
                source_text,
            )
        )
    extractor = {"model": "gpt-5.6-luna", "prompt_version": "demo-candidate-v1", "worker_id": "luna-demo-worker"}
    verifier = {"model": "gpt-5.6-sol", "prompt_version": "demo-verify-v1", "worker_id": "sol-demo-reviewer", "verdict": "accept"}
    relations = [
        {
            "relation_id": "rel:demo_bora_aylin_teacher", "source_entity_id": "person:bora_example",
            "target_entity_id": "person:aylin_demo", "relation_type": "student_teacher",
            "member_subtype": None, "direction": "directed", "confidence": 1.0,
            "evidence_ids": [evidence[0]["evidence_id"]], "status": "accepted",
            "extractor": extractor, "verifier": verifier, "note": "Synthetic demonstration relation."
        },
        {
            "relation_id": "rel:demo_aylin_bora_output", "source_entity_id": "person:aylin_demo",
            "target_entity_id": "person:bora_example", "relation_type": "academic_output",
            "member_subtype": None, "direction": "undirected", "confidence": 1.0,
            "evidence_ids": [evidence[1]["evidence_id"]], "status": "accepted",
            "extractor": extractor, "verifier": verifier, "note": "Synthetic demonstration relation."
        },
        {
            "relation_id": "rel:demo_aylin_cem_context", "source_entity_id": "person:aylin_demo",
            "target_entity_id": "person:cem_sample", "relation_type": "in_same_context",
            "member_subtype": None, "direction": "undirected", "confidence": 1.0,
            "evidence_ids": [evidence[2]["evidence_id"]], "status": "accepted",
            "extractor": extractor, "verifier": verifier, "note": "Synthetic demonstration relation."
        },
    ]
    run = {
        "run_id": "run:synthetic-demo-v1", "protocol_version": "protocol-v1",
        "taxonomy_version": "taxonomy-v1",
        "isolation_attestation": "Synthetic demo only; no prior relation outputs were used.",
        "luna_gate": {"min_precision": 0.9, "min_recall": 0.8, "max_unresolved_rate": 0.1, "locked": True},
        "assignments": [{"shard_id": "shard:synthetic-demo-1", "source_id": source["source_id"], "source_sha256": source["sha256"], "worker_id": "luna-demo-worker"}],
    }
    shard = {
        "schema_version": "shard-v1", "run_id": run["run_id"], "config_sha256": run_config_digest(run),
        "shard_id": "shard:synthetic-demo-1", "source_id": source["source_id"],
        "source_sha256": source["sha256"], "worker_id": "luna-demo-worker", "status": "READY",
        "source": source, "source_text": source_text, "entities": entities,
        "evidence": evidence, "relations": relations, "error": None
    }
    atomic_write_json(demo / "run.json", run)
    atomic_write_json(demo / "shards" / "synthetic-demo.json", shard)
    merge_shards(demo / "run.json", demo / "shards", demo / "bundle", replace=True)
    gold = [
        {
            "case_id": f"case:synthetic:{index}", "source_id": source["source_id"],
            "source_sha256": source["sha256"], "source_entity_id": relation["source_entity_id"],
            "target_entity_id": relation["target_entity_id"], "relation_type": relation["relation_type"],
            "member_subtype": relation["member_subtype"], "direction": relation["direction"],
            "label": "positive", "split": "pilot", "annotators": ["human:synthetic-author"],
            "note": "Synthetic gold label; not historical evidence."
        }
        for index, relation in enumerate(relations, start=1)
    ]
    metrics = evaluate(gold, relations, evidence, {"min_precision": 0.9, "min_recall": 0.8, "max_unresolved_rate": 0.1})
    metrics["scope"] = "synthetic_pipeline_self_test"
    atomic_write_json(demo / "gold.json", gold)
    atomic_write_json(demo / "metrics.json", metrics)
    atomic_write_json(
        demo / "published.json",
        {
            "title": "Synthetic Meridian demonstration",
            "disclaimer": "All names, institutions, events, quotations, and relations in this demo are fictional.",
            "run": run, "metrics": metrics, "source": source, "source_text": source_text,
            "entities": entities, "evidence": evidence, "relations": relations
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the deterministic synthetic demonstration bundle")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    build_demo(args.repo.resolve())
    print("Synthetic demonstration bundle is ready")


if __name__ == "__main__":
    main()
