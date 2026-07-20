from __future__ import annotations

import argparse
import csv
import io
import subprocess
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from pipeline.contracts import validate_payload
from pipeline.io import atomic_write_json, canonical_sha256, load_json, sha256_bytes, sha256_file


REGISTRY_VERSION = "legacy-node-registry-v1"
IMPORT_DATE = "2026-07-20"
NORMALIZATION_VERSION = "registry-import-v1"
REGISTRY_NOTE = "Unverified candidate identity only; inclusion asserts no relationship."
BASELINE_COMMIT = "54496c9bfb6051e3ce4bb8f2109776313f3a9883"
V2_COMMIT = "349e34f11abf4e3ef1de1a3919a8b549c1c24837"
EXPECTED_LEGACY_COMMIT = "e2abd60b8df5a974a53720f873b3d270856e101b"
RIGHTS_BASIS = "participant attestation recorded in docs/seed-rights-attestation.md"
LEGACY_FILES = {
    "fundamental": Path("data/input/fundamental_persons.csv"),
    "base": Path("data/input/base_persons.csv"),
    "events": Path("data/input/events.csv"),
    "institutes": Path("data/input/institutes.csv"),
}
V2_ADDED_IDS = {
    "person:ali_kaya",
    "person:levent_akant",
    "person:alkan_kabakcioglu",
    "person:huseyin_kocak",
    "person:atac_imamoglu",
    "person:hagi_ahmedov",
    "person:ersan_demiralp",
    "person:huseyin_kaya",
    "person:muhittin_mungan",
    "person:meral_tosun",
    "person:dieter_van_den_bleeken",
    "person:ali_suleyman_ustunel",
    "person:murat_gunaydin",
    "event:2026_inonu_barut_100_anma",
    "event:erdal_inonu_bilime_adanmis_bir_omur_anma",
    "institute:feza_gursey_research_center",
}
COMPOSITE_IDS = {
    "institute:silivri_matematik_enstitusu_and_silivri",
    "institute:tubitak_mam_and_gebze",
    "institute:ictp_and_trieste",
    "institute:bilim_ve_teknik_and_bilim_cocuk",
    "event:1946_universiteler_kanunu_and_ankara_universitesi_kurulus",
    "event:1991_1993_uluslararasi_matematiksel_fizik_konferanslari",
    "event:nato_yaz_okullari_1967_1970_1972_1981_1983_1984_1989_1994",
}


