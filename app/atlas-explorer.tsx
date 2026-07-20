"use client";

import { useMemo, useState } from "react";

type Entity = { entity_id: string; canonical_name: string; kind: string };
type Verification = {
  status: string; method: string; page_number: number | null;
  char_start: number | null; char_end: number | null; verifier: string;
};
type Evidence = {
  evidence_id: string; quote: string; quote_sha256: string;
  source_id: string; page_status: string; page_start: number | null; verification: Verification;
};
type Actor = { model: string; worker_id: string; prompt_version: string; verdict?: string };
type Relation = {
  relation_id: string; source_entity_id: string; target_entity_id: string;
  relation_type: string; direction: string; confidence: number;
  evidence_ids: string[]; extractor: Actor; verifier: Actor | null;
};

const label = (value: string) => value.replaceAll("_", " ");

export function AtlasExplorer({
  entities, evidence, relations,
}: { entities: Entity[]; evidence: Evidence[]; relations: Relation[] }) {
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState(relations[0]?.relation_id ?? "");
  const names = useMemo(() => new Map(entities.map((item) => [item.entity_id, item.canonical_name])), [entities]);
  const evidenceById = useMemo(() => new Map(evidence.map((item) => [item.evidence_id, item])), [evidence]);
  const filters = ["all", ...Array.from(new Set(relations.map((item) => item.relation_type)))];
  const visible = filter === "all" ? relations : relations.filter((item) => item.relation_type === filter);
  const selected = relations.find((item) => item.relation_id === selectedId) ?? visible[0];
  const selectedEvidence = selected ? evidenceById.get(selected.evidence_ids[0]) : undefined;

  return (
    <div className="atlas-shell">
      <div className="filter-row" role="group" aria-label="Filter relations">
        {filters.map((item) => (
          <button
            className={filter === item ? "active" : ""}
            key={item}
            type="button"
            aria-pressed={filter === item}
            onClick={() => {
              setFilter(item);
              const next = item === "all" ? relations[0] : relations.find((relation) => relation.relation_type === item);
              if (next) setSelectedId(next.relation_id);
            }}
          >
            {label(item)}
          </button>
        ))}
      </div>
      <div className="atlas-layout">
        <div className="relation-list" aria-label="Verified relations">
          {visible.map((relation) => (
            <button
              type="button"
              key={relation.relation_id}
              className={selected?.relation_id === relation.relation_id ? "relation-row selected" : "relation-row"}
              onClick={() => setSelectedId(relation.relation_id)}
            >
              <span className="relation-people">
                <strong>{names.get(relation.source_entity_id)}</strong>
                <i aria-hidden="true">{relation.direction === "directed" ? "→" : "↔"}</i>
                <strong>{names.get(relation.target_entity_id)}</strong>
              </span>
              <span className="relation-type">{label(relation.relation_type)}</span>
              <span className="verified-mark">✓ verified</span>
            </button>
          ))}
        </div>
        <article className="evidence-panel" aria-live="polite">
          {selected && selectedEvidence ? (
            <>
              <div className="panel-kicker"><span>Evidence record</span><code>{selectedEvidence.evidence_id}</code></div>
              <h3>{names.get(selected.source_entity_id)} <span>{selected.direction === "directed" ? "→" : "↔"}</span> {names.get(selected.target_entity_id)}</h3>
              <p className="type-chip">{label(selected.relation_type)}</p>
              <blockquote>“{selectedEvidence.quote}”</blockquote>
              <dl>
                <div><dt>Source</dt><dd>{selectedEvidence.source_id}</dd></div>
                <div><dt>Location</dt><dd>{selectedEvidence.page_status === "exact" ? "Page" : "Text segment"} {selectedEvidence.verification.page_number} · chars {selectedEvidence.verification.char_start}–{selectedEvidence.verification.char_end}</dd></div>
                <div><dt>Match</dt><dd>{label(selectedEvidence.verification.status)} · {selectedEvidence.verification.method}</dd></div>
                <div><dt>Extractor</dt><dd>{selected.extractor.model} · {selected.extractor.worker_id}</dd></div>
                <div><dt>Reviewer</dt><dd>{selected.verifier?.model} · {selected.verifier?.verdict}</dd></div>
                <div><dt>Quote hash</dt><dd><code>{selectedEvidence.quote_sha256.slice(0, 18)}…</code></dd></div>
              </dl>
            </>
          ) : null}
        </article>
      </div>
    </div>
  );
}
