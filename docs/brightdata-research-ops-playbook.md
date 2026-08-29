# Bright Data playbook for research and operations agents

This document captures the durable lessons from building Paper Factory. It is
intended as shared context for a future hackathon where Bright Data supplies
public web data to multi-purpose research and operations agents.

## The short version

Bright Data should be the acquisition layer, not the database, workflow engine,
or reasoning system. A hosted collector gives agents a more stable contract than
hand-maintained page selectors, and Bright Data's self-healing reduces breakage
when a source changes. It does **not** guarantee that a collector returns every
field the application needs, that linked PDFs become text, or that output is
automatically persisted in our system.

The reliable pattern is:

```text
public source
  -> hosted Bright Data collector
  -> asynchronous collection ID
  -> retrieve and validate completed dataset
  -> normalize into a source-neutral contract
  -> persist transactionally in PostgreSQL/object storage
  -> publish an event or work request
  -> research/ops agents reason over persisted evidence
  -> retain provenance, outputs, failures, and retries
```

Design the product around that boundary from the beginning.

## 1. What Bright Data does—and does not do

### Bright Data is good at

- Running hosted scrapers against public websites.
- Traversing a listing page into a bounded set of detail pages.
- Returning structured datasets rather than forcing every consumer to parse HTML.
- Absorbing many source-layout changes through Scraper Studio's self-healing.
- Giving an application an asynchronous trigger/status/dataset lifecycle.
- Providing one acquisition mechanism for heterogeneous public sources such as
  paper indexes, research blogs, documentation, status pages, changelogs, and
  public incident or release feeds.

### Bright Data is not automatically

- A source of complete research evidence. A title and abstract are discovery
  metadata, not a complete paper.
- A PDF-to-text system. A collector may return a PDF URL while leaving
  `full_text` empty.
- A database or durable product state. Completed datasets must be retrieved,
  normalized, and persisted by the application.
- A scheduler, work queue, agent coordinator, or review system.
- A guarantee that a generated collector meets our semantic contract.
- A substitute for application-level validation, provenance, retries, and
  observability.

The most important conceptual correction from this project was: **self-healing
means the hosted scraper attempts to preserve its extraction behavior when the
site changes; it does not mean the downstream product heals itself or that missing
capabilities appear automatically.**

## 2. Start with the data contract, not the scraper prompt

Define the normalized record before creating collectors. A useful multi-source
research/ops envelope is:

```json
{
  "record_id": "{source}:{source_id}",
  "source": "arxiv",
  "source_id": "2608.19202",
  "kind": "research_paper",
  "title": "...",
  "summary": "...",
  "authors": ["..."],
  "subjects": ["..."],
  "published_at": "2026-08-22T00:00:00Z",
  "source_url": "https://...",
  "document_url": "https://...pdf",
  "full_text": "...",
  "content_sha256": "...",
  "acquired_at": "2026-08-22T21:00:00Z",
  "collector_id": "c_...",
  "collection_id": "j_...",
  "raw_object_uri": "s3://.../raw.json",
  "schema_version": "research-record/v1"
}
```

Use `{source}:{source_id}` as the durable identity. Do not pretend every source
has an arXiv ID, GitHub repository, incident number, or other source-specific key.
Retain source-specific fields when useful, but keep them nullable and subordinate
to the source-qualified identity.

Define explicit validity tiers:

- `discovered`: identity, title, summary, source URL.
- `enriched`: usable body text and acquisition provenance.
- `actionable`: passes the domain-specific gate for an agent task.
- `verified`: an agent output has supporting evidence and passed its acceptance
  rule.

This prevents an abstract-only record from silently entering a workflow that
requires methods, metrics, or complete instructions.

## 3. Separate discovery from enrichment

A listing page and a complete document are different acquisition problems.

### Discovery collector

Use a cheap, bounded collector to identify candidates:

- source ID
- title
- authors or owner
- abstract/summary
- tags or subjects
- publication/update time
- detail-page and document URLs

### Enrichment collector or extractor

Run only for selected candidates and acquire what the agent actually needs:

- complete article or document text
- methods/procedures
- linked code and datasets
- release notes or operational changes
- tables, metrics, and evidence links
- checksums and source timestamps

This two-stage design controls cost and latency while avoiding the false belief
that discovery metadata is sufficient for deep agent work.

For PDFs, treat extraction as a distinct capability. Our live evaluations showed
that collectors for public research pages could reliably return metadata and
direct PDF URLs while returning no `full_text`. Attempts to self-heal those
collectors into general PDF text extractors failed. Plan a dedicated PDF/document
extraction stage rather than assuming link traversal will solve it.

## 4. Bounded fan-out must be explicit

A listing is an index page containing links to many records. “Fan-out” means the
collector visits some of those detail links and returns complete records. Bound it
deliberately:

- maximum records per run
- maximum detail pages followed
- maximum runtime and cost
- pagination cursor or `skip` value
- source/date/category filters

Our arXiv collector followed at most three detail pages per run. The `/new` page
returned only two records on one run; a `/recent?skip=0&show=25` run returned three.
To build a large initial catalog, use pagination or a committed bootstrap dataset.
Do not confuse “every new record from now on” with “enough historical records to
make the product useful on day one.”