def _git(legacy_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(legacy_root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _rows(content: bytes) -> list[tuple[int, dict[str, str]]]:
    text = content.decode("utf-8-sig")
    return [
        (index, row)
        for index, row in enumerate(csv.DictReader(io.StringIO(text)), start=2)
    ]


def _identity_key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


def _dedupe(values: list[str], *, omit: str | None = None) -> list[str]:
    omitted = _identity_key(omit) if omit else None
    selected: dict[str, str] = {}
    for value in values:
        cleaned = " ".join(unicodedata.normalize("NFC", value).split())
        key = _identity_key(cleaned)
        if cleaned and key != omitted and key not in selected:
            selected[key] = cleaned
    return sorted(selected.values(), key=str.casefold)


def _row_id(source_name: str, row: dict[str, str]) -> str:
    if source_name == "base":
        return row.get("canonical_node_id") or row["node_id"]
    return row["node_id"]


@lru_cache(maxsize=None)
def _version_blob(legacy_root: Path, commit: str, source_name: str) -> bytes:
    relative = LEGACY_FILES[source_name]
    return _git(legacy_root, "show", f"{commit}:{relative.as_posix()}")


def _source_version(
    legacy_root: Path, source_name: str, entity_id: str
) -> tuple[str, str, bytes, int]:
    commit = V2_COMMIT if entity_id in V2_ADDED_IDS else BASELINE_COMMIT
    author_status = (
        "prior_claude_derived_from_participant_roadmap"
        if commit == V2_COMMIT
        else "participant_supplied_baseline"
    )
    relative = LEGACY_FILES[source_name]
    content = _version_blob(legacy_root, commit, source_name)
    matches = [number for number, row in _rows(content) if _row_id(source_name, row) == entity_id]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one provenance row for {entity_id} in {commit}:{relative}; got {matches}"
        )
    return commit, author_status, content, matches[0]


def _source_record(
    *,
    legacy_root: Path,
    entity_id: str,
    source_name: str,
    imported_fields: list[str],
) -> dict[str, Any]:
    commit, author_status, content, row_number = _source_version(
        legacy_root, source_name, entity_id
    )
    return {
        "baseline_artifact": f"{commit}:{LEGACY_FILES[source_name].as_posix()}",
        "baseline_sha256": sha256_bytes(content),
        "legacy_commit": commit,
        "original_author_status": author_status,
        "source_row": row_number,
        "imported_fields": imported_fields,
    }


def _entity(entity_id: str, kind: str, name: str, aliases: list[str]) -> dict[str, Any]:
    canonical_name = " ".join(unicodedata.normalize("NFC", name).split())
    return {
        "entity_id": entity_id,
        "kind": kind,
        "canonical_name": canonical_name,
        "aliases": _dedupe(aliases, omit=canonical_name),
        "registry_version": REGISTRY_VERSION,
        "note": REGISTRY_NOTE,
    }


def _manifest_record(
    *,
    legacy_root: Path,
    entity_id: str,
    source_name: str,
    alias_path: Path,
    alias_hash: str,
) -> dict[str, Any]:
    legacy_id_aliases: list[str] = []
    if entity_id == "person:masatoshi_gunduz_ikeda":
        legacy_id_aliases.append("person:gunduz_ikeda")
    if entity_id == "institute:feza_gursey_enstitusu":
        legacy_id_aliases.append("institute:feza_gursey_institute")
    return {
        "entity_id": entity_id,
        "imported_fields": ["canonical_name", "aliases", "kind"],
        "sources": [
            _source_record(
                legacy_root=legacy_root,
                entity_id=entity_id,
                source_name=source_name,
                imported_fields=["canonical_name", "kind"],
            )
        ],
        "alias_allowlist": {
            "path": alias_path.as_posix(),
            "sha256": alias_hash,
        },
        "import_date": IMPORT_DATE,
        "normalization_version": NORMALIZATION_VERSION,
        "rights_basis": RIGHTS_BASIS,
        "verification_status": "unverified_seed",
        "relationship_claims": 0,
        "legacy_id_aliases": legacy_id_aliases,
        "adjudication_status": (
            "needs_atomic_split_review" if entity_id in COMPOSITE_IDS else "not_required"
        ),
    }


def build_registry(
    legacy_root: Path,
    legacy_ref: str = EXPECTED_LEGACY_COMMIT,
    approved_aliases_path: Path = Path("data/registry/approved-aliases.json"),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    resolved_commit = _git(legacy_root, "rev-parse", legacy_ref).decode("ascii").strip()
    if resolved_commit != EXPECTED_LEGACY_COMMIT:
        raise ValueError(
            f"Legacy registry must resolve to reviewed commit {EXPECTED_LEGACY_COMMIT}; "
            f"got {resolved_commit}"
        )

    source_blobs = {
        name: _git(legacy_root, "show", f"{resolved_commit}:{relative.as_posix()}")
        for name, relative in LEGACY_FILES.items()
    }
    v2_blobs = {
        name: _git(legacy_root, "show", f"{V2_COMMIT}:{relative.as_posix()}")
        for name, relative in LEGACY_FILES.items()
    }
    if source_blobs != v2_blobs:
        raise ValueError("Reviewed registry inputs diverge from the frozen V2 input commit")

    source_hashes = {name: sha256_bytes(content) for name, content in source_blobs.items()}
    input_rows = {name: _rows(content) for name, content in source_blobs.items()}
    approved_aliases = load_json(approved_aliases_path)
    alias_hash = sha256_file(approved_aliases_path)

    entities: dict[str, dict[str, Any]] = {}
    manifest: dict[str, dict[str, Any]] = {}

    for _, row in input_rows["base"]:
        entity_id = _row_id("base", row)
        if entity_id in entities:
            raise ValueError(f"Duplicate canonical person ID: {entity_id}")
        entities[entity_id] = _entity(
            entity_id, "person", row["display_name"], approved_aliases.get(entity_id, [])
        )
        manifest[entity_id] = _manifest_record(
            legacy_root=legacy_root,
            entity_id=entity_id,
            source_name="base",
            alias_path=approved_aliases_path,
            alias_hash=alias_hash,
        )

    fundamental_ids: set[str] = set()
    for _, row in input_rows["fundamental"]:
        entity_id = row["node_id"]
        if entity_id not in entities:
            raise ValueError(f"Fundamental person missing from base master: {entity_id}")
        fundamental_ids.add(entity_id)
        entity = entities[entity_id]
        base_name = entity["canonical_name"]
        fundamental_name = " ".join(unicodedata.normalize("NFC", row["display_name"]).split())
        if len(fundamental_name) > len(base_name):
            entity["canonical_name"] = fundamental_name
        entity["aliases"] = _dedupe(
            approved_aliases.get(entity_id, []), omit=entity["canonical_name"]
        )
        manifest[entity_id]["sources"].append(
            _source_record(
                legacy_root=legacy_root,
                entity_id=entity_id,
                source_name="fundamental",
                imported_fields=["canonical_name", "kind"],
            )
        )

    for source_name, kind in (("events", "event"), ("institutes", "institute")):
        for _, row in input_rows[source_name]:
            entity_id = row["node_id"]
            if entity_id in entities:
                raise ValueError(f"Duplicate global entity ID: {entity_id}")
            entities[entity_id] = _entity(
                entity_id, kind, row["display_name"], approved_aliases.get(entity_id, [])
            )
            manifest[entity_id] = _manifest_record(
                legacy_root=legacy_root,
                entity_id=entity_id,
                source_name=source_name,
                alias_path=approved_aliases_path,
                alias_hash=alias_hash,
            )

    unknown_alias_ids = set(approved_aliases) - set(entities)
    if unknown_alias_ids:
        raise ValueError(f"Alias allowlist references unknown IDs: {sorted(unknown_alias_ids)}")

    registry = sorted(entities.values(), key=lambda item: item["entity_id"])
    provenance = sorted(manifest.values(), key=lambda item: item["entity_id"])
    for item in registry:
        validate_payload("entity", item)
    for item in provenance:
        validate_payload("registry-provenance", item)

    kinds = Counter(item["kind"] for item in registry)
    report = {
        "registry_version": REGISTRY_VERSION,
        "generated_by": "pipeline.registry:v3",
        "legacy_ref": resolved_commit,
        "legacy_ref_commit": resolved_commit,
        "source_files": [
            {
                "path": f"{resolved_commit}:{LEGACY_FILES[name].as_posix()}",
                "sha256": source_hashes[name],
                "row_count": len(input_rows[name]),
            }
            for name in ("fundamental", "base", "events", "institutes")
        ],
        "alias_allowlist": {
            "path": approved_aliases_path.as_posix(),
            "sha256": alias_hash,
            "entity_count": len(approved_aliases),
        },
        "reconciliation": {
            "fundamental_people_joined": len(fundamental_ids),
            "legacy_id_mappings": {
                "person:gunduz_ikeda": "person:masatoshi_gunduz_ikeda",
                "institute:feza_gursey_institute": "institute:feza_gursey_enstitusu",
            },
            "prior_claude_derived_records": len(V2_ADDED_IDS),
            "composite_records_held_for_adjudication": len(COMPOSITE_IDS),
            "rules": [
                "The 267-person merged master is keyed by canonical_node_id.",
                "The four fundamental rows join the master; presentation roles are configured separately.",
                "Only canonical names, allowlisted aliases, and coarse entity kinds migrate.",
                "No legacy edge, evidence, role, discipline, affiliation, date, or biography migrates.",
            ],
        },
        "counts": {
            "total": len(registry),
            "by_kind": dict(sorted(kinds.items())),
            "historical_relations": 0,
        },
        "registry_sha256": canonical_sha256(registry),
        "provenance_manifest_sha256": canonical_sha256(provenance),
    }
    validate_payload("migration-report", report)
    return registry, provenance, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the clean-room MAT4Person node registry")
    parser.add_argument("legacy_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--legacy-ref", default=EXPECTED_LEGACY_COMMIT)
    parser.add_argument(
        "--approved-aliases",
        type=Path,
        default=Path("data/registry/approved-aliases.json"),
    )
    args = parser.parse_args()
    registry, manifest, report = build_registry(
        args.legacy_root, args.legacy_ref, args.approved_aliases
    )
    atomic_write_json(args.output, registry)
    atomic_write_json(args.manifest, manifest)
    atomic_write_json(args.report, report)


if __name__ == "__main__":
    main()
