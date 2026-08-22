# Handoff: Research Factory

## Overview
Research Factory is a standalone operations console for an autonomous paper-reproduction
pipeline: it scrapes new AI research (arXiv + frontier-lab blogs), scores each paper's claims
for reproducibility, has an agent write runnable Python for the promising ones, executes that
code in a sandbox, and only interrupts a human once a program has run cleanly. The console is
built to be filmed/projected for engineers: dark by default, high contrast, no thin weights.

This bundle is **only** the Research Factory app. It shares nothing with any other product
surface and should stay visually and structurally independent.

## About the design files
Everything in `paper-factory/` is a **design reference built in HTML** — a working prototype
(React 18 UMD + in-browser Babel, no build step) that shows intended look and behavior. It is
not production code to ship as-is. The task is to **recreate this design in the target
codebase's environment** (its React/Vite/Next/etc. setup and conventions), or, if the frontend
is greenfield, pick the stack that fits the backend team and implement the same screens there.
Opening `paper-factory/index.html` in a browser runs the whole prototype on bundled mock data —
use it as the living spec while implementing.

Two documents in the bundle are **not** design references and carry over directly:
- `paper-factory/API.md` — the REST contract the frontend expects (4 endpoints, exact shapes,
  optional-field/degradation rules, status vocabulary). Build the backend to this.
- `paper-factory/INTEGRATION.md` — a hook-point map: which file/function feeds each surface,
  what is mock vs. real, polling cadence, the mock fallback layer, security expectations, and a
  deploy checklist. Follow it when wiring the real API.

## Fidelity
**High-fidelity.** Colors, type, spacing, status treatments, and copy are final. Recreate
pixel-perfectly; where the target codebase has an existing component library, match these
visuals with it rather than importing this CSS wholesale. Desktop only (min width 1180px, no
responsive breakpoints — intentional and in-scope).

## Screens / Views

### 1. Factory (home, default route)
- **Top bar** (72px, sticky): logo tile (44px rounded square, inline-SVG mark: cyan ring over
  three stepped bars) · tabs `factory` / `settings` (active = 2px cyan underline inset) ·
  right: "N repros ready" pill (ink/paper square + tracked mono), live dot ("live · 4s", cyan
  pulse; amber "snapshot" only when a configured API fails), `light mode`/`dark mode` toggle,
  `sign in`, solid **join the waitlist** CTA.
- **Hero**: cyan mono eyebrow "PAPERS IN. WORKING CODE OUT." → lockup (62px mark + 68px
  Libre Franklin 600 title "Research Factory", -0.035em) → one full-width paragraph (20px/1.62)
  → CTA row (solid button + mono note).
- **HOW IT WORKS** panel: header strip, then 4 columns over one continuous rail (1px line,
  13px circle nodes at column centers, four 6px cyan blocks travelling left→right on an 11s
  loop): `scrape` / `score` / `reproduce` / `monitoring & review`, each with one prose line.
  Active steps get a pulsing marker (cyan = generating, ink/paper = review waiting) and a
  ring-glow node.
- **SELF HEALING LOOPS**: two side-by-side box-flow diagrams.
  - Loop 1 "the scraper broke": Scrape fails (gray/state) → SigNoz (detects, alerts) → Port
    (heals, no gate) → Bright Data (gets a new scraper); "human notified" box hangs from Port;
    solid return arc under everything labeled "re-run, traced clean".
  - Loop 2 "the generated code broke": Paper flagged → Port agent (writes code) → GitHub
    Actions (runs it) → Port (human approves); dashed retry arc between agent and Actions
    labeled "on failure, retry with the traceback, max 2"; legend note "the gate is here, not
    in loop 1".
  - Tool identity = colored monogram tiles + tinted boxes (see tokens). Real product logos are
    trademarked and were deliberately not reproduced — keep the monogram/color system unless
    the team has licensed assets.
- **STATUS** band ("updated every 4 seconds"): four figures (42px Martian Mono) — papers
  ingested / reproductions attempted / pass rate (per-attempt) / live repros (= repro-ready +
  approved; sub-line "N waiting on a human decision"; number goes paper-white when hot).
- **Search + filters**: `/`-prefixed keyword field (title substring, all terms must match,
  clear button) · reproducible-only toggle · status chips with live counts (all states /
  generating / repro / queued / approved / rejected / ingested) · result line
  "N of 222 papers matching "q" · sorted by pipeline activity" (sort toggles to newest-first).
