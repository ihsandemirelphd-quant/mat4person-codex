from __future__ import annotations

import copy
import unittest
from pathlib import Path

from pipeline.contracts import ContractError, load_json, validate_bundle, validate_payload


FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = load_json(FIXTURES / "source.json")
        cls.entities = load_json(FIXTURES / "entities.json")
        cls.source_text = load_json(FIXTURES / "source-text.json")
        cls.evidence = load_json(FIXTURES / "evidence.json")
        cls.relation = load_json(FIXTURES / "relation.json")

    def validate(self, **overrides: object) -> None:
        validate_bundle(
            sources=overrides.get("sources", [self.source]),
            entities=overrides.get("entities", self.entities),
            source_texts=overrides.get("source_texts", [self.source_text]),
            evidence=overrides.get("evidence", [self.evidence]),
            relations=overrides.get("relations", [self.relation]),
        )

    def test_valid_bundle(self) -> None:
        self.validate()

    def test_evidence_rejects_whitespace_quote(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["quote"] = "   "
        evidence["quote_sha256"] = "0" * 64
        with self.assertRaises(ContractError):
            self.validate(evidence=[evidence])

    def test_exact_page_requires_page_numbers(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["page_start"] = None
        evidence["page_end"] = None
        with self.assertRaises(ContractError):
            validate_payload("evidence", evidence)

    def test_unknown_evidence_reference_is_rejected(self) -> None:
        relation = copy.deepcopy(self.relation)
        relation["evidence_ids"] = ["evidence:missing:1"]
        with self.assertRaises(ContractError):
            self.validate(relations=[relation])

    def test_accepted_relation_rejects_unverified_evidence(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["verification"] = {
            "status": "unverified", "method": "none",
            "normalization_profile_version": None, "page_number": None,
            "char_start": None, "char_end": None, "match_count": 0,
            "matched_text_sha256": None, "verifier": "code:verify-quotes-v1",
            "reason": "quote_not_found"
        }
        with self.assertRaises(ContractError):
            self.validate(evidence=[evidence])

    def test_duplicate_relation_id_is_rejected(self) -> None:
        with self.assertRaises(ContractError):
            self.validate(relations=[self.relation, copy.deepcopy(self.relation)])

    def test_unknown_entity_is_rejected(self) -> None:
        relation = copy.deepcopy(self.relation)
        relation["target_entity_id"] = "person:missing"
        with self.assertRaises(ContractError):
            self.validate(relations=[relation])

    def test_self_verification_is_rejected(self) -> None:
        relation = copy.deepcopy(self.relation)
        relation["verifier"]["worker_id"] = relation["extractor"]["worker_id"]
        with self.assertRaises(ContractError):
            self.validate(relations=[relation])

    def test_tampered_exact_span_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["verification"]["char_end"] -= 1
        with self.assertRaises(ContractError):
            self.validate(evidence=[evidence])

    def test_stale_text_hash_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["text_artifact_sha256"] = "b" * 64
        with self.assertRaises(ContractError):
            self.validate(evidence=[evidence])

    def test_unpaginated_source_rejects_exact_page_claim(self) -> None:
        source = copy.deepcopy(self.source)
        source["page_count"] = None
        source["content_kind"] = "plain_text"
        with self.assertRaises(ContractError):
            self.validate(sources=[source])

    def test_seed_registry_matches_entity_contract(self) -> None:
        seed = load_json(FIXTURES.parents[2] / "data" / "seed" / "entities.json")
        self.assertEqual(len(seed), 19)
        for entity in seed:
            validate_payload("entity", entity)


if __name__ == "__main__":
    unittest.main()
