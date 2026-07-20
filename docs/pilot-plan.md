# Controlled historical pilot

The participant-provided Google Drive corpus is authorized for private research
analysis. That authorization does not grant public redistribution rights. The
public atlas may show source metadata, extraction counts, and hashes now;
quotations and historical relations remain at zero until rights review and
verification pass.

## Acquired pilot

The ten selected PDFs were resolved to exact Drive files and freshly hashed on
2026-07-20. The public manifest hashes private Drive locators instead of
exposing account emails or raw file IDs. The immutable records are in
`data/research/pilot-source-manifest.json`.

1. `source:v2_inonu_bilime_adanmis_bir_omur_pdf`
2. `source:v2_inonu_barut_100_pdf`
3. `source:v2_ikeda_koc_life_devoted_2003_pdf`
4. `source:v2_ikeda_matematik_dunyasi_2003_pdf`
5. `source:v2_inonu_invited_speakers_pdf`
6. `source:v2_fge_history_people_pdf`
7. `source:v2_fge_history_seminars_pdf`
8. `source:v2_fge_history_schools_semesters_pdf`
9. `source:v2_fge_yayin_listesi_pdf`
10. `source:v2_fge_research_staff_pdf`

The old candidate name `source:v2_ikeda_alp_eden_life_devoted_pdf` was corrected
after reading the PDF metadata: the document is Cemal Koç's 2003 article. The old
ID remains only as a provenance alias in the manifest.

## Completed controls

- The old registry expects 83 raw files; 82 are present in Drive. The only
  missing file is `Erdal İnönü Moseley Çanakkale mehmet emin.ppt`.
- Drive filename substitutions such as `|` to `_` were normalized during the
  reconciliation and were not counted as missing content.
- Old extracted JSONL, prior GPT results, AI scans, and the prior Person–FGE
  relation report are excluded from evidence.
- All ten selected PDFs have a fresh raw-byte SHA-256 and verified byte size.
- All ten PDFs were freshly extracted into 162 physical-page records; all 162
  records contain text and each text artifact has its own SHA-256.
- Representative page 1 of every PDF was rendered and visually reviewed. The
  two low-text warnings in the Koç article were also reviewed: pages 2 and 14
  are intentional duplicate portrait pages and their visible caption is present
  in the extracted text. No source currently requires OCR.
- FGE remains distinct from FGRC in the entity registry and pilot scope.
- Private analysis authorization is recorded separately from publication rights.

## Remaining controls

- Verify publisher identity and public quotation rights for nine sources. The
  Koç journal article has a recorded CC BY 4.0 licence reference.
- Create and human-review source-level gold labels before model evaluation.
- Add a Dilhan Eryurt raw-source batch after this FGE-heavy pilot; this ten-file
  selection currently covers three of the four Suns.
- Use Terra for initial candidate extraction and independent Sol review.
- Freeze gold labels and Luna thresholds before any scale extraction.

The text-free public review record is
`data/research/pilot-extraction-report.json`. Raw PDFs and extracted page text
remain in ignored private directories and are not published.

## Gold design

Label positive, negative, and ambiguous cases. Assign the split at source level.
Use at least two annotators for ambiguous or acceptance-critical cases, record
adjudication, and keep labels hidden from extraction workers.

The real Luna gate remains precision ≥ 0.90, recall ≥ 0.80, and unresolved rate
≤ 0.10. A failed gate routes the affected source class to Terra; it does not
lower the threshold.
