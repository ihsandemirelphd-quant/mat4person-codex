from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pipeline.contracts import load_json, validate_bundle


def _rows(bundle: Path, plural: str, singular: str | None = None) -> list[dict[str, Any]]:
    path = bundle / plural
    if path.exists():
        payload = load_json(path)
        return payload if isinstance(payload, list) else [payload]
    if singular is not None and (bundle / singular).exists():
        return [load_json(bundle / singular)]
    return []


def validate_directory(bundle: Path) -> None:
    validate_bundle(
        sources=_rows(bundle, "sources.json", "source.json"),
        entities=_rows(bundle, "entities.json", "entity.json"),
        source_texts=_rows(bundle, "source-texts.json", "source-text.json"),
        evidence=_rows(bundle, "evidence.json"),
        relations=_rows(bundle, "relations.json", "relation.json"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a MAT4Person contract bundle")
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    validate_directory(args.bundle)
    print(f"Valid contract bundle: {args.bundle}")


if __name__ == "__main__":
    main()
