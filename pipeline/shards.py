from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError, validate_bundle, validate_payload
from pipeline.io import atomic_write_json, canonical_json_bytes, canonical_sha256, load_json


def run_config_digest(config: dict[str, Any]) -> str:
    return canonical_sha256(config)


def validate_shard(shard: dict[str, Any], config: dict[str, Any]) -> None:
    validate_payload("run", config)
    validate_payload("shard", shard)
    if shard["run_id"] != config["run_id"]:
        raise ContractError(f"Shard {shard['shard_id']} belongs to another run")
    if shard["config_sha256"] != run_config_digest(config):
        raise ContractError(f"Shard {shard['shard_id']} has a stale run configuration")
    assignments = {row["shard_id"]: row for row in config["assignments"]}
    assignment = assignments.get(shard["shard_id"])
    if assignment is None:
        raise ContractError(f"Shard {shard['shard_id']} was not assigned")
    for field in ("source_id", "source_sha256", "worker_id"):
        if shard[field] != assignment[field]:
            raise ContractError(f"Shard {shard['shard_id']} violates its {field} assignment")
    if shard["status"] != "READY":
        raise ContractError(f"Shard {shard['shard_id']} is not READY")
    if shard["source"]["source_id"] != shard["source_id"]:
        raise ContractError(f"Shard {shard['shard_id']} contains a foreign source")
    validate_bundle(
        sources=[shard["source"]],
        entities=shard["entities"],
        source_texts=[shard["source_text"]],
        evidence=shard["evidence"],
        relations=shard["relations"],
    )
    if any(row["source_id"] != shard["source_id"] for row in shard["evidence"]):
        raise ContractError(f"Shard {shard['shard_id']} contains foreign evidence")


def _relation_key(row: dict[str, Any]) -> tuple[Any, ...]:
    endpoints = [row["source_entity_id"], row["target_entity_id"]]
    if row["direction"] == "undirected":
        endpoints.sort()
    return (
        endpoints[0],
        endpoints[1],
        row["relation_type"],
        row["member_subtype"],
        row["direction"],
    )


def merge_shards(
    config_path: Path, shard_dir: Path, output_dir: Path, *, replace: bool = False
) -> dict[str, Any]:
    config = load_json(config_path)
    validate_payload("run", config)
    expected = {row["shard_id"] for row in config["assignments"]}
    shard_paths = sorted(shard_dir.glob("*.json"))
    shards = [load_json(path) for path in shard_paths]
    actual = [row.get("shard_id") for row in shards]
    if len(actual) != len(set(actual)):
        raise ContractError("Duplicate shard_id")
    missing = expected - set(actual)
    foreign = set(actual) - expected
    if missing or foreign:
        raise ContractError(f"Shard set mismatch; missing={sorted(missing)}, foreign={sorted(foreign)}")
    for shard in shards:
        validate_shard(shard, config)

    sources = sorted((row["source"] for row in shards), key=lambda row: row["source_id"])
    source_texts = sorted((row["source_text"] for row in shards), key=lambda row: row["source_id"])
    entities_by_id: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    relation_keys: dict[tuple[Any, ...], dict[str, Any]] = {}
    for shard in shards:
        for entity in shard["entities"]:
            existing = entities_by_id.get(entity["entity_id"])
            if existing is not None and canonical_json_bytes(existing) != canonical_json_bytes(entity):
                raise ContractError(f"Divergent entity collision: {entity['entity_id']}")
            entities_by_id[entity["entity_id"]] = entity
        evidence.extend(shard["evidence"])
        for relation in shard["relations"]:
            key = _relation_key(relation)
            if key in relation_keys:
                raise ContractError(f"Divergent relation collision: {key}")
            relation_keys[key] = relation
            relations.append(relation)

    entities = sorted(entities_by_id.values(), key=lambda row: row["entity_id"])
    evidence.sort(key=lambda row: row["evidence_id"])
    relations.sort(key=lambda row: row["relation_id"])
    validate_bundle(
        sources=sources,
        entities=entities,
        source_texts=source_texts,
        evidence=evidence,
        relations=relations,
    )
    report = {
        "merge_policy": "fail-closed-v1",
        "run_id": config["run_id"],
        "config_sha256": run_config_digest(config),
        "shards": [
            {"shard_id": row["shard_id"], "sha256": canonical_sha256(row)}
            for row in sorted(shards, key=lambda row: row["shard_id"])
        ],
        "counts": {
            "sources": len(sources),
            "entities": len(entities),
            "evidence": len(evidence),
            "relations": len(relations),
        },
    }
    files = {
        "sources.json": sources,
        "source-texts.json": source_texts,
        "entities.json": entities,
        "evidence.json": evidence,
        "relations.json": relations,
        "merge-report.json": report,
    }
    temporary: Path | None = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent)
    )
    try:
        for name, value in files.items():
            atomic_write_json(temporary / name, value)
        if output_dir.exists():
            identical = all(
                (output_dir / name).exists()
                and (output_dir / name).read_bytes() == (temporary / name).read_bytes()
                for name in files
            )
            if identical:
                return report
            if not replace:
                raise ContractError(f"Output directory already exists with different content: {output_dir}")
            shutil.rmtree(output_dir)
        temporary.replace(output_dir)
        temporary = None
        return report
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)
