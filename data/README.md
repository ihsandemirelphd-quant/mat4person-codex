# Public data area

Phase 0 contains no real historical corpus and no historical relation claims.
The files under `data/demo/` are synthetic fixtures. `data/research/` contains
metadata-only source leads; it contains no downloaded source text or evidence.
Later phases will add:

- `source_manifest.jsonl` with stable IDs, hashes, citations, access metadata,
  and processing status;
- `entities.json` with the approved seed entities;
- `gold_eval.jsonl` with human-reviewed positive, negative, and ambiguous cases;
  and
- sanitized, verified graph artifacts suitable for the public Sites build.

Raw copyrighted documents belong in `data/raw/`, which is ignored by Git.

`data/seed/entities.json` contains candidate entities only; inclusion does not
assert a relationship. `data/demo/` is fully synthetic and may be committed.

`data/research/pilot-source-manifest.json` records the ten participant-authorized
Drive PDFs selected for the first historical pilot. It contains raw-byte hashes
and acquisition metadata, but no PDF bytes, extracted text, quotations, or
historical claims. Private analysis authorization is intentionally separate
from public quotation and redistribution rights.

`data/registry/entities.json` is the clean-room identity registry reconstructed
from the user-provided people, event, and institute lists in the earlier
MAT4Person repository. `data/registry/migration-report.json` freezes input
hashes, reconciliation rules, counts, and the output digest. Registry presence
is not a historical relationship claim.

`approved-aliases.json` is the explicit clean-run alias allowlist.
`presentation.json` assigns the user-approved Sun, planet, nebula, institution,
and event shapes independently of the legacy data. Seven composite labels are
flagged in `provenance.json` for atomic split review.

Rebuild it when both repositories are available:

```text
python -m pipeline.registry ../math_fidani data/registry/entities.json data/registry/provenance.json data/registry/migration-report.json --legacy-ref e2abd60b8df5a974a53720f873b3d270856e101b
```
