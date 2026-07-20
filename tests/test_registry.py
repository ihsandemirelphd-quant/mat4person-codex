from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

from pipeline.contracts import load_json, validate_payload
from pipeline.io import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(ROOT / "data" / "registry" / "entities.json")
        cls.provenance = load_json(ROOT / "data" / "registry" / "provenance.json")
        cls.presentation = load_json(ROOT / "data" / "registry" / "presentation.json")
        cls.approved_aliases = load_json(ROOT / "data" / "registry" / "approved-aliases.json")
        cls.report = load_json(ROOT / "data" / "registry" / "migration-report.json")

    def test_registry_is_unique_and_contract_valid(self) -> None:
        identifiers = [item["entity_id"] for item in self.registry]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for entity in self.registry:
            validate_payload("entity", entity)
        for item in self.provenance:
            validate_payload("registry-provenance", item)
        validate_payload("migration-report", self.report)

    def test_reconciled_counts_are_frozen(self) -> None:
        self.assertEqual(len(self.registry), 321)
        self.assertEqual(
            Counter(item["kind"] for item in self.registry),
            {"person": 267, "event": 23, "institute": 31},
        )
        sun_ids = set(self.presentation["sun_ids"])
        nebula_ids = set(self.presentation["nebula_ids"])
        roles = Counter()
        for entity in self.registry:
            if entity["entity_id"] in sun_ids:
                roles["sun"] += 1
            elif entity["entity_id"] in nebula_ids:
                roles["nebula"] += 1
            else:
                roles[self.presentation["default_roles"][entity["kind"]]] += 1
        self.assertEqual(
            roles,
            {"sun": 4, "planet": 263, "event": 23, "institution": 29, "nebula": 2},
        )

    def test_registry_contains_no_historical_relations(self) -> None:
        self.assertEqual(self.report["counts"]["historical_relations"], 0)
        self.assertTrue(all(item["verification_status"] == "unverified_seed" for item in self.provenance))
        self.assertTrue(all(item["relationship_claims"] == 0 for item in self.provenance))
        self.assertTrue(
            all("relation" not in key for item in self.registry for key in item)
        )

    def test_registry_and_provenance_ids_align(self) -> None:
        entity_ids = [item["entity_id"] for item in self.registry]
        provenance_ids = [item["entity_id"] for item in self.provenance]
        self.assertEqual(len(provenance_ids), len(set(provenance_ids)))
        self.assertEqual(set(entity_ids), set(provenance_ids))
        self.assertEqual(
            sum(item["adjudication_status"] == "needs_atomic_split_review" for item in self.provenance),
            7,
        )

    def test_import_allowlist_excludes_legacy_enrichment(self) -> None:
        allowed = {"entity_id", "kind", "canonical_name", "aliases", "registry_version", "note"}
        banned = {
            "roles", "discipline_group", "institutions", "date", "city", "country",
            "founders", "contributors", "evidence", "confidence", "relations",
        }
        for entity in self.registry:
            self.assertEqual(set(entity), allowed)
            self.assertTrue(set(entity).isdisjoint(banned))
            self.assertEqual(
                entity["aliases"],
                sorted(self.approved_aliases.get(entity["entity_id"], []), key=str.casefold),
            )

    def test_reconciliation_keeps_canonical_ikeda_and_separate_fg_nodes(self) -> None:
        by_id = {item["entity_id"]: item for item in self.registry}
        presentation = self.presentation
        ikeda = by_id["person:masatoshi_gunduz_ikeda"]
        self.assertIn("Gündüz İkeda", ikeda["aliases"])
        provenance = {item["entity_id"]: item for item in self.provenance}
        self.assertIn("person:gunduz_ikeda", provenance[ikeda["entity_id"]]["legacy_id_aliases"])
        self.assertIn(ikeda["entity_id"], presentation["sun_ids"])
        self.assertIn("institute:feza_gursey_enstitusu", by_id)
        self.assertIn("institute:feza_gursey_research_center", by_id)
        self.assertIn("institute:feza_gursey_enstitusu", presentation["nebula_ids"])
        self.assertIn("institute:feza_gursey_research_center", presentation["nebula_ids"])

    def test_registry_digest_matches_report(self) -> None:
        self.assertEqual(
            canonical_sha256(self.registry), self.report["registry_sha256"]
        )
        self.assertEqual(
            canonical_sha256(self.provenance), self.report["provenance_manifest_sha256"]
        )
        self.assertEqual(
            self.report["legacy_ref_commit"],
            "e2abd60b8df5a974a53720f873b3d270856e101b",
        )
        self.assertEqual(self.report["reconciliation"]["prior_claude_derived_records"], 16)


if __name__ == "__main__":
    unittest.main()