Recommended modes:

1. **Bootstrap:** backfill bounded historical pages until the catalog is useful.
2. **Incremental:** poll the new/recent feed and upsert by source-qualified ID.
3. **Targeted enrichment:** fetch full content for records selected by policy or a
   human.
4. **Refresh:** reacquire records when their source timestamp or content hash
   changes.

## 5. Use the asynchronous lifecycle correctly

The application should own a durable run record with at least:

```text
source
collector_id
target_url / input
collection_id
status: submitted | collecting | ingesting | completed | failed | canceled
source_status
records_received
records_written
failure_count
error
started_at / finished_at / completed_at
```

The runtime sequence is:

1. Trigger the collector and persist the returned collection ID immediately.
2. Poll status with a deadline and visible progress.
3. Retrieve the dataset only after completion.
4. Validate the entire batch against the declared contract.
5. Preserve raw output for debugging.
6. Normalize and upsert transactionally.
7. Record counts and exact failures.
8. Emit downstream work only after durable persistence succeeds.

Do not make a request wait indefinitely for scraping. Return a run ID to the UI or
agent and let it poll. Long-running collector generation, healing, and collection
should be started early while other work continues.

## 6. Validate semantics, not merely HTTP success

“The API returned 200” is weak evidence. Validate:

- required identity and title fields
- source URL and document URL shape
- correct output envelope (`list`, nested records, JSONL, and so on)
- minimum body length for enriched records
- absence of placeholder/error-page text
- per-source author and date conventions
- uniqueness by `{source}:{source_id}`
- content hash stability
- counts expected for the requested bound

For a full-text contract, reject records below a meaningful length rather than
silently labeling them enriched. Store discovery-only records, but keep their tier
honest.

Decide batch semantics explicitly:

- **Atomic batch:** validate everything before writing anything. Best when partial
  state would mislead downstream agents.
- **Per-record acceptance:** write valid records, quarantine failures, and report
  `records_received`, `records_written`, and `failure_count`. Best for broad
  research/ops feeds where one malformed page should not discard the rest.

Do not accidentally claim partial-write behavior while the code normalizes the
entire batch before its first database write.

## 7. Persist in the right places

Use PostgreSQL for queryable runtime state:

- normalized records
- acquisition runs and statuses
- agent work requests
- current output state
- relations and review decisions

Use object storage for large or immutable evidence:

- raw Bright Data payloads
- PDFs and downloaded documents
- extracted full text snapshots
- generated packages and websites
- logs, traces, screenshots, and evaluation artifacts

Store URIs and hashes in PostgreSQL. Local JSON and Markdown files are useful as
committed bootstrap fixtures or test data, not as live cross-machine state.

## 8. Credentials and collector ownership are coupled

An API key can authenticate successfully and still receive `404 Collector not
found`. In our case, that meant the key belonged to a different Bright Data
account/workspace than the collector—not that the collector ID was necessarily
wrong.

Before integration work, verify all four together:

1. Bright Data account/workspace.
2. API key created in or authorized for that workspace.
3. Collector visible to that account.
4. One live trigger/status/dataset round trip using that exact key.

Record collector IDs in configuration, never embed keys in code. Put local keys in
an ignored `.env`, deliver them to Kubernetes through a Secret, and verify presence
without printing values. Do not create replacement collectors merely to work
around an ownership mismatch; that creates divergent contracts and more confusion.

## 9. Multi-source agents need adapters, not one universal schema prompt

Each source should have a small adapter that maps hosted collector output into the
shared envelope. Keep collector-specific oddities at that edge.

Useful source families for a research/ops agent system:

- Research: arXiv listings, lab research pages, proceedings, public paper pages.
- Engineering: documentation, changelogs, GitHub releases, public issue trackers.
- Operations: vendor status pages, incident histories, advisories, maintenance
  notices, public cloud/service updates.
- Market/context: public announcements, pricing pages, product catalogs, policy
  pages, and regulatory publications.

Do not assume a collector that works for one publisher will generalize across
heterogeneous publisher pages and PDFs. Prefer one tested collector per coherent
source family, then normalize downstream.

## 10. Give agents evidence pointers, not giant transient prompts

Once data is durable, an agent work request should contain:

- normalized record ID
- task type and acceptance rule
- relevant object-store URIs and hashes
- acquisition run/collection ID
- allowed tools and budgets
- correlation/trace ID
- prior attempt observations

Avoid passing huge bodies through every coordination layer when an authenticated
worker can load the canonical record from PostgreSQL/object storage. If content
must cross a service boundary, bound its size, record that truncation, and never
call a partial excerpt “the complete document.”

Separate agent roles where practical:

- acquisition agent: triggers and diagnoses collectors
- normalization agent: maps and validates source output
- research agent: synthesizes evidence and identifies uncertainty
- operations agent: turns changes/incidents into bounded actions
- verifier: checks outputs against explicit rules
- reviewer: approves consequential results

Retries must receive observed failures—validation errors, runtime output, trace
summaries—not a vague “try again.” Cap retries and preserve every attempt.

