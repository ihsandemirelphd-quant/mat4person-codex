from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from pipeline.contracts import ContractError, load_json
from pipeline.evaluate import evaluate
from pipeline.ingest import ingest_text
from pipeline.io import atomic_write_json, canonical_sha256
from pipeline.shards import merge_shards, run_config_digest, validate_shard
from pipeline.verification import unverified, verify_evidence


FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


class PipelineTests(unittest.TestCase):
    def test_ingestion_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "note.txt"
            source_path.write_text("Page one.\fPage two.", encoding="utf-8")
            for name in ("a", "b"):
                ingest_text(
                    source_path,
                    source_id="source:deterministic_note",
                    title="Deterministic note",
                    language="en",
                    output_dir=root / name,
                )
            self.assertEqual((root / "a/source.json").read_bytes(), (root / "b/source.json").read_bytes())
            self.assertEqual((root / "a/source-text.json").read_bytes(), (root / "b/source-text.json").read_bytes())

    def test_exact_and_normalized_quote_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "note.txt"
            source_path.write_text("Bora   Example supervised\nAylin Demo.", encoding="utf-8")
            source, source_text = ingest_text(
                source_path,
                source_id="source:spacing_note",
                title="Spacing note",
                language="en",
                output_dir=root / "ingested",
            )
            base = {
                "evidence_id": "evidence:spacing_note:1",
                "source_id": source["source_id"],
                "source_sha256": "0" * 64,
                "text_artifact_sha256": "0" * 64,
                "quote": "Bora Example supervised Aylin Demo.",
                "quote_sha256": "0" * 64,
                "page_status": "exact",
                "page_start": 1,
                "page_end": 1,
                "verification": unverified("pending"),
            }
            normalized = verify_evidence(base, source_text)
            self.assertEqual(normalized["verification"]["status"], "normalized_match")
            exact = copy.deepcopy(base)
            exact["quote"] = "Bora   Example supervised\nAylin Demo."
            exact = verify_evidence(exact, source_text)
            self.assertEqual(exact["verification"]["status"], "exact_match")

    def _fixture_shard(self) -> tuple[dict, dict]:
        source = load_json(FIXTURES / "source.json")
        config = {
            "run_id": "run:synthetic-v1",
            "protocol_version": "protocol-v1",
            "taxonomy_version": "taxonomy-v1",
            "isolation_attestation": "No prior relation outputs were exposed to workers.",
            "luna_gate": {
                "min_precision": 0.9,
                "min_recall": 0.8,
                "max_unresolved_rate": 0.1,
                "locked": True,
            },
            "assignments": [{
                "shard_id": "shard:synthetic-1",
                "source_id": source["source_id"],
                "source_sha256": source["sha256"],
                "worker_id": "extractor-a",
            }],
        }
        shard = {
            "schema_version": "shard-v1",
            "run_id": config["run_id"],
            "config_sha256": run_config_digest(config),
            "shard_id": "shard:synthetic-1",
            "source_id": source["source_id"],
            "source_sha256": source["sha256"],
            "worker_id": "extractor-a",
            "status": "READY",
            "source": source,
            "source_text": load_json(FIXTURES / "source-text.json"),
            "entities": load_json(FIXTURES / "entities.json"),
            "evidence": [load_json(FIXTURES / "evidence.json")],
            "relations": [load_json(FIXTURES / "relation.json")],
            "error": None,
        }
        return config, shard

    def test_shard_merge_is_deterministic_and_gate_passes(self) -> None:
        config, shard = self._fixture_shard()
        validate_shard(shard, config)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            atomic_write_json(root / "run.json", config)
            atomic_write_json(root / "shards/one.json", shard)
            first = merge_shards(root / "run.json", root / "shards", root / "bundle")
            second = merge_shards(root / "run.json", root / "shards", root / "bundle")
            self.assertEqual(canonical_sha256(first), canonical_sha256(second))
            gold = [{
                "case_id": "case:synthetic:1",
                "source_id": shard["source_id"],
                "source_sha256": shard["source_sha256"],
                "source_entity_id": "person:bora_example",
                "target_entity_id": "person:aylin_demo",
                "relation_type": "student_teacher",
                "member_subtype": None,
                "direction": "directed",
                "label": "positive",
                "split": "pilot",
                "annotators": ["human:fixture"],
            }]
            metrics = evaluate(
                gold,
                load_json(root / "bundle/relations.json"),
                load_json(root / "bundle/evidence.json"),
                {"min_precision": 0.9, "min_recall": 0.8, "max_unresolved_rate": 0.1},
            )
            self.assertTrue(metrics["gate_pass"])

    def test_missing_shard_fails_closed(self) -> None:
        config, _ = self._fixture_shard()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "shards").mkdir()
            atomic_write_json(root / "run.json", config)
            with self.assertRaises(ContractError):
                merge_shards(root / "run.json", root / "shards", root / "bundle")


if __name__ == "__main__":
    unittest.main()
