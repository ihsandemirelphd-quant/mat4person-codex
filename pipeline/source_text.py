from __future__ import annotations

from typing import Any

from pipeline.io import canonical_sha256


INGEST_VERSION = "text-v1"
OFFSET_UNIT = "unicode_code_point_half_open"


def artifact_digest(payload: dict[str, Any]) -> str:
    material = {
        "source_id": payload["source_id"],
        "source_sha256": payload["source_sha256"],
        "ingest_version": payload["ingest_version"],
        "offset_unit": payload["offset_unit"],
        "pages": payload["pages"],
    }
    return canonical_sha256(material)
