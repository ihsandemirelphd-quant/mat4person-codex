from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError
from pipeline.io import canonical_sha256, load_json, sha256_text
from pipeline.pilot_review_report import (
    build_pilot_candidate_review_report,
    validate_pilot_candidate_review_report,
)
from pipeline.shards import run_config_digest
from pipeline.source_text import artifact_digest


ROOT = Path(__file__).resolve().parents[1]
IKEDA_SOURCE_ID = "source:v2_ikeda_koc_life_devoted_2003_pdf"
FGE_SOURCE_ID = "source:v2_fge_research_staff_pdf"


def _make_shard(
    config: dict[str, Any],
    assignment: dict[str, Any],
    *,
    candidate_count: int,
    accepted_count: int,
) -> dict[str, Any]:
    source_id = assignment["source_id"]
    stem = "ikeda" if source_id == IKEDA_SOURCE_ID else "fge"
    quotes = [f"Private source excerpt {stem} {index}." for index in range(candidate_count)]
    page_text = "\n".join(quotes)
    page = {
        "page_number": 1,
        "printed_label": "1",
        "text": page_text,
        "text_sha256": sha256_text(page_text),
    }
    source_text = {
        "source_id": source_id,
        "source_sha256": assignment["source_sha256"],
        "artifact_sha256": "0" * 64,
        "ingest_version": "text-v1",
        "offset_unit": "unicode_code_point_half_open",
        "pages": [page],
    }
    source_text["artifact_sha256"] = artifact_digest(source_text)
    source = {
        "source_id": source_id,
        "title": f"Private synthetic {stem} source",
        "source_type": "pdf",
        "access": {"kind": "private", "uri": None},
        "sha256": assignment["source_sha256"],
        "language": "en",
        "page_count": 1,
        "content_kind": "pdf_text",
        "ingest_version": "text-v1",
        "rights_note": "Private unit-test fixture.",
    }
    entities = [
        {
            "entity_id": "person:synthetic_person",
            "kind": "person",
            "canonical_name": "Private Person One",
            "aliases": [],
            "registry_version": "test-v1",
        },
        {
            "entity_id": "institute:synthetic_institute",
            "kind": "institute",
            "canonical_name": "Private Institute One",
            "aliases": [],
            "registry_version": "test-v1",
        },
    ]
    evidence = []
    relations = []
    offset = 0
    for index, quote in enumerate(quotes):
        evidence_id = f"evidence:{stem}_{index}"
        evidence.append(
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "source_sha256": assignment["source_sha256"],
                "text_artifact_sha256": source_text["artifact_sha256"],
                "quote": quote,
                "quote_sha256": sha256_text(quote),
                "page_status": "exact",
                "page_start": 1,
                "page_end": 1,
                "verification": {
                    "status": "exact_match",
                    "method": "exact-v1",
                    "normalization_profile_version": None,
                    "page_number": 1,
                    "char_start": offset,
                    "char_end": offset + len(quote),
                    "match_count": 1,
                    "matched_text_sha256": sha256_text(quote),
                    "verifier": "mechanical-test-v1",
                    "reason": None,
                },
            }
        )
        verdict = "accept" if index < accepted_count else "review"
        status = "accepted" if verdict == "accept" else "review"
        relations.append(
            {
                "relation_id": f"rel:{stem}_{index}",
                "source_entity_id": "person:synthetic_person",
                "target_entity_id": "institute:synthetic_institute",
                "relation_type": "person_institute_presence",
                "member_subtype": None,
                "direction": "directed",
                "confidence": 0.9,
                "evidence_ids": [evidence_id],
                "status": status,
                "extractor": {
                    "model": "codex-terra-role",
                    "prompt_version": "terra-candidate-v1",
                    "worker_id": assignment["worker_id"],
                    "response_sha256": canonical_sha256(
                        {"source_id": source_id, "index": index}
                    ),
                },
                "verifier": {
                    "model": "codex-sol-role",
                    "prompt_version": "sol-review-v1",
                    "worker_id": "sol-independent-reviewer",
                    "verdict": verdict,
                },
            }
        )
        offset += len(quote) + 1

    return {
        "schema_version": "shard-v1",
        "run_id": config["run_id"],
        "config_sha256": run_config_digest(config),
        "shard_id": assignment["shard_id"],
        "source_id": source_id,
        "source_sha256": assignment["source_sha256"],
        "worker_id": assignment["worker_id"],
        "status": "READY",
        "source": source,
        "source_text": source_text,
        "entities": entities,
        "evidence": evidence,
        "relations": relations,
    }


