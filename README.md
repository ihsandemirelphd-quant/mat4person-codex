# MAT4Person Evidence Atlas

MAT4Person is a Codex plugin and reproducible pipeline for turning source
documents into relationship graphs where every accepted edge is bound to a
located quotation, an immutable source revision, and an independent review.

This repository is a clean-room GPT-5.6 reproduction of the earlier 4 Suns and
Feza Gürsey experiment. It does **not** import the earlier Gemini/Claude code,
prompts, graph outputs, or claims.

**Live demonstration:** https://mat4person-evidence-atlas.ihsandemirel076.chatgpt.site

## What works now

- Content-addressed UTF-8 ingestion with explicit paginated/unpaginated status.
- Exact and NFKC/whitespace-normalized quotation location with hashes and
  Unicode code-point offsets.
- Entity, source, text-artifact, evidence, relation, run, shard, and gold-label
  contracts.
- Independent extractor/verifier enforcement.
- Isolated per-source worker shards and deterministic fail-closed merge.
- Source-level gold evaluation with a predeclared Luna quality gate.
- Tamper-evident freeze manifests.
- An installable Codex plugin with the reusable `build-evidence-atlas` skill.
- A complete synthetic demonstration and interactive OpenAI Sites interface.

The bundled demonstration is fictional. It validates the product path but does
not claim that Luna has passed the future historical gold set.

## Architecture

```text
source bytes → immutable text artifact → candidate shard
                                      ↓
                        deterministic quote locator
                                      ↓
                  independent Sol review + verdict
                                      ↓
              fail-closed merge → gold gate → freeze → site
```

Model routing:

- **GPT-5.6 Sol:** contracts, ambiguous decisions, independent verification,
  merge review, and release.
- **GPT-5.6 Terra:** tool-heavy or interpretive document work.
- **GPT-5.6 Luna:** repetitive candidate extraction only after the real gold
  gate passes.
- **Code:** every reproducible operation: hashes, quotation location, schema
  checks, merge, metrics, and freezing.

## Quick start

Requirements: Python 3.11+, Node 22.13+, pnpm, and Git.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
pnpm install

.\.venv\Scripts\python.exe -m pipeline.demo
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
pnpm test
```

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with
`.venv/bin/python`.

The site runs with:

```text
pnpm run dev
```

## Plugin installation

The plugin is designed for Codex environments that support local plugins.
From the cloned repository:

```text
codex plugin marketplace add .
codex plugin add mat4person-evidence-atlas@personal
```

Start a new Codex task after installation, then try:

```text
Use $build-evidence-atlas to audit data/demo/published.json against its source.
```

The plugin lives in
`plugins/mat4person-evidence-atlas/`. Its standalone quotation checker needs
only Python's standard library.

## Pipeline commands

```text
mat4person ingest <utf8-text> <output> --source-id source:id --title "Title"
mat4person verify-quotes <evidence.json> <source-text.json> <output.json>
mat4person validate-shard <run.json> <shard.json>
mat4person merge <run.json> <shards-dir> <bundle-dir>
mat4person evaluate <gold.json> <bundle-dir> <metrics.json>
mat4person freeze <bundle-dir> <manifest.json> --run-id run:id --check-clean
```

All commands fail with a non-zero exit when an acceptance condition is
violated. Worker shards never edit shared graph files.

## How Codex and GPT-5.6 were used

Codex built the clean repository, deterministic contracts, tests, plugin skill,
synthetic run, and site. Parallel agents independently audited source
availability, current Build Week rules, contract correctness, and the finished
skill. One forward-test found that the initial demo invented “page 1” for plain
text; the pipeline was changed so unpaginated sources use null page bounds and
physical text segments are recorded separately.

Human product decisions define the research question, clean-room boundary,
allowed relation taxonomy, model-cost policy, publication standard, and the
rule that historical claims remain unpublished until rights review and a human
gold set are complete.

## Clean-room and data policy

- Previous model outputs remain comparison-only until the fresh run is frozen.
- AI-authored scans and summaries cannot support accepted relations.
- Copyrighted raw documents stay outside Git.
- Public artifacts may contain source metadata, hashes, lawful URLs, short
  excerpts, and derived records.
- FGE and FGRC remain separate entities. The İkeda genealogy layer is deferred.

See [the experiment protocol](docs/experiment-protocol.md),
[the controlled pilot plan](docs/pilot-plan.md), and
[the submission checklist](docs/submission-checklist.md).

## Build Week judging path

Best-fit track: **Developer Tools**.

Judges can use the [deployed site](https://mat4person-evidence-atlas.ihsandemirel076.chatgpt.site) for a no-build product walkthrough, clone this
repository for the complete deterministic test path, or install the local
plugin and run it against the included synthetic source. No account or paid API
key is required for the synthetic pipeline test.

## License

Code and original documentation are MIT licensed. Source documents and quoted
archival material retain their respective rights.
