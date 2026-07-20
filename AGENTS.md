# MAT4Person Codex working agreement

## Purpose

This repository is a clean-room reproduction of the MAT4Person 4 Suns and
Feza Gürsey experiment. The old `math_fidani` and
`mat4person-knowledge-graph` repositories are comparison baselines only.

## Non-negotiable rules

- Do not copy old implementation code, prompts, relation outputs, generated
  graph data, or website code into this repository.
- Do not inspect old relation outputs until a clean run has been validated,
  frozen, and committed.
- Treat primary documents as evidence. AI-authored scans or summaries are
  comparison material, never primary evidence.
- Never accept a relation without at least one evidence record containing a
  non-empty quotation and a stable source identifier.
- Report a page only when the source supports one. Use `not_paginated` or
  `unknown` explicitly instead of inventing a page.
- Keep copyrighted raw documents outside Git. Commit manifests, hashes,
  lawful source URLs, short evidence excerpts, and derived structured data.
- Workers write isolated per-source shards. Only the primary agent merges
  shared graph and report files.

## Model routing

- GPT-5.6 Sol owns architecture, schema changes, ambiguous decisions, final
  evidence verification, merges, release review, and publication.
- GPT-5.6 Terra handles document work that requires judgment or tool use.
- GPT-5.6 Luna handles clear, repeatable, high-volume extraction only after it
  passes the gold evaluation set.
- Run at most three parallel workers. Prefer batches over one agent per edge.

## Repository layout

- `pipeline/`: deterministic ingestion, validation, merge, and reporting code.
- `schemas/`: public JSON contracts for sources, evidence, and relations.
- `data/`: public manifests, seed entities, and gold evaluation data.
- `runs/`: generated run artifacts; raw or intermediate runs stay ignored.
- `app/`: the Sites application.
- `plugins/mat4person-evidence-atlas/`: the installable Codex plugin.
- `docs/`: protocol, decisions, model routing, and run reports.

## Verification

Before declaring a phase complete:

1. Run the contract tests.
2. Run the website build.
3. Validate the plugin manifest.
4. Review the diff for old-run leakage, unsupported claims, and accidental raw
   source inclusion.

Phase 0 is complete only when the clean repository, contracts, tests, Sites
starter, plugin manifest, and experimental protocol all validate without
processing the real corpus.
