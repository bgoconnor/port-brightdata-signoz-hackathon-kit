# SPEC — Paper Factory

Team spec. Read this first. ~5 min.

---

## 1. What we're building

**A factory that reads new AI papers and manufactures runnable code from the good ones.**

Scrape arXiv cs.AI new submissions. Score each paper for whether it has a
reproducible core claim. High-scoring papers trigger a Port workflow where a
coding agent writes a minimal executable illustration of the paper's central
mechanism. The code must actually run before a human is asked to approve it.

Second loop: we manufacture a bug in the scoring pipeline. SigNoz catches it,
Port routes it to an agent that diagnoses from the trace alone and patches it,
human approves.

**The app is a paper board. The submission is the factory.**

---

## 2. Why this wins

The judges (Anthropic engineers) published their criteria. The two hardest to
satisfy are *"how it tests and verifies what it produces"* and *"how it handles
failures, retries, and changing requirements."*

- **Loop A is verification** — generated code is executed before a human sees it.
  Failed runs get rejected and re-prompted.
- **Loop B is failure handling** — a real bug, diagnosed from telemetry, patched
  under human approval.

Also: *"whether it can run again, rather than producing one carefully rehearsed
result."* Both loops re-run on demand.

Every sponsor tool is load-bearing. Remove one and the loop breaks:

- **Bright Data** — the raw material. No papers, no factory.
- **SigNoz** — the only thing that notices the break. Bright Data doesn't detect
  breakage; their docs say the operator is the detector.
- **Port** — the context lake, the orchestration, and the human gate on an agent
  writing code.

---

## 3. Architecture

### Loop A — Paper to reproduction (headline)

```
Bright Data scrapes arXiv cs.AI /new
  -> normalize -> SQLite -> paper board (static HTML)
  -> scoring step flags papers with a reproducible core claim
  -> upsert Paper entity in Port
  -> Port workflow triggers:
       agent reads abstract
       -> writes ONE self-contained Python file
       -> WORKFLOW EXECUTES IT
            fails  -> reject, re-prompt with traceback (max 2 retries)
            passes -> Review step, human approves
  -> committed to reproductions/
  -> whole run traced in SigNoz
```

### Loop B — Manufactured break (second act)

```
make break   (applies a real bug to the scoring pipeline)
  -> pipeline runs, partial failure
  -> SigNoz: 40 rows in, 12 rows out, span event scraper.processing_failed
  -> alert fires -> Port workflow
       agent gets THE TRACE AND THE REPO ONLY — not the diff
       -> diagnoses, patches, adds regression test
       -> Review step, human approves
  -> re-run, traced clean
```

---

## 4. Hard definitions

These exist to stop scope from exploding. Do not renegotiate them during the build.

### "Reproduction" means:

- **One file.** Self-contained Python.
- **Under 100 lines.**
- **Toy data only.** Synthetic, generated in the file. No downloads, no datasets.
- **Runs in under 10 seconds.**
- **Prints one number, or writes one plot.**

It is **not** a replication of the paper's results. It is a *minimal executable
illustration of the central mechanism*. We say exactly this on camera. Framed
honestly, nobody calls it overreach.

### "The break" means:

Unhandled null in the normalize step — one scraped field comes back empty and the
transform does arithmetic on it. Throws mid-batch: some records written, some not.
Partial success is the realistic failure mode and it reads beautifully in a trace.

**The agent must not be told what the break is.** It gets the SigNoz trace and the
repo. That is the claim we make on camera and it's the difference between a factory
and a magic trick.

Therefore: **the break patch is not committed.** Untracked file or generated at
demo time. A sharp judge will look for the answer sitting in the repo.

---

## 5. Scope and timing

Real build window is **11:00–16:00**. 16:00 is a hard freeze; the last hour is video.

### T0 — Spine. Done by 13:00.

- [ ] One Bright Data collector against arXiv cs.AI /new
- [ ] Scrape → normalize → SQLite (one table, no ORM, no migrations)
- [ ] Static HTML paper board. No build step, no framework.
- [ ] OTel wired, one trace verified landing in SigNoz
- [ ] Scoring step (can be a heuristic or a single LLM call — either is fine)

**If T0 is not done by 13:00, stop adding features and start filming.**

### T1 — Loop A. Done by 15:00.

- [ ] Port blueprint: `Paper` (title, authors, arxiv_id, score, status)
- [ ] Port blueprint: `Reproduction` (paper ref, status, run result, file path)
- [ ] Port workflow: flagged paper → agent → **execute the output** → Review step
- [ ] Rejection path works and is demonstrable
- [ ] Port dashboard: papers ingested, reproductions attempted, pass rate
- [ ] `CLAUDE.md` with collector ID and scraper rules, committed

### T2 — Loop B. Optional.

- [ ] `make break` / pipeline validation / named span event / SigNoz alert rule
- [ ] Port workflow: alert → agent diagnoses from trace → patch → Review

**Cut Loop B before cutting Loop A.** Two half-loops lose to one loop that visibly
runs twice.

### 16:00 — Freeze. Video only.

---

## 6. The four required shots

Submission requires a 3–5 minute video showing: terminal scraping workflow, Port
dashboard, live SigNoz monitoring, Bright Data auto-repair.

**If it doesn't appear in a shot, it's out of scope.** This is the cut rule for the
whole day.

Note: the auto-repair requirement is the weakest fit for our design — our break is
in the pipeline, not the scraper. Mitigation: run one `brightdata scraper heal`
cycle on the collector as a separate short shot, and let the pipeline loop carry
the narrative weight. Budget 15 min for this; don't let it derail Loop A.

---

## 7. Roles

- **Pipeline** — scrape, normalize, SQLite, board
- **Observability** — OTel spans, SigNoz dashboard, alert rule
- **Port** — blueprints, workflow, Review step, dashboard
- **Demo owner** — writes the script at 11:00, owns the video, **does not build
  features.** This role is not optional; it's who keeps us shippable.

---

## 8. Rules of engagement

- **Write the demo script before writing code.** Build only what appears on screen.
- Prefer boring solutions. Every dependency is a risk at 15:00.
- Commit as you go, clear messages. Commit history is part of the submission.
- Never fake a passing result. If it can't be verified, say so.
- No new features after 15:00. None.

---

## 9. Known constraints

- **Bright Data `scraper create` takes 5–25 minutes**, cap of 3 concurrent. Kick
  off generation during the 10:00 workshop so it finishes while the SigNoz and
  Port talks run.
- Scrapers run on Bright Data's cloud — **any target must be a public URL.**
- **Port ships an official Claude Code plugin** (one-command install, MCP + Skills).
  Install it first. Biggest available shortcut.
- SigNoz is scored on whether a judge could diagnose a failure **from the dashboards
  alone.** Row counts per stage as span attributes are what make that true.

---

## 10. Open decisions

- **Does a reproduction get committed as a real GitHub PR, or written to
  `reproductions/` and surfaced in Port?** PR is more impressive, costs ~30 min and
  a token. **Decide by 11:15.**
- Scoring step: heuristic vs. LLM call. Heuristic is faster and less fragile.
- Stack: leaning Python + SQLite + static HTML, no build step.
