import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html", host: "localhost" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the evidence-first product", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /MAT4Person — Evidence-first relationship atlas/);
  assert.match(html, /Every edge should/);
  assert.match(html, /Explore 321 candidate labels/);
  assert.match(html, /Synthetic verification ledger/);
  assert.match(html, /fictional demo/);
  assert.match(html, /data-registry-count="321"/);
  const registryStart = html.indexOf('id="historical-registry"');
  const registryEnd = html.indexOf('id="source-ledger"', registryStart);
  const sourceEnd = html.indexOf('id="evidence-demo"', registryEnd);
  const registryRegion = html.slice(registryStart, registryEnd);
  const sourceRegion = html.slice(registryEnd, sourceEnd);
  assert.equal((registryRegion.match(/data-registry-node/g) ?? []).length, 321);
  assert.equal((registryRegion.match(/data-status="registry-only"/g) ?? []).length, 321);
  assert.equal((registryRegion.match(/data-adjudication="needs_atomic_split_review"/g) ?? []).length, 7);
  assert.doesNotMatch(registryRegion, /data-source-candidate/);
  assert.match(sourceRegion, /data-source-candidate-count="10"/);
  assert.match(sourceRegion, /data-license-ready-count="1"/);
  assert.match(sourceRegion, /data-hash-verified-count="10"/);
  assert.match(sourceRegion, /data-extraction-pending-count="10"/);
  assert.equal((sourceRegion.match(/data-source-candidate=/g) ?? []).length, 10);
  assert.equal((sourceRegion.match(/data-rights-status="cc_by_4_0"/g) ?? []).length, 1);
  assert.doesNotMatch(sourceRegion, /data-registry-node|data-synthetic-verified-demo/);
  assert.ok(html.indexOf("data-synthetic-verified-demo") > sourceEnd);
  assert.match(html, /Ten real documents/);
  assert.match(html, /Zero premature claims/);
  assert.match(html, /Public reuse is a separate decision/);
  assert.match(html, /Candidate registry/);
  assert.match(html, /inclusion does not imply identity resolution/i);
  assert.match(html, /data-synthetic-verified-demo/);
  assert.match(html, /All names, institutions, events, quotations, and relations in this demo are fictional/);
  assert.match(html, /0<\/strong><span>historical edges published/);
  assert.match(html, /og:image/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("removes starter assets and keeps product safeguards", async () => {
  const [page, layout, css, packageJson, registryAtlas] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(new URL("../app/registry-atlas.tsx", import.meta.url), "utf8"),
  ]);
  assert.doesNotMatch(page, /SkeletonPreview|codex-preview/);
  assert.doesNotMatch(layout, /Starter Project|codex-preview|favicon\.svg/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  assert.match(css, /:focus-visible/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /shape-sun/);
  assert.match(css, /shape-planet/);
  assert.match(css, /shape-nebula/);
  assert.match(css, /shape-institution/);
  assert.match(css, /shape-event/);
  assert.match(css, /split-review-badge/);
  assert.match(css, /source-ledger/);
  assert.match(css, /rights-cc_by_4_0/);
  assert.match(css, /forced-colors/);
  assert.doesNotMatch(registryAtlas, /"use client"|onClick|<button|tabIndex/);
  await access(new URL("../public/og.png", import.meta.url));
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
  await assert.rejects(access(new URL("../public/favicon.svg", root)));
});
