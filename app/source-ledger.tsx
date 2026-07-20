type SourceCandidate = {
  source_candidate_id: string;
  anchor_entity_id: string;
  anchor_name: string;
  title: string;
  publisher: string;
  canonical_url: string;
  source_type: string;
  access_status: string;
  rights_status: string;
  ingestion_status: string;
  evidence_claims: number;
  relationship_claims: number;
  research_question: string;
};

const rightsLabels: Record<string, string> = {
  cc_by_4_0: "CC BY 4.0",
  republication_restricted: "link only",
  all_rights_reserved: "rights reserved",
  rights_review_required: "rights review",
};

const accessLabels: Record<string, string> = {
  public_confirmed: "public page",
  public_landing: "public landing",
  intermittent: "intermittent access",
};

export function SourceLedger({ records }: { records: SourceCandidate[] }) {
  const readyCount = records.filter(
    (record) => record.ingestion_status === "license_ready_download_pending",
  ).length;

  return (
    <section
      className="source-ledger"
      id="source-ledger"
      aria-labelledby="source-ledger-title"
      data-source-candidate-count={records.length}
      data-license-ready-count={readyCount}
    >
      <div className="source-ledger-head">
        <div>
          <p className="eyebrow">Historical pilot · source queue</p>
          <h3 id="source-ledger-title">Four leads.<br />Zero borrowed claims.</h3>
        </div>
        <p>
          These are publisher or institution-managed starting points for the four Suns.
          A public link proves availability, not quotation rights. No document text,
          evidence excerpt, gold label, or historical edge has been imported.
        </p>
      </div>

      <div className="source-readiness" aria-label="Source queue readiness">
        <p><strong>{records.length}</strong><span>Sun-specific source leads</span></p>
        <p><strong>{readyCount}</strong><span>licence-ready for controlled ingestion</span></p>
        <p><strong>0</strong><span>historical evidence claims</span></p>
        <p><strong>0</strong><span>historical relationship claims</span></p>
      </div>

      <ul className="source-card-grid">
        {records.map((record, index) => (
          <li
            className="source-card"
            data-source-candidate
            data-anchor-id={record.anchor_entity_id}
            data-rights-status={record.rights_status}
            data-ingestion-status={record.ingestion_status}
            key={record.source_candidate_id}
          >
            <div className="source-card-index" aria-hidden="true">0{index + 1}</div>
            <div className="source-card-body">
              <p className="source-anchor">{record.anchor_name}</p>
              <h4>{record.title}</h4>
              <p className="source-publisher">{record.publisher} · {record.source_type.toUpperCase()}</p>
              <div className="source-badges" aria-label="Access and rights status">
                <span>{accessLabels[record.access_status]}</span>
                <span className={`rights-${record.rights_status}`}>{rightsLabels[record.rights_status]}</span>
              </div>
              <p className="source-question"><strong>Research question</strong>{record.research_question}</p>
              <a href={record.canonical_url} target="_blank" rel="noreferrer">
                Inspect publisher record <span aria-hidden="true">↗</span>
              </a>
            </div>
          </li>
        ))}
      </ul>

      <p className="source-ledger-note">
        Next gate: acquire the licence-ready İkeda PDF bytes, hash the immutable
        revision, inspect pagination, and prepare candidate labels for human
        adjudication. The other three records stay link-only until their terms are cleared.
      </p>
    </section>
  );
}
