from __future__ import annotations

from typing import Any

from pipeline.contracts import ContractError, validate_payload


EXPECTED_SOURCE_IDS = {
    "source:v2_inonu_bilime_adanmis_bir_omur_pdf",
    "source:v2_inonu_barut_100_pdf",
    "source:v2_ikeda_koc_life_devoted_2003_pdf",
    "source:v2_ikeda_matematik_dunyasi_2003_pdf",
    "source:v2_inonu_invited_speakers_pdf",
    "source:v2_fge_history_people_pdf",
    "source:v2_fge_history_seminars_pdf",
    "source:v2_fge_history_schools_semesters_pdf",
    "source:v2_fge_yayin_listesi_pdf",
    "source:v2_fge_research_staff_pdf",
}

EXCLUDED_TITLE_MARKERS = {
    "gpt results",
    "with sources",
    "without sources",
    "person-fge relations",
    "gpt scan",
}


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ContractError(f"Pilot manifest contains a duplicate {label}")


def validate_pilot_source_manifest(
    manifest: dict[str, Any],
    entities: list[dict[str, Any]],
    sun_ids: list[str],
) -> dict[str, int]:
    """Validate the authorized, claim-free ten-document Drive pilot."""

    validate_payload("pilot-source-manifest", manifest)

    if manifest["corpus"]["owner_role"] != "participant_corpus_owner":
        raise ContractError("Pilot corpus owner role does not match the authorized source folder")
    if manifest["corpus"]["authorized_role"] != "codex_research_account":
        raise ContractError("Pilot corpus is not bound to the authorized research role")
    if manifest["baseline_reconciliation"]["missing_files"] != [
        "Erdal İnönü Moseley Çanakkale mehmet emin.ppt"
    ]:
        raise ContractError("Baseline reconciliation does not identify the verified missing file")

    if len(sun_ids) != 4 or len(set(sun_ids)) != 4:
        raise ContractError("Presentation must configure exactly four unique Sun IDs")

    entity_by_id = {row["entity_id"]: row for row in entities}
    if len(entity_by_id) != len(entities):
        raise ContractError("Registry contains duplicate entity IDs")

    sources = manifest["sources"]
    source_ids = [row["source_id"] for row in sources]
    file_locators = [row["drive"]["file_locator_sha256"] for row in sources]
    hashes = [row["drive"]["raw_sha256"] for row in sources]
    _unique(source_ids, "source ID")
    _unique(file_locators, "Drive file locator")
    _unique(hashes, "raw SHA-256")

    if set(source_ids) != EXPECTED_SOURCE_IDS:
        missing = sorted(EXPECTED_SOURCE_IDS - set(source_ids))
        extra = sorted(set(source_ids) - EXPECTED_SOURCE_IDS)
        raise ContractError(f"Pilot source set drifted; missing={missing}, extra={extra}")

    scope_ids: set[str] = set()
    for source in sources:
        folded_title = source["title"].casefold()
        blocked = sorted(
            marker for marker in EXCLUDED_TITLE_MARKERS if marker in folded_title
        )
        if blocked:
            raise ContractError(
                f"Pilot source {source['source_id']} matches excluded AI-output markers: {blocked}"
            )

        for entity_id in source["scope_entity_ids"]:
            if entity_id not in entity_by_id:
                raise ContractError(
                    f"Pilot source {source['source_id']} references unknown scope entity {entity_id}"
                )
            scope_ids.add(entity_id)

    return {
        "sources": len(sources),
        "bytes": sum(row["drive"]["size_bytes"] for row in sources),
        "sun_coverage": len(set(sun_ids) & scope_ids),
        "scope_entities": len(scope_ids),
        "license_verified": sum(
            row["publication_status"] == "license_verified_extraction_pending"
            for row in sources
        ),
        "rights_review_required": sum(
            row["publication_status"] == "rights_review_required" for row in sources
        ),
        "extraction_pending": sum(
            row["extraction_status"] == "pending_page_preserving_extraction"
            for row in sources
        ),
        "evidence_claims": sum(row["evidence_claims"] for row in sources),
        "relationship_claims": sum(row["relationship_claims"] for row in sources),
    }
