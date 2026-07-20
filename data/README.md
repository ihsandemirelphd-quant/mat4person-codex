# Public data area

Phase 0 intentionally contains no real corpus and no historical relation
claims. Later phases will add:

- `source_manifest.jsonl` with stable IDs, hashes, citations, access metadata,
  and processing status;
- `entities.json` with the approved seed entities;
- `gold_eval.jsonl` with human-reviewed positive, negative, and ambiguous cases;
  and
- sanitized, verified graph artifacts suitable for the public Sites build.

Raw copyrighted documents belong in `data/raw/`, which is ignored by Git.

`data/seed/entities.json` contains candidate entities only; inclusion does not
assert a relationship. `data/demo/` is fully synthetic and may be committed.