def _make_gold(config: dict[str, Any]) -> list[dict[str, Any]]:
    counts = {IKEDA_SOURCE_ID: 8, FGE_SOURCE_ID: 7}
    splits = {IKEDA_SOURCE_ID: "pilot", FGE_SOURCE_ID: "validation"}
    hashes = {
        row["source_id"]: row["source_sha256"] for row in config["assignments"]
    }
    result = []
    for source_id, count in counts.items():
        stem = "ikeda" if source_id == IKEDA_SOURCE_ID else "fge"
        for index in range(count):
            result.append(
                {
                    "case_id": f"case:draft_{stem}_{index}",
                    "source_id": source_id,
                    "source_sha256": hashes[source_id],
                    "source_entity_id": "person:synthetic_person",
                    "target_entity_id": "institute:synthetic_institute",
                    "relation_type": "person_institute_presence",
                    "member_subtype": None,
                    "direction": "directed",
                    "label": "positive",
                    "split": splits[source_id],
                    "annotators": ["ai-draft:terra-test", "ai-review:sol-test"],
                    "note": "DRAFT ONLY; not human-reviewed. Synthetic unit-test case.",
                }
            )
    return result


def _fixture() -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]
]:
    manifest = load_json(ROOT / "data" / "research" / "pilot-source-manifest.json")
    hashes = {
        row["source_id"]: row["drive"]["raw_sha256"] for row in manifest["sources"]
    }
    config = {
        "run_id": "run:pilot-review-test-v1",
        "protocol_version": "protocol-v1",
        "taxonomy_version": "taxonomy-v1",
        "isolation_attestation": "Synthetic source-isolated report validation fixture.",
        "luna_gate": {
            "min_precision": 0.9,
            "min_recall": 0.8,
            "max_unresolved_rate": 0.1,
            "locked": True,
        },
        "assignments": [
            {
                "shard_id": "shard:pilot-review-test-ikeda",
                "source_id": IKEDA_SOURCE_ID,
                "source_sha256": hashes[IKEDA_SOURCE_ID],
                "worker_id": "terra-ikeda-test",
            },
            {
                "shard_id": "shard:pilot-review-test-fge",
                "source_id": FGE_SOURCE_ID,
                "source_sha256": hashes[FGE_SOURCE_ID],
                "worker_id": "terra-fge-test",
            },
        ],
    }
    shards = [
        _make_shard(config, config["assignments"][0], candidate_count=6, accepted_count=5),
        _make_shard(config, config["assignments"][1], candidate_count=8, accepted_count=7),
    ]
    return config, shards, _make_gold(config), manifest


class PilotCandidateReviewReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config, self.shards, self.gold, self.manifest = _fixture()

    def build(self) -> dict[str, Any]:
        return build_pilot_candidate_review_report(
            self.config,
            self.shards,
            self.gold,
            self.manifest,
            generated_at="2026-07-20",
        )

    def test_report_reproduces_expected_private_gate_counts(self) -> None:
        report = self.build()
        self.assertEqual(
            report["counts"],
            {
                "sources": 2,
                "candidates_proposed": 14,
                "mechanically_located": 14,
                "accepted_private_review": 12,
                "held_for_entity_review": 2,
                "rejected": 0,
                "draft_gold_cases": 15,
                "human_gold_cases": 0,
                "luna_gate_runs": 0,
                "published_evidence_claims": 0,
                "published_relations": 0,
            },
        )
        status_by_source = {
            row["source_id"]: row["public_release_status"]
            for row in report["sources"]
        }
        self.assertEqual(
            status_by_source[IKEDA_SOURCE_ID],
            "blocked_publisher_byte_reconciliation",
        )
        self.assertEqual(status_by_source[FGE_SOURCE_ID], "blocked_rights_review")

    def test_public_report_contains_no_private_payload_fields_or_values(self) -> None:
        report_text = json.dumps(self.build(), ensure_ascii=False, sort_keys=True)
        for forbidden_key in (
            "quote",
            "source_entity_id",
            "target_entity_id",
            "relation_id",
            "evidence_id",
            "canonical_url",
            "file_locator_sha256",
        ):
            self.assertNotIn(f'"{forbidden_key}"', report_text)
        for forbidden_value in (
            "Private Person One",
            "Private Institute One",
            "Private source excerpt",
            "person:synthetic_person",
            "institute:synthetic_institute",
            "rel:ikeda_0",
        ):
            self.assertNotIn(forbidden_value, report_text)
        locator = self.manifest["sources"][0]["drive"]["file_locator_sha256"]
        self.assertNotIn(locator, report_text)

    def test_source_hash_must_match_manifest(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        source = next(row for row in manifest["sources"] if row["source_id"] == IKEDA_SOURCE_ID)
        source["drive"]["raw_sha256"] = "0" * 64
        with self.assertRaises(ContractError):
            build_pilot_candidate_review_report(
                self.config,
                self.shards,
                self.gold,
                manifest,
                generated_at="2026-07-20",
            )

    def test_source_level_split_leakage_is_rejected(self) -> None:
        gold = copy.deepcopy(self.gold)
        gold[1]["split"] = "validation"
        with self.assertRaises(ContractError):
            build_pilot_candidate_review_report(
                self.config,
                self.shards,
                gold,
                self.manifest,
                generated_at="2026-07-20",
            )

    def test_non_draft_or_human_gold_is_rejected(self) -> None:
        gold = copy.deepcopy(self.gold)
        gold[0]["note"] = "Human-reviewed."
        gold[0]["annotators"] = ["human:reviewer"]
        with self.assertRaises(ContractError):
            build_pilot_candidate_review_report(
                self.config,
                self.shards,
                gold,
                self.manifest,
                generated_at="2026-07-20",
            )

    def test_manual_or_luna_candidate_is_rejected(self) -> None:
        shards = copy.deepcopy(self.shards)
        verification = shards[0]["evidence"][0]["verification"]
        verification.update(
            {
                "status": "manual",
                "method": "manual",
                "normalization_profile_version": None,
                "page_number": 1,
                "char_start": None,
                "char_end": None,
                "match_count": 1,
                "matched_text_sha256": None,
                "verifier": "human-test",
                "reason": "Synthetic manual exception.",
            }
        )
        with self.assertRaises(ContractError):
            build_pilot_candidate_review_report(
                self.config,
                shards,
                self.gold,
                self.manifest,
                generated_at="2026-07-20",
            )

        shards = copy.deepcopy(self.shards)
        shards[0]["relations"][0]["extractor"]["model"] = "luna"
        with self.assertRaises(ContractError):
            build_pilot_candidate_review_report(
                self.config,
                shards,
                self.gold,
                self.manifest,
                generated_at="2026-07-20",
            )

    def test_report_count_tampering_is_rejected(self) -> None:
        report = self.build()
        report["counts"]["accepted_private_review"] = 11
        with self.assertRaises(ContractError):
            validate_pilot_candidate_review_report(
                report, self.config, self.shards, self.gold, self.manifest
            )


if __name__ == "__main__":
    unittest.main()
