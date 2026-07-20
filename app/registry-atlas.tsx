type RegistryEntity = {
  entity_id: string;
  kind: "person" | "institute" | "event";
  canonical_name: string;
  aliases: string[];
};

type RegistryProvenance = {
  entity_id: string;
  verification_status: "unverified_seed";
  relationship_claims: number;
  adjudication_status: string;
};

type RegistryPresentation = {
  sun_ids: string[];
  nebula_ids: string[];
  default_roles: Record<string, "planet" | "institution" | "event">;
};

const groups = [
  { role: "sun", title: "Four Suns", description: "Central research anchors", plural: "Suns" },
  { role: "nebula", title: "FG nebulae", description: "FGE and FGRC, kept separate", plural: "nebulae" },
  { role: "planet", title: "People in scope", description: "Candidate people; no connection implied", plural: "people" },
  { role: "event", title: "Events in scope", description: "Candidate event labels awaiting source review", plural: "events" },
  { role: "institution", title: "Institutions in scope", description: "Candidate organizations awaiting source review", plural: "institutions" },
] as const;

export function RegistryAtlas({
  entities,
  provenance,
  presentation,
}: {
  entities: RegistryEntity[];
  provenance: RegistryProvenance[];
  presentation: RegistryPresentation;
}) {
  const provenanceById = new Map(provenance.map((item) => [item.entity_id, item]));
  const sunIds = new Set(presentation.sun_ids);
  const nebulaIds = new Set(presentation.nebula_ids);
  const entries = entities.map((entity) => ({
    ...entity,
    provenance: provenanceById.get(entity.entity_id),
    visualRole: sunIds.has(entity.entity_id)
      ? "sun"
      : nebulaIds.has(entity.entity_id)
        ? "nebula"
        : presentation.default_roles[entity.kind],
  }));

  return (
    <section
      className="registry-atlas"
      id="historical-registry"
      aria-labelledby="registry-title"
      data-registry-count={entities.length}
    >
      <div className="registry-head">
        <div>
          <p className="eyebrow">Candidate registry · nodes only</p>
          <h3 id="registry-title">Research scope,<br />before the edges.</h3>
        </div>
        <p>
          These names define search scope only. Inclusion does not imply identity
          resolution, affiliation, membership, collaboration, influence, or event
          participation. Historical edges remain at zero until evidence is located
          and independently verified.
        </p>
      </div>

      <ul className="registry-legend" aria-label="Node shape legend">
        {groups.map((group) => (
          <li key={group.role}>
            <span className={`node-shape shape-${group.role}`} aria-hidden="true" />
            <strong>{group.title}</strong>
            <span>{group.description}</span>
          </li>
        ))}
        <li className="legend-status">
          <span className="status-outline" aria-hidden="true" />
          <strong>Dashed outline</strong>
          <span>unverified registry seed</span>
        </li>
        <li className="legend-status">
          <span className="split-review-swatch" aria-hidden="true" />
          <strong>Amber badge</strong>
          <span>composite label awaiting split review</span>
        </li>
      </ul>

      <div className="registry-groups">
        {groups.map((group) => {
          const members = entries.filter(
            (entry) => entry.visualRole === group.role,
          );
          return (
            <section className={`registry-group registry-${group.role}`} key={group.role}>
              <header>
                <div>
                  <span className={`node-shape shape-${group.role}`} aria-hidden="true" />
                  <h4>{group.title}</h4>
                </div>
                <p><strong>{members.length}</strong> {group.plural}</p>
              </header>
              <ul className="registry-grid">
                {members.map((entry) => (
                  <li
                    className="registry-node"
                    data-registry-node
                    data-kind={entry.kind}
                    data-visual-role={group.role}
                    data-status="registry-only"
                    data-adjudication={entry.provenance?.adjudication_status}
                    key={entry.entity_id}
                  >
                    <span className={`node-shape shape-${group.role}`} aria-hidden="true" />
                    <span className="registry-name">{entry.canonical_name}</span>
                    {entry.provenance?.adjudication_status === "needs_atomic_split_review" ? (
                      <span className="split-review-badge">split review</span>
                    ) : null}
                    <span className="sr-only">
                      {entry.kind}; unverified registry seed; no relationship claims;
                      {entry.provenance?.adjudication_status === "needs_atomic_split_review"
                        ? " composite label awaiting atomic split review"
                        : " atomic split review not required"}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
      <p className="registry-footnote">
        Shape, glow, and fill encode node type only; the dashed card encodes
        unverified status. Seven composite legacy labels are visibly held for atomic
        split review. No date,
        affiliation, discipline, biography, source excerpt, or old relationship was imported.
      </p>
    </section>
  );
}
