# Drive corpus acquisition ledger

Checked on 2026-07-20 through the authorized research account. The `math4people`
folder is participant-owned, and the research account has writer access. The
public manifest hashes private Drive locators instead of exposing account emails
or raw file IDs.

## Baseline reconciliation

- Legacy registry: **83** expected raw files.
- Drive baseline: **82** raw files present.
- Missing: `Erdal İnönü Moseley Çanakkale mehmet emin.ppt`.
- Apparent punctuation mismatches are Drive filename normalization, not missing
  documents.

The missing PowerPoint was searched across the accessible Drive and was not
found. It does not block the selected ten-document pilot.

## Ten-document pilot

All ten selected PDFs were read as raw bytes through the authorized Drive
connection. Together they contain **18,475,323 bytes**. Each now has a stable
source ID, hashed Drive locator, modified time, byte size, and fresh SHA-256 in
`data/research/pilot-source-manifest.json`.

- **10/10** acquired and hash-verified for private research.
- **10/10** awaiting fresh page-preserving extraction.
- **1/10** has a recorded CC BY 4.0 licence reference.
- **9/10** require source-specific public quotation review.
- **0** historical evidence claims and **0** historical relations published.

## Excluded comparison material

Old JSONL text extractions, GPT result folders and ZIPs, “WITH sources” and
“WITHOUT sources” scans, and `Person-FGE relations.pdf` are comparison material
only. They are not evidence inputs.

## Next controlled operation

Freshly extract physical pages from all ten PDFs, record text-artifact hashes,
and route OCR or ambiguous layouts to Terra. No quotation becomes public until
code locates it in the bound page text and an independent Sol reviewer accepts
the candidate.
