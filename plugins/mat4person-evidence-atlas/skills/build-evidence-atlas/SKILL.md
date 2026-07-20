---
name: build-evidence-atlas
description: Build, audit, or repair source-grounded relationship graphs from documents. Use for evidence extraction, provenance checking, quotation verification, entity/relation normalization, independent review, worker-shard merging, gold-set evaluation, or preparing a publishable evidence atlas from text, OCR, HTML, or document-derived source text.
---

# Build Evidence Atlas

Create a relationship atlas in which every accepted edge remains traceable to a stable source revision and a located quotation. Keep model judgment separate from deterministic validation.

## Workflow

1. Inventory source files without treating previous AI summaries or graph outputs as evidence.
2. Read [contracts.md](references/contracts.md) before creating entities, evidence, or relations.
3. Create an immutable source revision: record the content hash, rights note, access URI when lawful, and page-text artifact.
4. Extract candidates into one shard per assigned source. Never let workers edit a shared graph.
5. Locate every quotation mechanically. In the MAT4Person repository, use `python -m pipeline.verification`; outside it, use `scripts/verify_quote.py` for a standalone exact/normalized check.
6. Reject unresolved entities, stale hashes, missing quotations, invented pages, and relation types outside the frozen taxonomy.
7. Send surviving candidates to a reviewer whose `worker_id` differs from the extractor. Require an explicit `accept`, `reject`, or `review` verdict.
8. Merge READY shards only after the complete assignment set validates. Fail closed on missing, foreign, stale, or divergent shards.
9. Evaluate model output against human labels split by source. Do not use Luna for bulk extraction until the locked precision, recall, and unresolved-rate gate passes.
10. Freeze hashes, model/prompt identifiers, metrics, code revision, and isolation attestation before comparing with any earlier run.

## Model routing

Read [model-routing.md](references/model-routing.md) when coordinating more than one model.

- Use Sol for schema changes, ambiguous judgments, independent verification, merges, and release review.
- Use Terra for document interpretation or tool-heavy extraction.
- Use Luna only for stable repetitive extraction after the gold gate passes.
- Use code for hashing, normalization, quotation location, schema checks, merging, metrics, and freeze manifests.

## Acceptance boundary

Label an edge `accepted` only when all of these are true:

- Both endpoints resolve to the entity registry.
- Evidence binds the exact source and text-artifact hashes.
- The quotation is non-empty and mechanically located, or a human manual-review record explains the exception.
- Page status is explicit; never invent pagination.
- The verifier differs from the extraction worker and records `verdict: accept`.
- The complete bundle passes deterministic validation.

If any condition fails, use `candidate`, `review`, or `rejected`; never silently repair evidence with model-authored text.

## Publication

Publish short excerpts and lawful source metadata only. Keep copyrighted raw documents out of the repository. Clearly distinguish synthetic demonstrations, fresh research results, and comparison baselines.