## 11. Observability should tell the acquisition story

Instrument the real path before building dashboards. A useful trace has:

```text
acquisition_run
  -> collector.trigger
  -> collector.poll
  -> dataset.retrieve
  -> records.validate
  -> records.normalize
  -> database.upsert
  -> downstream.dispatch
```

Attach:

- source, collector ID, and collection ID
- target/pagination mode without credentials
- rows received, valid, written, and rejected
- bytes retrieved and body-length distribution
- elapsed time per stage
- retry count and terminal status
- record IDs or a bounded sample, not full sensitive bodies

Emit named events for contract failures. Verify that the telemetry collector is
actually listening and that traces land in storage; environment variables and
healthy pods alone do not prove observability. In this project, SigNoz's collector
service exposed OTLP port 4318, but an OpAMP-provided no-op runtime configuration
left the process refusing connections. A visible trace is the acceptance test.

## 12. Failure modes we actually encountered

### Collector ownership mismatch

**Symptom:** authentication succeeds, collector lookup returns 404.

**Lesson:** verify account/workspace ownership before changing application code.

### Metadata without complete content

**Symptom:** dozens of valid records and PDF URLs, but every `full_text` is empty.

**Lesson:** distinguish discovery success from enrichment success; use a dedicated
document extraction stage.

### Self-heal does not create a missing capability

**Symptom:** a targeted heal asking for PDF-body extraction fails activation and
leaves the collector unchanged.

**Lesson:** self-healing protects an existing extraction contract; it is not a
general-purpose workflow synthesis guarantee.

### A bounded collector looks “stuck” or “too small”

**Symptom:** waiting for a batch, or seeing only two/three records on the page.

**Lesson:** expose run status, bound fan-out, paginate deliberately, and seed a
bootstrap catalog separately from incremental scraping.

### Local files masquerade as application state

**Symptom:** agents see JSON/Markdown outputs on one machine but the app and other
agents do not.

**Lesson:** commit fixtures; persist runtime records and artifacts in shared
services.

### Additive data is not automatically integrated

**Symptom:** a generated artifact exists, but the application or catalog shows no
corresponding domain entity.

**Lesson:** define the complete write-back contract before generation: which
database row, catalog entity, status, evidence link, and UI state are updated.

## 13. Hackathon operating plan

### Before the event

- Create the Bright Data workspace and invite every operator.
- Generate a machine API key in the collector-owning workspace.
- Create and live-test one collector per critical source family.
- Save sample raw outputs and contract tests.
- Prepare a bootstrap dataset large enough to make the UI credible.
- Decide discovery/enrichment tiers and object-store layout.
- Build a fake collector adapter for offline development.

### First hour

1. Trigger the slowest collector or generation job immediately.
2. Verify credentials, collector visibility, and one collection ID.
3. Persist one real record end to end.
4. Display it in the app.
5. Produce one real trace.
6. Only then expand sources, dashboards, agents, or repair loops.

### Definition of done for each source

- [ ] Hosted collector is visible to the deployment credential.
- [ ] Trigger returns a collection ID.
- [ ] Status polling reaches a terminal state.
- [ ] Dataset retrieval returns the expected envelope.
- [ ] Contract validation covers required fields and semantic minimums.
- [ ] Raw output is retained with provenance.
- [ ] Normalized records are idempotently persisted.
- [ ] Pagination/bounds are explicit.
- [ ] UI or agent can observe current state.
- [ ] At least one failure path is tested.
- [ ] Trace/log evidence is visibly stored.
- [ ] Downstream output writes back to its domain entity.

## 14. Recommended MVP architecture

For the next multi-purpose research/ops agent hackathon, build only this spine
before adding sophistication:

```text
Source Registry
  source family + collector ID + normalized adapter + schedule/bounds

Acquisition API
  POST /runs -> collection ID
  GET /runs/{id} -> lifecycle/counts/error

Ingestion Worker
  retrieve -> retain raw -> validate -> normalize -> PostgreSQL/object store

Policy Gate
  selects actionable records by type, freshness, completeness, and cost

Agent Worker
  loads canonical evidence -> performs bounded task -> retains attempts

Verifier
  applies explicit acceptance rules -> pass/fail/blocked with observations

Operator UI
  records, acquisition state, agent state, evidence links, retry/review controls
```

Start with one research source and one operations source. Demonstrate one complete
artifact from each. Breadth is useful only after the end-to-end write-back path is
real.

## 15. Principles to carry forward

1. Bright Data owns reliable public-web acquisition; our system owns meaning.
2. Self-healing reduces scraper maintenance; it does not remove contract testing.
3. Discovery and enrichment are separate stages with separate success criteria.
4. Persist first, dispatch second.
5. Source-qualified identity and provenance are non-negotiable.
6. A URL to a document is not the document's text.
7. Bounded fan-out and pagination must be visible product behavior.
8. Bootstrap data and incremental data solve different problems.
9. Every generated artifact needs an explicit write-back and UI/catalog state.
10. A successful process is not automatically a successful domain outcome.
11. Retry from evidence, cap attempts, and preserve failures.
12. Verify with live records, stored artifacts, and visible traces—not configuration
    alone.

