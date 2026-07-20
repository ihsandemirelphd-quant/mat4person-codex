type PilotSource = {
  source_id: string;
  title: string;
  scope_entity_ids: string[];
  drive: {
    size_bytes: number;
    raw_sha256: string;
  };
  origin: {
    publisher: string;
    canonical_url: string | null;
    rights_status: string;
  };
  analysis_status: string;
  extraction_status: string;
  publication_status: string;
  evidence_claims: number;
  relationship_claims: number;
};

type PilotManifest = {
  baseline_reconciliation: {
    registry_rows: number;
    raw_files_present: number;
  };
  sources: PilotSource[];
};

type ExtractionSource = {
  source_id: string;
  text_artifact_sha256: string;
  page_count: number;
  representative_pages_reviewed: number[];
  review_status: "passed";
  ocr_required_pages: number[];
};

type PilotExtractionReport = {
  counts: {
    sources: number;
    pages: number;
    nonempty_pages: number;
    visually_reviewed_sources: number;
    ocr_required_sources: number;
  };
  sources: ExtractionSource[];
};

const rightsLabels: Record<string, string> = {
  cc_by_4_0: "CC BY 4.0",
  rights_review_required: "rights review",
};

const scopeLabels: Record<string, string> = {
  "person:asim_orhan_barut": "Asım Orhan Barut",
  "person:erdal_inonu": "Erdal İnönü",
  "person:masatoshi_gunduz_ikeda": "Masatoshi Gündüz İkeda",
  "event:2026_inonu_barut_100_anma": "İnönü–Barut 100",
  "institute:feza_gursey_enstitusu": "Feza Gürsey Institute",
};

function formatBytes(value: number) {
  return `${(value / 1_000_000).toFixed(2)} MB`;
}

export function SourceLedger({
  manifest,
  extraction,
}: {
  manifest: PilotManifest;
  extraction: PilotExtractionReport;
}) {
  const records = manifest.sources;
  const licenseVerified = records.filter(
    (record) => record.publication_status === "license_verified",
  ).length;
  const totalBytes = records.reduce((sum, record) => sum + record.drive.size_bytes, 0);
  const extractionBySource = new Map(
    extraction.sources.map((record) => [record.source_id, record]),
  );

  return (
    <section
      className="source-ledger"
      id="source-ledger"
      aria-labelledby="source-ledger-title"
      data-source-candidate-count={records.length}
      data-license-ready-count={licenseVerified}
      data-hash-verified-count={records.length}
      data-extraction-complete-count={extraction.counts.sources}
      data-extraction-pending-count={0}
      data-page-count={extraction.counts.pages}
      data-ocr-required-count={extraction.counts.ocr_required_sources}
    >
      <div className="source-ledger-head">
        <div>
          <p className="eyebrow">Historical pilot · Drive corpus</p>
          <h3 id="source-ledger-title">Ten real documents.<br />162 fresh pages.<br />Zero premature claims.</h3>
        </div>
        <p>
          The participant-authorized Drive files are resolved and hash-verified for
          private analysis, then extracted into page-addressable text and visually
          reviewed. Public reuse is a separate decision: source PDFs and text stay out
          of the site, and no quotation or historical edge is published yet.
        </p>
      </div>

      <div className="source-readiness" aria-label="Source queue readiness">
        <p><strong>{records.length}/10</strong><span>Drive PDFs acquired and hash-verified</span></p>
        <p><strong>{extraction.counts.pages}</strong><span>physical pages freshly extracted</span></p>
        <p><strong>{extraction.counts.ocr_required_sources}</strong><span>sources require OCR after visual review</span></p>
        <p><strong>0</strong><span>historical evidence claims</span></p>
      </div>

      <ul className="source-card-grid">
        {records.map((record, index) => {
          const extractionRecord = extractionBySource.get(record.source_id);
          if (!extractionRecord) return null;
          return (
          <li
            className="source-card"
            data-source-candidate
            data-source-id={record.source_id}
            data-rights-status={record.origin.rights_status}
            data-analysis-status={record.analysis_status}
            data-extraction-status={record.extraction_status}
            key={record.source_id}
          >
            <div className="source-card-index" aria-hidden="true">{String(index + 1).padStart(2, "0")}</div>
            <div className="source-card-body">
              <p className="source-anchor">
                {record.scope_entity_ids.map((id) => scopeLabels[id] ?? id).join(" · ")}
              </p>
              <h4>{record.title}</h4>
              <p className="source-publisher">{record.origin.publisher} · PDF · {formatBytes(record.drive.size_bytes)}</p>
              <div className="source-badges" aria-label="Access and rights status">
                <span>private analysis authorized</span>
                <span>{extractionRecord.page_count} pages · text reviewed</span>
                <span className={`rights-${record.origin.rights_status}`}>{rightsLabels[record.origin.rights_status]}</span>
              </div>
              <p className="source-question">
                <strong>Raw-byte SHA-256</strong>
                <code>{record.drive.raw_sha256.slice(0, 16)}…</code>
              </p>
              <p className="source-question">
                <strong>Page-text artifact SHA-256</strong>
                <code>{extractionRecord.text_artifact_sha256.slice(0, 16)}…</code>
              </p>
              {record.origin.canonical_url ? (
                <a href={record.origin.canonical_url} target="_blank" rel="noreferrer">
                  Inspect publisher record <span aria-hidden="true">↗</span>
                </a>
              ) : null}
            </div>
          </li>
          );
        })}
      </ul>

      <p className="source-ledger-note">
        Baseline check: {manifest.baseline_reconciliation.raw_files_present} of {manifest.baseline_reconciliation.registry_rows} old raw files are present; one PowerPoint is missing. The ten-file pilot now has {formatBytes(totalBytes)} of verified private source bytes and {extraction.counts.nonempty_pages} nonempty page records. Next gate: create and independently review a source-level gold set. This FGE-heavy pilot covers three Suns; the Dilhan Eryurt source batch follows separately.
      </p>
    </section>
  );
}
