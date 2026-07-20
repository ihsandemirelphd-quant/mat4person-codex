import demo from "@/data/demo/published.json";
import registry from "@/data/registry/entities.json";
import registryPresentation from "@/data/registry/presentation.json";
import registryProvenance from "@/data/registry/provenance.json";
import { AtlasExplorer } from "./atlas-explorer";
import { RegistryAtlas } from "./registry-atlas";

const stages = [
  ["01", "Ingest", "Hash source bytes and extract page-addressable text."],
  ["02", "Extract", "Luna or Terra proposes candidates in isolated source shards."],
  ["03", "Locate", "Code reproduces every quotation against the bound text artifact."],
  ["04", "Verify", "A separate Sol worker accepts, rejects, or returns an edge for review."],
  ["05", "Merge", "A fail-closed merge rejects missing, stale, foreign, or divergent shards."],
  ["06", "Freeze", "The release records hashes, metrics, models, prompts, and code revision."],
];

const routes = [
  ["Sol", "Reasoning lead", "Schemas, ambiguity, independent review, release"],
  ["Terra", "Document specialist", "OCR, mixed formats, interpretation, tools"],
  ["Luna", "Scale worker", "Repeatable extraction only after the gold gate"],
  ["Code", "Deterministic spine", "Hashes, quote location, validation, merge, metrics"],
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="wordmark" href="#top" aria-label="MAT4Person home">
          <span className="mark" aria-hidden="true">M4</span>
          <span>MAT4Person</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#historical-registry">Registry</a>
          <a href="#evidence-demo">Evidence</a>
          <a href="#method">Method</a>
        </nav>
        <a className="header-cta" href="#atlas">Open the atlas</a>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">Evidence-first relationship research</p>
          <h1>Every edge should<br /><em>show its receipts.</em></h1>
          <p className="hero-lede">
            MAT4Person imports 321 candidate labels into a reviewable registry, then turns
            source documents into a reviewable relationship atlas. Models can propose
            a connection; only located evidence and independent verification publish it.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="#historical-registry">Explore 321 candidate labels</a>
            <a className="text-link" href="#method">Read the six-stage method <span aria-hidden="true">↘</span></a>
          </div>
        </div>

        <aside className="proof-card" aria-label="Synthetic verification ledger">
          <div className="proof-card-head">
            <span>Synthetic verification ledger</span>
            <span className="live-pill"><i /> fictional demo</span>
          </div>
          <div className="proof-connection">
            <div className="person-token warm">BE</div>
            <div className="connection-line"><span>student_teacher</span></div>
            <div className="person-token cool">AD</div>
          </div>
          <blockquote>“{demo.evidence[0].quote}”</blockquote>
          <dl className="proof-meta">
            <div><dt>Located</dt><dd>Text segment {demo.evidence[0].verification.page_number} · exact span</dd></div>
            <div><dt>Extracted</dt><dd>GPT-5.6 Luna</dd></div>
            <div><dt>Reviewed</dt><dd>GPT-5.6 Sol · accept</dd></div>
            <div><dt>Integrity</dt><dd><code>{demo.evidence[0].quote_sha256.slice(0, 12)}…</code></dd></div>
          </dl>
        </aside>
      </section>

      <section className="trust-strip" aria-label="Demonstration status">
        <div><strong>{registry.length}</strong><span>candidate registry labels imported</span></div>
        <div><strong>4 + 2</strong><span>Suns and FG nebulae</span></div>
        <div><strong>{demo.relations.length}</strong><span>verified synthetic test edges</span></div>
        <div><strong>0</strong><span>historical edges published</span></div>
      </section>

      <section className="section atlas-section" id="atlas">
        <div className="section-heading split-heading">
          <div>
            <p className="eyebrow">Interactive proof</p>
            <h2>See every node.<br />Believe no edge without evidence.</h2>
          </div>
          <p>
            The historical layer imports 321 participant-directed candidate labels
            with provenance but no old graph claims. A separate fictional
            run demonstrates the complete evidence and verification path.
          </p>
        </div>
        <RegistryAtlas
          entities={registry}
          provenance={registryProvenance}
          presentation={registryPresentation}
        />
        <div className="synthetic-heading" id="evidence-demo">
          <div>
            <p className="eyebrow">Verified synthetic test</p>
            <h3>Now inspect an edge<br />and its receipts.</h3>
          </div>
          <p>
            This layer is deliberately fictional. It proves the publication gate
            without visually mixing unverified historical nodes with verified edges.
          </p>
        </div>
        <div className="demo-disclaimer"><span>Demo boundary</span>{demo.disclaimer}</div>
        <section aria-label="Synthetic verified evidence demo" data-synthetic-verified-demo>
          <AtlasExplorer
            entities={demo.entities}
            evidence={demo.evidence}
            relations={demo.relations}
          />
        </section>
      </section>

      <section className="section method-section" id="method">
        <div className="section-heading">
          <p className="eyebrow">Deterministic spine</p>
          <h2>Models judge. Code keeps the record honest.</h2>
        </div>
        <div className="stage-grid">
          {stages.map(([number, title, body]) => (
            <article className="stage-card" key={number}>
              <span>{number}</span><h3>{title}</h3><p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section routing-section">
        <div className="routing-intro">
          <p className="eyebrow">GPT-5.6 routing</p>
          <h2>Use the smallest model that has earned the job.</h2>
          <p>
            Luna is not a weaker Terra hidden inside it. It is a speed-and-cost route
            for stable work. Terra handles interpretation. Sol owns the decisions
            that change what the atlas claims.
          </p>
        </div>
        <div className="route-list">
          {routes.map(([name, role, work], index) => (
            <article key={name}>
              <span className={`route-dot route-${index + 1}`} />
              <h3>{name}</h3><strong>{role}</strong><p>{work}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section plugin-section" id="plugin">
        <div>
          <p className="eyebrow">Codex plugin</p>
          <h2>Bring the protocol to your own archive.</h2>
          <p>
            The repository includes the installable <strong>mat4person-evidence-atlas</strong>
            plugin, a reusable Build Evidence Atlas skill, frozen JSON contracts, and a
            standalone quotation verifier.
          </p>
        </div>
        <div className="command-card" aria-label="Plugin capabilities">
          <p><span>01</span> Create immutable source revisions</p>
          <p><span>02</span> Separate candidate extraction from review</p>
          <p><span>03</span> Locate and hash exact quotations</p>
          <p><span>04</span> Evaluate Luna before scaling it</p>
          <p><span>05</span> Freeze a tamper-evident release</p>
        </div>
      </section>

      <section className="status-section">
        <p className="eyebrow">Research status</p>
        <h2>The method is ready.<br />The historical corpus is not yet claimed.</h2>
        <div className="status-grid">
          <p><strong>Ready now</strong>321 provenance-marked candidate labels, contracts, validators, plugin skill, synthetic vertical slice, and public interface.</p>
          <p><strong>Next controlled gate</strong>Rights review and a human-labeled 8–12 source pilot covering the four Suns and FGE/FGRC.</p>
          <p><strong>Only after freeze</strong>Comparison with the previous Gemini/Claude graph and publication of supported historical relations.</p>
        </div>
      </section>

      <footer>
        <div className="wordmark"><span className="mark" aria-hidden="true">M4</span><span>MAT4Person</span></div>
        <p>Built with Codex and the GPT-5.6 model family · Clean-room run</p>
        <a href="#top">Back to top ↑</a>
      </footer>
    </main>
  );
}
