from __future__ import annotations

import copy
import unittest
from pathlib import Path

from pipeline.candidate_shard import build_candidate_shard
from pipeline.contracts import ContractError
from pipeline.io import load_json
from pipeline.review_shard import review_candidate_shard


ROOT = Path(__file__).resolve().parents[1]


class CandidateReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = load_json(ROOT / "data" / "demo" / "ingested" / "source.json")
        cls.source_text = load_json(
            ROOT / "data" / "demo" / "ingested" / "source-text.json"
        )
        cls.registry = load_json(ROOT / "data" / "demo" / "published.json")["entities"]
        cls.config = {
            "run_id": "run:candidate-review-test",
            "protocol_version": "protocol-v1",
            "taxonomy_version": "taxonomy-v1",
            "isolation_attestation": "Synthetic fixture only.",
            "luna_gate": {
                "min_precision": 0.9,
                "min_recall": 0.8,
                "max_unresolved_rate": 0.1,
                "locked": True,
            },
            "assignments": [
                {
                    "shard_id": "shard:candidate-review-test-1",
                    "source_id": cls.source["source_id"],
                    "source_sha256": cls.source["sha256"],
                    "worker_id": "terra-test-worker",
                }
            ],
        }
        cls.spec = {
            "spec_version": "candidate-spec-v1",
            "source_id": cls.source["source_id"],
            "source_sha256": cls.source["sha256"],
            "worker": {
                "model": "codex-terra-role",
                "prompt_version": "terra-candidate-v1",
                "worker_id": "terra-test-worker",
            },
            "relations": [
                {
                    "relation_id": "rel:test_bora_aylin_teacher",
                    "source_entity_id": "person:bora_example",
                    "target_entity_id": "person:aylin_demo",
                    "relation_type": "student_teacher",
                    "member_subtype": None,
                    "direction": "directed",
                    "confidence": 0.99,
                    "evidence": [
                        {
                            "evidence_id": "evidence:test_bora_aylin_teacher:1",
                            "quote": "Professor Bora Example supervised Aylin Demo's doctoral work.",
                            "page_status": "not_paginated",
                            "page_start": None,
                            "page_end": None,
                        }
                    ],
                }
            ],
        }

    def build(self, spec=None):
        return build_candidate_shard(
            config=self.config,
            source=self.source,
            source_text=self.source_text,
            registry=self.registry,
            spec=spec if spec is not None else self.spec,
        )

    def review(self, shard, decisions=None):
        payload = {
            "review_version": "review-decisions-v1",
            "run_id": self.config["run_id"],
            "reviewer": {
                "model": "codex-sol-role",
                "prompt_version": "sol-review-v1",
                "worker_id": "sol-test-reviewer",
            },
            "decisions": decisions
            if decisions is not None
            else [
                {
                    "relation_id": "rel:test_bora_aylin_teacher",
                    "verdict": "accept",
                }
            ],
        }
        return review_candidate_shard(shard, self.config, payload)

    def test_builds_located_isolated_candidate(self) -> None:
        shard = self.build()
        self.assertEqual(shard["status"], "READY")
        self.assertEqual(len(shard["relations"]), 1)
        self.assertEqual(shard["relations"][0]["status"], "candidate")
        self.assertEqual(shard["evidence"][0]["verification"]["status"], "exact_match")

    def test_unlocatable_quote_fails_closed(self) -> None:
        spec = copy.deepcopy(self.spec)
        spec["relations"][0]["evidence"][0]["quote"] = "Invented quotation"
        with self.assertRaises(ContractError):
            self.build(spec)

    def test_independent_review_accepts_candidate(self) -> None:
        reviewed = self.review(self.build())
        relation = reviewed["relations"][0]
        self.assertEqual(relation["status"], "accepted")
        self.assertEqual(relation["verifier"]["verdict"], "accept")
        self.assertNotEqual(
            relation["extractor"]["worker_id"], relation["verifier"]["worker_id"]
        )

    def test_review_must_cover_every_candidate(self) -> None:
        with self.assertRaises(ContractError):
            self.review(self.build(), decisions=[])

    def test_extractor_cannot_self_review(self) -> None:
        shard = self.build()
        payload = {
            "review_version": "review-decisions-v1",
            "run_id": self.config["run_id"],
            "reviewer": {
                "model": "codex-sol-role",
                "prompt_version": "sol-review-v1",
                "worker_id": "terra-test-worker",
            },
            "decisions": [
                {
                    "relation_id": "rel:test_bora_aylin_teacher",
                    "verdict": "accept",
                }
            ],
        }
        with self.assertRaises(ContractError):
            review_candidate_shard(shard, self.config, payload)


if __name__ == "__main__":
    unittest.main()
