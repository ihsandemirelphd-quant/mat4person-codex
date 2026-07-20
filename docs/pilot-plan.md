# Controlled historical pilot

The public synthetic demonstration does not authorize historical extraction.
Start the real pilot only after source access and quotation-publication rights
are confirmed.

## Target sources

The clean-room inventory identified these ten high-value source records from
the legacy manifest. Reconcile each entry with the underlying primary document,
compute a new SHA-256, record a canonical lawful URL where available, and add a
rights note before ingestion.

1. `source:v2_inonu_bilime_adanmis_bir_omur_pdf`
2. `source:v2_inonu_barut_100_pdf`
3. `source:v2_ikeda_alp_eden_life_devoted_pdf`
4. `source:v2_ikeda_matematik_dunyasi_2003_pdf`
5. `source:v2_inonu_invited_speakers_pdf`
6. `source:v2_fge_history_people_pdf`
7. `source:v2_fge_history_seminars_pdf`
8. `source:v2_fge_history_schools_semesters_pdf`
9. `source:v2_fge_yayin_listesi_pdf`
10. `source:v2_fge_research_staff_pdf`

## Preconditions

- Reconcile the 83 legacy manifest rows with 84 local raw files.
- Exclude AI-authored “WITH sources” and “WITHOUT sources” documents from the
  evidence set; use them only as search leads.
- Separate FGE from FGRC at entity resolution.
- Keep the İkeda genealogy layer out of the pilot.
- OCR image-only inputs and require human verification for OCR quotations.
- Freeze gold labels and Luna thresholds before model evaluation.

## Gold design

Label positive, negative, and ambiguous cases. Assign the split at source level.
Use at least two annotators for ambiguous or acceptance-critical cases, record
adjudication, and keep labels hidden from extraction workers.

The real Luna gate remains precision ≥ 0.90, recall ≥ 0.80, and unresolved rate
≤ 0.10. A failed gate routes the affected source class to Terra; it does not
lower the threshold.
