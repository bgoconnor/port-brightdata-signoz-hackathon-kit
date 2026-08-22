# SPEC v3 — Evidence-Backed Paper Factory

> **Status: CURRENT AND AUTHORITATIVE**
>
> Owners should read §1–3, then go directly to their track in §5. Historical source
> versions are indexed in [`docs/specs/README.md`](docs/specs/README.md).

Changes from v2: replaces the abstract-to-single-file mechanism demo with a
claim-driven reproduction pipeline. Discovery metadata is no longer treated as
sufficient evidence. A successful run must identify a claim, acquire the paper and
available artifacts, execute a declared experiment, and compare observed evidence
with the paper's stated result. Mechanism demos remain useful but are labeled as
such and never counted as reproductions.

---

## 1. What we're building

**A factory that discovers new AI papers and produces inspectable, evidence-backed
reproduction attempts for feasible claims.**

Scrape arXiv cs.AI new submissions for discovery. Score each paper for whether it
contains a testable claim, then enrich selected candidates with full text, methods,
claimed metrics, linked code, datasets, and environment information. Port governs
a workflow that selects one claim, assesses feasibility, builds an experiment
package, executes it, and compares observed results with a declared acceptance
rule. **A passing process is not automatically a reproduced result.** The evidence
must support the selected claim before a human is asked to approve that outcome.

Second loop: we manufacture a bug in the processing pipeline — upstream data
arriving in a shape the app didn't expect. SigNoz catches it, Port routes it to an
agent that diagnoses from the trace alone and patches it, human approves.

**The app is a paper board. The submission is the factory.**

Theme is *zero downtime* — survive when something breaks. Kunal's examples: UI
changes, APIs break, data in the wrong format. Ours is the third. In the demo,
describe Loop B honestly as a controlled simulation of malformed upstream data.

---

## 2. What the judges said, verbatim-ish

- **Port (Mauritius):** he will not look at your app. His line was *"that's cute —
  show me what factory built it."* He explicitly said you're not obliged to use
  Port, but Port is a platform for building software factories so it's a head start.
  He also said: don't read docs, hook Port MCP to your agent and ask it to build you
  a software factory — **then go look at what it did.**
- **Bright Data (Adam):** the Bright Data team are judges. Public data only; it will
  not authenticate against anything. Scraper Studio supplies self-healing scrapers,
  giving the application a more reliable acquisition contract than hand-written,
  brittle HTML rules. We rely on that capability; we do not rebuild its healing loop.
- **SigNoz (Kevin):** *"we don't expect you guys to be able to use our platform at
  all."* His actual advice: feed the SigNoz docs to your coding agent and let it
  wire the instrumentation. Take that advice literally.

**Consequence for us:** Mauritius will ask what built the paper board. Loop A builds
*reproductions*, which is a different artifact. Loop 0 (§3) closes that gap. It is
~20 minutes of work and it directly answers the one question the Port judge
pre-announced.

---

## 3. Architecture — three loops

### Loop 0 — The factory built the app (NEW, ~20 min, answers the Port judge)

```
Paper board is cataloged in Port as a Service entity
  -> a change request is filed against it as a Port entity
  -> Port workflow: agent implements the change
  -> Review step: human approves
  -> change lands, service entity updated
```

One real change routed through this is enough. Suggested change: "add a
'reproduction status' column to the paper board." Small, visible, and it ties Loop 0
to Loop A on screen.

### Loop A — Paper to reproduction (headline)

```
Bright Data scrapes arXiv cs.AI /new
  -> normalize discovery metadata -> SQLite -> paper board
  -> scoring step flags papers with a potentially testable claim
  -> enrichment fetches full paper + linked public code/data
  -> upsert Paper entity in Port
  -> Port workflow:
       extract one explicit claim and its reported metric
       -> feasibility gate (reproduce / mechanism_demo / blocked)
       -> generate an experiment manifest and versioned package
       -> build a clean isolated environment
       -> execute the declared experiment
            infra/code failure -> repair from evidence (max 2 retries)
            experiment completes -> compare observed vs. reported result
       -> outcome: reproduced / not_reproduced / inconclusive / blocked
       -> Review step: human approves the evidence and label
  -> package + manifest + logs + metrics land in reproductions/{arxiv_id}/
  -> whole run traced in SigNoz
```

### Loop B — Manufactured break (second act, cuttable)

```
make break   (upstream record arrives in an unexpected shape)
  -> pipeline runs, partial failure
  -> SigNoz: 40 rows in, 12 rows out, span event pipeline.processing_failed
  -> alert fires -> POST to Port
       agent gets THE TRACE AND THE REPO ONLY — not the diff
       -> diagnoses, patches, adds regression test
       -> Review step, human approves
  -> re-run, traced clean
```

**Cut order if we're behind: B first, then 0. Never cut A.**

---

## 4. Hard definitions

Do not renegotiate these during the build.

**"Reproduction attempt" means:** an execution against one explicitly quoted or
precisely paraphrased paper claim. The attempt records the paper version, source
URLs, code/data provenance, environment, command, random seeds, reported value,
observed value, comparison rule, logs, and artifacts. Its outcome is one of:
`reproduced`, `not_reproduced`, `inconclusive`, or `blocked`. Only `reproduced`
means the observed evidence met the predeclared comparison rule.

