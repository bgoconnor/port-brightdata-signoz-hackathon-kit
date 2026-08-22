# Hackathon context

Reference doc for this repo. Written before kickoff. Contains the event constraints,
the sponsor tool realities we researched, the architecture we're building toward,
and the decisions still open.

---

## 1. The event

In-person, San Francisco. Judged by engineers from Anthropic.
Sponsors: **Port**, **Bright Data Scraper Studio**, **SigNoz**.

### Schedule

| Time | What |
|---|---|
| 09:00–09:45 | Check-in |
| 09:45–10:00 | Kickoff |
| 10:00–10:20 | Bright Data workshop |
| 10:20–10:40 | SigNoz workshop |
| 10:40–11:00 | Port workshop |
| 11:00–14:00 | Hacking |
| 14:00 | Pizza |
| 14:00–17:00 | Hacking |
| 17:00 | Submission opens |
| 18:00–19:00 | Judging + networking |
| 19:00 | Winners |

**Real build window is 11:00–16:00.** The last hour before submission is the demo
video. Treat 16:00 as a hard feature freeze.

**The workshops are not dead time.** Bright Data scraper generation takes 15–25
minutes per collector. Kick off generation during the Bright Data workshop so
collectors are building while the SigNoz and Port talks run.

### Submission requirements

- GitHub repo with code, commit history, and a README explaining what was built.
  Perfect code explicitly not required.
- **Demo video, 3–5 minutes**, showing four things:
  1. The terminal scraping workflow
  2. The Port dashboard setup
  3. Live SigNoz monitoring
  4. Bright Data auto-repair working

Those four shots are the scoring function. **If it doesn't appear in a shot, it's
out of scope.** That is the cut rule for the entire day.

### Prizes

- **Grand prize** (NVIDIA DGX Spark, $5k): best full-stack integration of all three
  tools in one pipeline. Using all three maximizes odds.
- **Track prizes** (Keychron keyboards, per team member):
  - Best Port integration — clearest workspace showing goals, technical choices,
    risk factors, cataloged services
  - Best Bright Data integration — pure terminal workflow, proper scraper rules
    config, clean JSON, working auto-repair
  - Best SigNoz integration — active tracing, logs, metrics across endpoints and
    background jobs

### What the judges said they're looking for

The framing: *"Can you build the factory that builds the app?"* The app is the test
run; the factory is the submission. Explicitly stated criteria:

- How faithfully the factory understands the brief and its constraints
- How it coordinates agents, tools, and human decisions
- How it tests and verifies what it produces
- How it handles failures, retries, changing requirements
- How clearly operators can see what happened and why
- **Whether it can run again, rather than producing one carefully rehearsed result**

Called out as *not* a factory: a single giant prompt; a fixed CI pipeline with an
LLM bolted on.

Rules: teams of 1–4, in-person SF, everything submitted by end of day.

---

## 2. Sponsor tool realities

Researched before kickoff. These are the facts that change the plan.

### Bright Data Scraper Studio

Terminal-first. `npx -p @brightdata/cli`. OAuth once. Each scraper has a stable
Collector ID (`c_*`) that survives runs and self-healing.

Core flow: **run → inspect → heal → approve → re-run**

```bash
brightdata scraper create <url> "<natural language description>"   # returns collector_id
brightdata scraper run <collector_id> <url> --pretty
brightdata scraper heal <collector_id>                             # stops at approval gate
brightdata scraper approve <collector_id>                          # commits the fix
```

**Critical constraints:**

- **Generation is slow.** `scraper create` typically takes 5–15 minutes, up to 25
  on complex targets. Heal runs the same refactor job. **You cannot break-and-fix
  live on camera.** Plan a time-cut in the video and say so out loud.
- **Concurrency cap of 3** generations per account. Exceeding it returns 429; the
  CLI backs off and retries (default 4 attempts).
- **Scrapers run on Bright Data's cloud infrastructure, not locally.** Any scrape
  target must be a **publicly reachable URL**. localhost fixtures will not work.
- **Bright Data does not detect breakage.** Their docs state it plainly: *you* are
  the detector — you inspect run output and decide. Healing is automatic;
  detection is not. **This gap is the whole opportunity** (see §3).
- A failed heal is non-destructive; the existing scraper keeps working.
- `--auto-approve` skips the human gate. Do not use it — the gate is the demo.
- Scraper config belongs in the project rules file (`CLAUDE.md`) so the coding
  agent reuses it automatically. This is explicitly scored.

Pricing: $1.50 / 1,000 page loads. 5,000 free credits/month. +$50 credits for
hackathon participants.

### Port

Agentic SDLC platform. Five building blocks: Context Lake, workflow orchestration,
AI agents, governance, interface layer.

- **Official Port plugin for Claude Code** — one-command install, gives MCP
  connection plus Port's own Skills. Install this first; it is the biggest
  available shortcut.
