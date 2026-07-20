# MAT4Person Evidence Atlas

MAT4Person is a Codex plugin and reproducible pipeline for building relationship
graphs from research documents without losing the evidence behind each edge.
A model can propose a relation, but it cannot become accepted until
deterministic code locates its quotation in a content-addressed text artifact
and a separate GPT-5.6 reviewer records a verdict.

The product includes immutable source ingestion, exact and normalized quote
location, entity-aware JSON contracts, isolated worker shards, deterministic
fail-closed merge, a source-level gold evaluation gate, tamper-evident freeze
manifests, an installable `build-evidence-atlas` Codex skill, and an interactive
OpenAI Sites evidence explorer.

We use GPT-5.6 Sol for architecture, ambiguity, and independent verification;
Terra for interpretive or tool-heavy documents; and Luna for high-volume
candidate extraction only after it passes a locked human gold gate. Code owns
hashing, normalization, quotation location, validation, merging, and metrics.

The included demonstration is fully fictional and reports zero historical
claims. This clean-room boundary lets judges test the entire vertical slice
without importing outputs from the project’s earlier Gemini/Claude baseline.
The next controlled step is a rights-reviewed, human-labeled 8–12 source pilot
covering the four central scientists and the separate FGE/FGRC institutions.

Best-fit track: **Developer Tools**.