**"Mechanism demo" means:** runnable code that illustrates an idea using synthetic
or toy data but does not test a reported paper result. It is a useful factory output
but is labeled `mechanism_demo` and is never included in the reproduction success
rate.

There is no source-line limit. Runtime, compute, dependency, network, and data
budgets are declared per attempt and enforced by the runner. Generated code runs in
an isolated environment without credentials. Network is disabled during execution;
any permitted public dependencies or datasets are resolved and checksummed during a
separate preparation stage. A workflow may stop honestly at `blocked` when required
code, data, hardware, licenses, methodological detail, or budget is unavailable.

**"The break" means:** a scraped field arrives empty where the transform does
arithmetic. Throws mid-batch — some records written, some not. Partial success is
the realistic failure mode and it reads beautifully in a trace.

**The agent must not be told what the break is.** It gets the trace and the repo.
That claim is the difference between a factory and a magic trick — so **the break
patch is not committed.** Untracked file or generated at demo time.

---

## 5. Tracks

Three owners, working in parallel. **The contracts in §6 are what let you work
without blocking each other — agree on them before you start, then don't change
them without telling the other two.**

---

### BEN — Bright Data + pipeline + app + Port workflows

You own the spine. Everyone else is blocked until T0 lands, so **speed over polish.**

**Now (before anything else)**
- [ ] Bright Data signup → Billing → Overview → Add promo code → `WEMAKEDEVS` ($50)
- [ ] `brightdata scraper create` against arXiv cs.AI /new. **Generation takes
      5–25 min — fire this first, then do everything below while it builds.**
      Schema: title, authors, arxiv_id, abstract, subjects
- [ ] Record the collector ID in `CLAUDE.md`

**T0 — by 13:00**
- [ ] `brightdata/scrape.py` — run collector, normalize to the §6 schema, write SQLite
- [ ] One table. No ORM, no migrations.
- [ ] `board.html` — static, reads from a JSON dump. No build step, no framework.
- [ ] `brightdata/score.py` — flag reproducible papers. **Heuristic first** (keywords:
      algorithm, we propose, toy, synthetic, complexity bound). LLM call only if
      time allows.
- [ ] `make scrape` works end to end from clean checkout
- [ ] **Publish `data/papers.json`** — this is Gracelyn's and Hugh's unblock

**T2 — only if Loop A is green**
- [ ] `make break` — untracked patch introducing the null-arithmetic bug
- [ ] Validation in the pipeline that detects partial writes and fails loudly

**Deliverable to the team by 13:00:** a populated SQLite DB, `data/papers.json`, and
a board that renders.

**T1 — Port factory ownership transferred to Ben**

- [ ] **Workflow A:** flagged paper → full-text/artifact enrichment → claim and
      feasibility gate → experiment package → **execute it** → compare evidence →
      retry implementation failures (max 2) → Review step → approve the outcome
- [ ] The rejection path. Show a failed run being rejected and re-prompted. **This
      is the most important single thing in the demo.**
- [ ] **Workflow 0 (Loop 0):** change request against the board Service → agent
      implements → Review → approve. Run one real change: "add reproduction status
      column to the board."
- [ ] **Workflow B, only after Loop A is green:** accept the SigNoz webhook and
      trigger the reviewed failure-response path.

Ben owns the live Port workflow definitions and their end-to-end verification.
Gracelyn's existing Workflow A and Workflow B definitions are the starting point;
preserve her completed work and extend it rather than replacing it blindly.

---

### GRACELYN — Port context + operator experience

You own the Port context lake, catalog, and operator experience. Port workflow
implementation transferred to Ben after the initial Workflow A and Workflow B
scaffolds were published.

**Now**
- [ ] Port signup (Gmail restriction is lifted today — if it fails, find Mauritius)
- [ ] **Install the Port Claude Code plugin / hook up Port MCP to your agent.** This
      is the single biggest shortcut available. Then *review what it built* — his
      advice was to ask AI to build the factory, then go look at what it did.
- [ ] Grab a t-shirt from Daniela. Free, no factory required.

**T1 — by 15:00. Do these in order; each is demoable alone.**
- [ ] Blueprint: `Paper` — title, authors, arxiv_id, score, status
- [ ] Blueprint: `Reproduction` — paper ref, selected claim, scope, provenance,
      reported/observed values, comparison rule, outcome, evidence path, retries