- **Table** (grid 1fr 216px 116px 208px; 3px status rail on the row's left edge): paper cell =
  17.5px title + sub-row (source badge, id linking to `source_url`, up to 2 subject tags,
  age) · authors (2 then "et al.") · score bar (74px, threshold tick at 0.70, cyan fill +
  "REP" flag when reproducible) · status chip. Row hover lifts one step; click opens detail.

### 2. Paper detail ("repro page", no reload)
"← pipeline" back link · title (33px) · meta row (source badge, id link, subjects, all
authors, age) · right column: status chip + score bar.
- `awaiting_review` → **review bar**: ink-left-rail panel, "The code ran. A human decides
  whether it reproduces the paper.", attempt/exit summary line, big solid **approve** +
  outlined **reject** (optimistic update, reconciled with the API).
- decided → quiet "approved/rejected by a human…" line; optional reviewer-note block.
- **THE REPRO** panel: left "what was reproduced" prose + GitHub repo link (GH monogram tile +
  `github.com/research-factory/repro-<id>`); right rows: paper claims / factory measured /
  verdict chip (reproduced = green, not reproduced = red).
- **Side-by-side frame** (the product's key shot): `ABSTRACT · HUMAN` pane (18.5px/1.66 prose)
  | `GENERATED IMPLEMENTATION · AGENT` pane (syntax-highlighted Python, line numbers, 560px
  equal heights, independent scroll). Generating papers show a blinking caret "writing…".
- **RUN OUTPUT**: terminal block (always-dark), header with exit state + line count, colorized
  lines ($ prompt cyan, tracebacks red, warnings amber, `REPRODUCED: True`/exit 0 green).
- **ATTEMPT HISTORY**: every attempt expanded by default — failed attempts are the point, never
  collapse them. Card: green/red left rail, "attempt N · passed/failed" header with duration +
  the extracted error line, body = code (left) | stdout/stderr terminal (right).

### 3. Waitlist
Narrow page (max 1080px): H1, one-line pitch, form — email + team · areas of interest (subject
chips) · title keywords (add/remove tags) · sources checklist · reproducibility bar slider
(0.50–0.95) · retry cap slider (0–4) · integrations checklist (webhook / REST / PR / Slack /
weekly email) · submit → recap screen echoing every choice. Labeled as prototype (not sent).

### 4. Sign-in
Email + password, solid sign-in (mock: flips to signed-in and routes to settings), link to
waitlist. Labeled as prototype.

### 5. Settings
Same config fields as waitlist under "intake and policy", plus API-key row (mono + copy),
webhook URL, account row, save button with transient "saved". Labeled as in-memory only.

## Interactions & behavior
- **Polling, not websockets**: summary + list every 4s; open detail re-polled on the same tick.
  Counts that change get a 0.55s pop animation (keyed remount).
- **Graceful degradation everywhere**: unreachable API / missing fields → render what exists,
  fall back to the bundled snapshot, one quiet amber inline notice + "snapshot" chip. A blank
  screen is never acceptable (this gets demoed live).
- **Status system = four visual families, not six colors**: inert (`ingested` — bare dim text,
  no container) · in-flight (`queued` outlined cyan; `generating` charged cyan + pulsing dot +
  sweeping underline) · needs-human (`awaiting_review`, labeled **"repro"** — the ONLY solid
  paper-white block in dark mode, inverts to solid ink in light mode) · terminal (`approved`
  dim green / `rejected` dim red, no motion). Row rails repeat the family color.
- **Theme toggle**: `data-pf-theme` on `<html>`, persisted (`localStorage["pf-theme"]`),
  applied pre-paint. Code + terminal blocks stay dark in BOTH themes.
- Motion is quiet and loop-based only where it signals liveness (belt dots, generating sweep,
  live dot); all disabled under `prefers-reduced-motion`.
- Client-side only: search, filters, sorting, routing (list ↔ detail ↔ account screens).

## State management
One root component holds: `list`, `summary`, `mode` (live/fallback), `notice`, `view`
({name, id}), `detail` (+ per-detail notice/loading), `busy` (review in flight), `signedIn`,
`theme`. Review decisions apply optimistically to both list and detail, then reconcile with the
POST response. See `INTEGRATION.md` §2–5 for the endpoint→surface map and the mock layer's
boundaries (`pf-data.js` simulates pipeline motion only when no API answers).

## Design tokens
**Type**: Libre Franklin (prose/UI); Martian Mono ("machine voice": labels, figures, chips,
eyebrows — tracked uppercase at 10–13px, 42px stat figures); IBM Plex Mono (code, terminal,
ids, form values). Google Fonts, weights 400–700 only.

**Dark (default)**: canvas `#0C1013` · top bar `#0A0E11` · panel `#0E1418` · panel header
`#0F1418` · field `#0F1519` · surface `#11171B`/`#161E23` · hairlines `#1F282E`/`#2C383F` ·
text `#E9EFF2` / `#A7B6BE` / `#72838D` (+ gray ramp `#DCE6EA→#3A464E`) · accent cyan `#46D9E8`
(hover `#A6EEF6`) · needs-human paper `#F2F7F9` on ink `#0A0E11` · ok `#3EDB92`/text `#74E5B4`
· error `#FF6B5E`/text `#FF9C90` · warn amber `#C9A227`.

**Light**: canvas `#F2F5F6` · panels `#FFFFFF` · lines `#DDE4E7`/`#C4CFD4` · text `#141F27` /
`#3C5058` / `#5C707C` · cyan → `#0A87A0` · needs-human → solid ink `#12202B` on white · ok
`#178A57` · error `#C43D2E`. Full override table lives at the bottom of `pf.css`
(`html[data-pf-theme="light"]`).

**Always-dark zones** (both themes): terminal `#06090B`, code `#090D10`, syntax palette
`tk-*` classes in `pf.css` (keywords `#6FC8FF`, defs `#FFD479`, calls `#9AE6C8`, strings
`#F2A76B`, docstrings `#7E9AA6`, comments `#5F7580`, numbers `#E4A0F0`, constants `#C9E48A`).

**Tool identity**: Port indigo `#6366F1` (light text `#B9B8FF` / dark-theme; `#4A4DBF` on
light) · SigNoz red-orange `#F25733` · Bright Data blue `#3E7BFA` · GitHub mono (`#21262D`
tile, `#8B949E` border) · state gray `#3A464E`. Tiles are 17–19px rounded squares with white
monogram letters (P / S / B / GH).

**Geometry**: radii 2px (chips/buttons/panels) and 6px (loop boxes) only; 3px left rails for
emphasis; 1px hairline borders do the lifting (no shadows anywhere); spacing on a loose 4px
base; content max 1720px with 40px gutters; min viewport 1180px.

## Assets
None external. The brand mark is a tiny inline SVG (`PFMark` in `pf-hero.jsx`): cyan circle
outline + three stepped bars (bars use `--pf-mark-bars` so they invert per theme). Fonts load
from Google Fonts. Tool "logos" are generic colored monogram tiles by design (trademark-safe).

## Security requirements (carry these over)
Paper titles/abstracts/authors are untrusted scraped input. The prototype never touches
`innerHTML`: the Python highlighter (`pf-hl.js`) emits tokens rendered as text nodes, and ids
are `encodeURIComponent`-ed into URLs/paths. Preserve these properties in the real
implementation.

## Files
```
paper-factory/
  index.html      entry — open in a browser to run the prototype on mock data
  pf.css          all styling: tokens (dark + light), status families, every component
  pf-app.jsx      root: top bar, routing, 4s polling, optimistic review, theme state
  pf-hero.jsx     mark (PFMark), hero, HOW IT WORKS rail, SELF HEALING LOOPS diagrams
  pf-list.jsx     stats band, search/filters, pipeline table
  pf-detail.jsx   repro summary, abstract|code frame, run output, attempt history, review bar
  pf-account.jsx  waitlist, sign-in, settings (mocked surfaces)
  pf-ui.jsx       shared atoms: status chips, score bar, code block, terminal, section heads
  pf-hl.js        Python tokenizer for syntax highlighting (token output, no HTML)
  pf-api.js       API client: base config, ?api= override, timeouts, normalization, fallback
  pf-data.js      bundled snapshot (222 papers) + mock pipeline motion — demo/fallback only
  API.md          REST contract for the backend (build to this)
  INTEGRATION.md  wiring guide: hook points, mock boundaries, deploy checklist
```
