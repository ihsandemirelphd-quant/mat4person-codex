# Demo video script — target 2:40

## 0:00–0:20 — Problem

“Relationship graphs are easy to generate and hard to trust. MAT4Person is an
evidence-first Codex plugin: a model may propose an edge, but the product cannot
publish it until code locates the quotation and a separate reviewer accepts
it.”

Show the site hero and verification ledger.

## 0:20–0:55 — Product

Scroll to the interactive atlas. Select all three synthetic relations and point
out the source ID, text segment, exact character span, quote hash, Luna
extractor, and Sol verifier.

Say: “This demo is deliberately fictional. The interface reports zero
historical claims, so the product can be tested without laundering results from
the earlier Gemini or Claude experiments.”

## 0:55–1:35 — Working pipeline

Show the repository and run:

```text
python -m pipeline.demo
python -m unittest discover -s tests -p "test_*.py"
```

Say: “Ingestion hashes the source, quote verification reproduces the exact
span, workers write isolated shards, merge fails closed, and evaluation uses a
locked gate. The included sample runs locally without an API key.”

## 1:35–2:05 — Codex plugin and GPT-5.6

Show `plugins/mat4person-evidence-atlas/skills/build-evidence-atlas/SKILL.md`.

Say: “Sol owns contracts and independent review. Terra handles documents that
need interpretation or tools. Luna receives only stable repetitive extraction
after passing a human gold set. Deterministic code handles everything that
should not depend on model judgment.”

Mention that parallel Codex reviewers audited the submission rules, contracts,
source inventory, and finished skill.

## 2:05–2:30 — Design decision and correction

Say: “A blind forward-test caught a subtle issue: the first demo called an
unpaginated text file page one. We changed the contract so real page numbers and
physical text segments cannot be confused. That is the product principle:
failed review improves the protocol instead of being hidden.”

## 2:30–2:40 — Close

Return to the hero.

“MAT4Person makes research graphs inspectable edge by edge. Every edge shows
its receipts.”