- **Port AI Builder** has Plan and Build modes. Plan analyzes and proposes a
  step-by-step plan; Build executes incrementally with steps traceable to the plan.
  It builds the *platform*, not the application.
- **Workflows** support agents as native steps, and **Review steps for
  human-in-the-loop** with dynamic approver lists. This is where our approval gate
  lives.
- Blueprints model entities; scorecards define standards; dashboards give the
  operator view.

### SigNoz

OpenTelemetry-native. Traces, metrics, logs. Cloud or self-hosted.

Scored on whether a judge could diagnose a failure **from the dashboards alone**.
Practical implications:

- One parent span per run (`scrape_run`), child span per target
- Span attributes: target, rows extracted, latency, collector ID, schema version
- **Failure and repair must be first-class named span events**, not log text:
  `scraper.extraction_failed`, `scraper.heal_started`, `scraper.heal_approved`
- Metrics: rows-per-run per target, repair event counter
- Observability must **feed back into the factory** — alerts, retries, escalation.
  A dashboard nobody acts on scores poorly.

---

## 3. The architecture

**One line: SigNoz is the detector. Port is the operator's console. Bright Data is
the mechanic.**

This works because it targets a real gap rather than re-demoing a sponsor feature.
Bright Data heals scrapers but never notices they're broken. Nothing watches the
runs. Nothing tells you a scraper went quietly empty at 2am. We build that.

```
scheduled scrape run
  -> OTel traces emitted to SigNoz
  -> validation on run output (zero rows / partial / schema mismatch)
  -> span event: scraper.extraction_failed
  -> SigNoz alert fires
  -> Port workflow triggered
       -> calls `brightdata scraper heal`
       -> Review step: human sees the diff, approves or rejects
  -> `brightdata scraper approve`
  -> re-run, traced clean, board back to fresh data
```

Why this scores: every sponsor tool is **causally required**. Remove any one and
the loop breaks. Cosmetic integration loses to causal integration.

### Making the break repeatable

Judges explicitly reward a system that "can run again" over a rehearsed result.

Mirror the target page to **GitHub Pages** (public URL — required, since Bright
Data runs in the cloud) as `v1.html`. Create `v2.html`: same content, structurally
different markup — different class names, table restructured into divs, values
nested deeper. It must genuinely defeat a selector written against v1.

Point the collector at the mirror. Flip versions on demand to trigger the break.
Real data for the live board, controlled mirror for the break demo. **Say this
out loud in the video** — frame it as rigor, not as hiding something.

---

## 4. Scope

### T0 — The Spine (done by 13:00)

- 2 collectors generated (not 5 — generation time makes more unaffordable)
- Scrape → normalized JSON → SQLite, one table
- Static HTML page, one table. No build step, no framework.
- OTel wired, one trace verified landing in SigNoz
- Mirror page live on GitHub Pages, v1/v2 flip working

**If T0 isn't done by 13:00, stop adding and start filming.** A working spine with
honest narration beats a broken factory.

### T1 — The Factory (done by 15:00)

This is the part actually being judged.

- Detection: validate run output, emit `scraper.extraction_failed`, SigNoz alert rule
- Port blueprint: `ScrapeRun` (status, rows, target, latency, collector ID),
  upserted every run
- Port workflow: alert-triggered → `scraper heal` → Review step with diff →
  approve → `scraper approve` → re-run
- Port dashboard: run history, repair count, last-healthy timestamp
- `CLAUDE.md` with collector IDs and scraper rules, committed

### T2 — Only if T1 is green at 15:00

Sparkline of history. Third target. Scraper-health scorecard. Slack notification on
the Review step.

### 16:00 — Freeze. Video only.

Because heal takes 5–25 minutes, trigger the break around 15:30 and film everything
else while it runs.

---

## 5. Open decisions

**Scrape target — not yet locked.** Criteria: no login, no pagination, one page,
flat 5–8 field schema, data that visibly changes, subject the room cares about.

Candidates:

| Target | Why | Risk |
|---|---|---|
| **arXiv cs.AI new submissions** | "What dropped in AI last night." Plain HTML, one page, daily refresh. Right audience. | Low |
| **Hacker News front page** | Literally Bright Data's documented example. Zero surprises. | Lowest, but generic |
| **AI lab careers pages** | "What each lab is building, inferred from hiring." Spicy. | Messier HTML |

**Stack** — leaning Python/FastAPI + SQLite + static HTML, no build step. Not final.

---

## 6. Operating principles

- **Write the demo script before writing code.** Build only what appears on screen.
- The app is deliberately boring. Spend the interest budget on *what* is scraped.
- Prefer boring working solutions. Every dependency is a risk at 15:00.
- One person owns the deploy and the demo and does not build features.
- Commit history is part of the submission — commit as you go, clear messages.
- Never fake a passing result. If it can't be verified, say so.