- [ ] Blueprint: `Service` — for the paper board itself (Loop 0)
- [ ] Seed entities from `data/papers.json` (don't wait for live scraping)
- [ ] Dashboard: papers ingested, reproductions attempted, pass rate, pending reviews

**Deliverable:** a Port catalog and dashboard a stranger can read, plus a clean
handoff of existing workflow context to Ben.

---

### HUGH — SigNoz

You have the hardest setup and the least glamorous demo. Budget accordingly.

**Now — this is a blocker, do it before anything else**
- [ ] SigNoz Cloud needs a **work email**. If nobody has one → self-host.
- [ ] Self-host: Docker Desktop, **allocate 4GB RAM to Docker** (this is the step
      that eats 40 minutes if skipped), run their compose command, create
      `s3.yaml`, admin account at `localhost:8080`, verify with `docker ps`
- [ ] **Feed the SigNoz docs to your coding agent** rather than learning the UI.
      Kevin said outright they don't expect anyone to use the platform unaided.

**T0 — by 13:00**
- [ ] OTel Python SDK in the pipeline, OTLP exporter to SigNoz
- [ ] **One trace visibly landing.** Nothing else matters until this works.
- [ ] Instrument against a stub pipeline if Ben isn't done — don't wait

**T1 — by 15:00**
- [ ] Parent span `pipeline_run`, child span per stage: scrape, normalize, score, write
- [ ] **Row counts in and out as span attributes on every stage.** This is what
      makes a failure diagnosable at a glance — the judge sees 40 in, 12 out. Scored
      criterion: could a judge diagnose the failure from dashboards alone?
- [ ] Named span events: `pipeline.processing_failed`,
      `reproduction.execution_failed`, `reproduction.approved`
- [ ] Metrics: rows per stage, reproduction pass/fail counter
- [ ] A dashboard that tells the story of a run without narration

**T2**
- [ ] Alert rule on partial-write failure → **webhook POST to Port**

**Deliverable:** a dashboard where the break is obvious on sight, and a working
webhook out.

---

### DEMO OWNER — assign someone at 11:00

Not a part-time role. Whoever takes it **does not build features.**

- [ ] Write the demo script at 11:00, before code exists
- [ ] Own the four required shots (§7)
- [ ] **Submit a skeleton at 14:00.** The submission link is editable — submit early
      and edit rather than racing at 17:00
- [ ] Record at 16:00
- [ ] LinkedIn post with photos, tagging WeMakeDevs + sponsors — there's a free MX
      Master Pro for the best one, and it's pure upside

---

## 6. Contracts — agree on these before you start

These are what make the three tracks independent. Changing one silently breaks
someone else's work.

**Paper record shape** (Ben → everyone):

```json
{
  "arxiv_id": "2508.12345",
  "title": "...",
  "authors": ["..."],
  "abstract": "...",
  "subjects": ["cs.AI"],
  "score": 0.82,
  "reproducible": true,
  "scraped_at": "2026-08-22T11:30:00Z"
}
```

- **Ben publishes `data/papers.json`** as soon as he has anything, even hand-faked.
  Gracelyn and Hugh both work off this file, not off the live scraper.
- **Hugh's alert POSTs to a Port webhook URL** that Ben provides. Direction
  matters: SigNoz runs on localhost and Port cannot reach into it. Traffic must flow
  SigNoz → Port.
- **Attempts land in `reproductions/{arxiv_id}/`.** At minimum the directory holds
  `manifest.json`, `README.md`, executable code, a locked dependency description,
  and machine-readable results. Logs and plots may be stored as GitHub workflow
  artifacts with their URLs and digests recorded in Port. The board reads the
  Port outcome; directory existence alone never means success.

**Nobody blocks on live data.** Fake the interface, integrate at 15:00.

---

## 7. Demo evidence

Video is 3–5 minutes. The locally recorded submission brief calls for the terminal
scraping workflow, Port dashboard, live SigNoz monitoring, and Bright Data
auto-repair. Reconfirm the exact required shots at kickoff.

**If it doesn't appear in a shot, it's out of scope.** Cut rule for the whole day.

Bright Data self-healing is part of the acquisition service, not Loop B. If a
self-healing shot remains required, demonstrate or explain the native capability in
a short, bounded segment using the official workflow. Do not build a parallel repair
system or distort Loop B to manufacture a Bright Data failure.

---

## 8. Timing

| Time | What |
|---|---|
| Now | Ben: collector generating. Gracelyn: Port MCP. Hugh: Docker + SigNoz up. |
| 13:00 | **T0 checkpoint.** If the spine isn't up, stop adding and start filming. |
| 14:00 | Submit skeleton (editable link). Pizza. |
| 15:00 | **T1 checkpoint.** Loop A green? If not, cut Loop B now. |
| 16:00 | **Hard freeze.** No new features. Record. |
| 17:00 | Submission. |

---

## 9. Rules of engagement

- Write the demo script before writing code. Build only what appears on screen.
- Prefer boring solutions. Every dependency is a risk at 15:00.
- Commit as you go, clear messages. Commit history is part of the submission.
- Never fake a passing result. If it can't be verified, say so.
- No new features after 15:00. None.
- Feed sponsor docs to your agent instead of reading them. Both the SigNoz and Port
  presenters recommended this from the stage.

---

## 10. Open decisions — resolve by 11:15

- **Publication policy:** every approved attempt is a GitHub PR containing its
  manifest and package. Port approval attests to the reviewed outcome; merging the
  PR publishes the evidence. A green process without a claim comparison cannot be
  labeled `reproduced`.
- Scoring: heuristic vs. LLM call. Start heuristic.
