# Evidence atlas contracts

## Core records

- `source`: stable ID, title, access classification, raw SHA-256, language, page count, content kind, ingest version, rights note.
- `source-text`: source ID/hash, artifact hash, normalization/offset version, contiguous physical pages, per-page text hashes.
- `entity`: stable typed ID, canonical name, aliases, registry version.
- `evidence`: source and text-artifact hashes, short quotation and quotation hash, explicit page status, mechanical/manual verification record.
- `relation`: typed endpoints, direction, confidence, evidence IDs, status, extractor execution, independent verifier execution and verdict.
- `run`: protocol/taxonomy versions, isolation attestation, locked model gate, complete source-to-worker assignments.
- `shard`: run/config/source/worker bindings plus one source payload and its candidate records.

## Frozen relation taxonomy

Person-to-person types:

- `guidance`
- `student_teacher`
- `grad_student`
- `academic_environment`
- `academic_output`
- `in_same_context`

FGE/FGRC-related types:

- `person_institute_presence`
- `person_event_presence`
- `fg_activity`
- `fg_talk`
- `fg_paper`
- `fg_member`

Use an `fg_member` subtype only for `fg_member`: `research_staff`, `postdoc`, `board`, `director`, `staff`, `group_photo`, or `award`.

Treat `academic_environment`, `academic_output`, and `in_same_context` as undirected. Canonicalize their endpoint order before comparison. For directed person-to-person types, use mentor/teacher/advisor as the source and mentee/student/graduate student as the target. Treat the remaining frozen types as directed from the person toward the institute, event, or FG context.

## Verification record

Use Unicode code-point half-open offsets `[char_start, char_end)`. Record the mechanical method (`exact-v1` or `nfkc-whitespace-v1`), match count, physical text segment, matched-text hash, and verifier. A normalized match may omit raw character offsets because normalization changes positions. A manual record must name the human verifier and explain the reason. Use `page_status: not_paginated` with null page bounds for plain text or HTML that has no source pagination, even though its extracted text artifact has a physical segment number.

Do not accept caller-asserted strings such as `exact_match` without reproducing the match from the bound source-text artifact.
