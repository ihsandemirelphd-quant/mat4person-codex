from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()


def find_all(text: str, quote: str) -> list[int]:
    found: list[int] = []
    start = 0
    while quote and (position := text.find(quote, start)) >= 0:
        found.append(position)
        start = position + len(quote)
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a quotation against UTF-8 source text")
    parser.add_argument("source", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--quote")
    group.add_argument("--quote-file", type=Path)
    args = parser.parse_args()
    text = args.source.read_text(encoding="utf-8")
    quote = args.quote if args.quote is not None else args.quote_file.read_text(encoding="utf-8")
    exact = find_all(text, quote)
    if exact:
        result = {
            "status": "exact_match", "method": "exact-v1", "match_count": len(exact),
            "char_start": exact[0], "char_end": exact[0] + len(quote),
            "quote_sha256": digest(quote), "matched_text_sha256": digest(quote)
        }
    else:
        normalized_quote = normalize(quote)
        normalized = find_all(normalize(text), normalized_quote)
        result = {
            "status": "normalized_match" if normalized else "unverified",
            "method": "nfkc-whitespace-v1" if normalized else "none",
            "match_count": len(normalized), "char_start": None, "char_end": None,
            "quote_sha256": digest(quote),
            "matched_text_sha256": digest(normalized_quote) if normalized else None
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] == "unverified":
        sys.exit(1)


if __name__ == "__main__":
    main()
