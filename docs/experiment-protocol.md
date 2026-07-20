# Clean-room experiment protocol

## Research question

Can Codex and the GPT-5.6 model family reproduce an evidence-first relationship
atlas from primary historical documents while improving traceability,
verification, and reproducibility over the previous MAT4Person runs?

## Isolation rule

The previous `math_fidani` relation outputs, prompts, generated graphs, reports,
and website implementation are embargoed until the clean run is frozen in a
tagged commit. Domain requirements may be recovered from the supplied roadmap:
the four central scientists, FGE and FGRC, the approved relation taxonomy, and
the separate İkeda genealogy concept.

Old AI-authored scans and summaries are not primary evidence. They may be
introduced only during the comparison phase and must be labeled as baseline
material.

## Phases

1. **Protocol:** freeze contracts, model routing, tests, and acceptance gates.
2. **Pilot corpus:** process 8–12 high-quality primary sources.
3. **Gold evaluation:** manually label positive, negative, and ambiguous cases.
4. **Candidate extraction:** run isolated source batches through Luna or Terra.
5. **Mechanical validation:** reject invalid schemas, missing quotations,
   unresolved entities, and unlocatable evidence.
6. **Independent verification:** use Sol with high reasoning on survivors.
7. **Freeze:** commit the validated graph and run report before baseline access.
8. **Comparison:** measure overlap, disagreements, unsupported edges, and new
   discoveries against the old run.
9. **Publication:** package the reusable plugin and publish the Sites atlas.

## Acceptance gate for a relation

A relation can become `accepted` only when:

- its source and target resolve to registered entities;
- at least one evidence record cites a stable `source_id`;
- each evidence quotation is non-empty and locatable in the extracted source;
- page information is exact, explicitly unavailable, or explicitly unknown;
- the relation type is part of the frozen taxonomy;
- a verifier distinct from the extraction worker records a verdict; and
- deterministic contract and cross-reference checks pass.

## Model routing

- Sol owns schemas, architecture, difficult judgments, independent verification,
  merges, final review, and publication.
- Terra handles sources that require substantial interpretation or tool use.
- Luna handles stable, repetitive extraction only after matching the gold-set
  quality threshold.
- At most three workers run concurrently. Workers emit separate source shards;
  they never edit shared graph or report files.

## Minimum reported metrics

- sources attempted, completed, failed, and excluded;
- candidates proposed and rejected at each gate;
- accepted relations by type and confidence;
- evidence records with exact pages, unpaginated sources, and unknown pages;
- gold-set precision, recall, and unresolved rate;
- model and prompt version by phase;
- source hash, repository commit, and run identifier; and
- baseline overlap and disagreement counts after the freeze.

## Phase 0 completion

Phase 0 does not process the real corpus. It is complete when the contracts,
fixtures, tests, Sites application, plugin manifest, repository policy, and
this protocol validate together.
