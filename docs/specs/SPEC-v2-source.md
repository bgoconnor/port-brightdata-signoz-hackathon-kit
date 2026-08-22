# SPEC v2 — Paper Factory

Team spec, parallelized. Read §1–3, then go straight to your own track in §5.

Changes from v1: added the factory-built-the-app loop (§3, Loop 0), split work into
three independent owner tracks with explicit contracts between them, and folded in
the workshop findings.

---

## 1. What we're building

**A factory that reads new AI papers and manufactures runnable code from the good
ones.**

Scrape arXiv cs.AI new submissions. Score each paper for whether it has a
reproducible core claim. High-scoring papers trigger a Port workflow where a coding
agent writes a minimal executable illustration of the paper's central mechanism.
**The code must actually run before a human is asked to approve it.**

Second loop: we manufacture a bug in the processing pipeline — upstream data
arriving in a shape the app didn't expect. SigNoz catches it, Port routes it to an
agent that diagnoses from the trace alone and patches it, human approves.

**The app is a paper board. The submission is the factory.**

Theme is *zero downtime* — survive when something breaks. Kunal's examples: UI
changes, APIs break, data in the wrong format. Ours is the third. **Narrate it as
upstream data caused this**, never as "we broke our own code."

---

## 2. What the judges said, verbatim-ish

- **Port (Mauritius):** he will not look at your app. His line was *"that's cute —
  show me what factory built it."* He explicitly said you're not obliged to use
  Port, but Port is a platform for building software factories so it's a head start.
  He also said: don't read docs, hook Port MCP to your agent and ask it to build you
  a software factory — **then go look at what it did.**
- **Bright Data (Adam):** the Bright Data team are judges. Public data only; it will
  not authenticate against anything. Scraper Studio gives self-healing scrapers —
  contrast with Beautiful Soup, where you hand-write brittle HTML rules.
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
  -> normalize -> SQLite -> paper board (static HTML)
  -> scoring step flags papers with a reproducible core claim
  -> upsert Paper entity in Port
  -> Port workflow:
       agent reads abstract
       -> writes ONE self-contained Python file
       -> WORKFLOW EXECUTES IT
            fails  -> reject, re-prompt with traceback (max 2 retries)
            passes -> Review step, human approves
  -> lands in reproductions/
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

**"Reproduction" means:** one self-contained Python file, under 100 lines, toy data
generated in-file, runs in under 10 seconds, prints one number or writes one plot.
It is **not** a replication of results — it's a *minimal executable illustration of
the central mechanism*. We say exactly that on camera.

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

### BEN — Bright Data + pipeline + app

You own the spine. Everyone else is blocked until T0 lands, so **speed over polish.**

**Now (before anything else)**
- [ ] Bright Data signup → Billing → Overview → Add promo code → `WEMAKEDEVS` ($50)
- [ ] `brightdata scraper create` against arXiv cs.AI /new. **Generation takes
      5–25 min — fire this first, then do everything below while it builds.**
      Schema: title, authors, arxiv_id, abstract, subjects
- [ ] Record the collector ID in `CLAUDE.md`

**T0 — by 13:00**
- [ ] `scrape.py` — run collector, normalize to the §6 schema, write SQLite
- [ ] One table. No ORM, no migrations.
- [ ] `board.html` — static, reads from a JSON dump. No build step, no framework.
- [ ] `score.py` — flag reproducible papers. **Heuristic first** (keywords:
      algorithm, we propose, toy, synthetic, complexity bound). LLM call only if
      time allows.
- [ ] `make scrape` works end to end from clean checkout
- [ ] **Publish `data/papers.json`** — this is Gracelyn's and Hugh's unblock

**T2 — only if Loop A is green**
- [ ] `make break` — untracked patch introducing the null-arithmetic bug
- [ ] Validation in the pipeline that detects partial writes and fails loudly

**Deliverable to the team by 13:00:** a populated SQLite DB, `data/papers.json`, and
a board that renders.

---

### GRACELYN — Port

You own the thing that's actually being judged. Mauritius said it plainly: he will
not look at the app.

**Now**
- [ ] Port signup (Gmail restriction is lifted today — if it fails, find Mauritius)
- [ ] **Install the Port Claude Code plugin / hook up Port MCP to your agent.** This
      is the single biggest shortcut available. Then *review what it built* — his
      advice was to ask AI to build the factory, then go look at what it did.
- [ ] Grab a t-shirt from Daniela. Free, no factory required.

**T1 — by 15:00. Do these in order; each is demoable alone.**
- [ ] Blueprint: `Paper` — title, authors, arxiv_id, score, status
- [ ] Blueprint: `Reproduction` — paper ref, status, run result, file path, retries
- [ ] Blueprint: `Service` — for the paper board itself (Loop 0)
- [ ] Seed entities from `data/papers.json` (don't wait for live scraping)
- [ ] **Workflow A:** flagged paper → agent writes repro → **execute it** →
      Review step → approve
- [ ] The rejection path. Show a failed run being rejected and re-prompted. **This
      is the most important single thing in the demo** — it's what separates us from
      a wrapper that prints LLM output.
- [ ] Dashboard: papers ingested, reproductions attempted, pass rate, pending reviews
- [ ] **Workflow 0 (Loop 0):** change request against the board Service → agent
      implements → Review → approve. Run one real change: "add reproduction status
      column to the board."

**T2**
- [ ] Workflow B: accept the SigNoz webhook, trigger diagnose-and-patch

**Deliverable:** a Port dashboard a stranger can read, and two workflows that run
live.

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
- **Hugh's alert POSTs to a Port webhook URL** that Gracelyn provides. Direction
  matters: SigNoz runs on localhost and Port cannot reach into it. Traffic must flow
  SigNoz → Port.
- **Reproductions land in `reproductions/{arxiv_id}.py`.** Gracelyn's workflow writes
  there; Ben's board reads the directory listing for status.

**Nobody blocks on live data.** Fake the interface, integrate at 15:00.

---

## 7. The four required shots

Video is 3–5 minutes. Required: terminal scraping workflow, Port dashboard, live
SigNoz monitoring, Bright Data auto-repair.

**If it doesn't appear in a shot, it's out of scope.** Cut rule for the whole day.

**Known gap:** the auto-repair requirement fits our design worst — our break is in
the pipeline, not the scraper. Mitigation: Ben runs one `brightdata scraper heal`
cycle as a separate short shot. **Budget 15 minutes, no more.** Heal takes 5–25
minutes to complete, so kick it off early and cut to the finished result.

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

- **Does a reproduction get committed as a real GitHub PR, or written to
  `reproductions/` and surfaced in Port?** PR is more impressive, costs ~30 min and
  a token. **Gracelyn's call — it changes what Workflow A builds.**
- Scoring: heuristic vs. LLM call. Start heuristic.
