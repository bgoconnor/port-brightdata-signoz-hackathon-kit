# Research Factory — backend integration guide

Companion to `API.md` (the endpoint contract). This file maps every piece of frontend
functionality to the exact hook point in code, says what is mock, what is real, and what the
backend must supply to light each surface up. File paths are relative to `paper-factory/`.

## 0. Architecture in one paragraph

The app is a static React page (`index.html` + `pf-*.jsx`, Babel in-browser, no build step).
All data flows through one client, `window.PFApi` (`pf-api.js`). The root component
(`pf-app.jsx` → `PaperFactory`) polls `PFApi.summary()` + `PFApi.papers()` every 4 s
(`PF_POLL_MS`), plus `PFApi.paper(id)` when a detail view is open. Everything else — filtering,
search, sorting, status chips — is client-side over that data. There is no router state in the
URL and no websockets by design.

## 1. Turning the real backend on

- `pf-api.js` → `PFApi.base`. Currently `""` (snapshot mode: no network calls, mock data only),
  overridable per load with `?api=<root>`. **To integrate: set the default to your API root**
  (e.g. `"/api"`) and keep the `?api=` override for demos.
- Timeout per request is 2.5 s (`TIMEOUT`); each call carries an `AbortController`.
- CORS: the page does plain `fetch` with `content-type: application/json`. Same-origin
  deployment (serve the static folder from the backend) avoids CORS entirely and makes
  `base:"/api"` just work.

## 2. Endpoint-by-endpoint hookup

All response shapes, optional-field behaviour and the status vocabulary are in `API.md`.
Summary of what each one feeds:

| Endpoint | Feeds | Hook point |
|---|---|---|
| `GET /summary` | 4 stat figures ("status" band) | `PFApi.summary()` → `StatStrip` (`pf-list.jsx`) |
| `GET /papers` | table, filters, counts, workflow live-dots, top-bar pill | `PFApi.papers()` → `PipelineScreen`, `WorkflowViz`, `TopBar` |
| `GET /papers/{id}` | detail: header, repro panel, abstract/code frame, run output, attempts | `PFApi.paper(id)` → `DetailScreen` (`pf-detail.jsx`) |
| `POST /papers/{id}/review` | Approve / Reject buttons | `PFApi.review(id, decision)` → `decide()` in `pf-app.jsx` |

Notes per endpoint:

- **/summary** — send `pass_rate` as a 0–1 fraction over *attempts*, not papers. Any absent
  field renders as "—" or is derived from the list; don't 500 on partial data.
- **/papers** — one payload, all rows (222 is fine; tested there). No pagination/sort/search
  params: the UI does keyword search (title substring, AND over terms), status filter,
  reproducible-only toggle, and activity-vs-newest sorting client-side. Omit the heavy fields
  (`generated_code`, `run_output`, `attempts`) here; the client strips them anyway.
- **/papers/{id}** — the whole detail object. The "the repro" panel needs `repro_summary`,
  `repro_result{claimed,measured,reproduced}`, `repo_url`; the panel shows for any paper with
  attempts or run output and degrades field-by-field. `attempts[]` must include failed attempts
  with full tracebacks — the UI renders them expanded on purpose.
- **/review** — respond with the updated paper. The UI applies the decision optimistically,
  then reconciles with your response; on network failure it keeps local state and shows a
  notice. Idempotency: a repeat POST with the same decision should be a no-op 200.

## 3. Mock layer — what to delete or keep

`pf-data.js` (`window.PFData`) is the bundled snapshot and fake backend. It also *simulates*
pipeline motion: `PFData.advance()` (called only in the no-API/fallback path of
`PFApi.summary()`) promotes `queued → generating → awaiting_review` every ~36 s and synthesizes
code/output/repro fields (`CODE_CURV_DONE`, `generic()`).

- **Keep it** as the graceful-degradation snapshot (recommended: the demo never blanks), or
- **Shrink it** to a handful of rows if payload size bothers you — the fallback path only needs
  *something* renderable.
- Real state transitions must come from your backend; `advance()` never runs while the API
  answers. Nothing else references `PFData`.

## 4. Status + naming semantics (easy to get wrong)

- Wire values stay `ingested | queued | generating | awaiting_review | approved | rejected`.
  Unknown values render as `ingested`.
- The UI *label* for `awaiting_review` is **"repro"**; "live repros" = `awaiting_review` +
  `approved` counts. Don't rename the wire value.
- `retry_count` renders as ×2/×3 on the chip. Attempts are capped at 3 total (2 retries) —
  reflect the real cap in `attempts[]`, the UI prints "retry cap 2" from data length.
- `generating` is the animated state; while a paper is `generating`, send whatever partial
  `generated_code` exists ("" is fine — the pane shows a writing caret).

## 5. Polling & liveness

- Cadence: `PF_POLL_MS` (4000 ms) in `pf-app.jsx`. Endpoints must be cheap; add ETag/304 if you
  like, the client ignores caching headers but browsers honor them.
- The top-bar chip shows **live** (cyan) when requests succeed, **snapshot** (amber) after a
  failure, with one quiet inline notice — that path is intentional demo behaviour; don't remove.
- Count-change "pop" animations key off value changes between polls; no extra work needed.

## 6. Mocked surfaces that need real endpoints *only if you want them live*

These are front-end-complete and clearly labeled as prototypes; wire them or leave them:

- **Waitlist** (`pf-account.jsx` → `WaitlistScreen`): collects email/org + full config
  (subjects, keywords, sources, threshold 0.5–0.95, retry cap 0–4, integrations). Suggested:
  `POST /waitlist` with that object; hook in the form's `onSubmit` (currently `setSent(true)`).
- **Settings** (`SettingsScreen`): same config object + webhook URL + API key display.
  Suggested `GET/PUT /settings`. State lives in `useConfig()` — replace its initial value with
  a fetch, and the "save changes" button's `setSaved(true)` with the PUT.
- **Sign-in** (`SignInScreen`): pure mock, any input "signs in" (`onSignedIn()` flips a flag in
  `pf-app.jsx`). Out of scope per the brief; wire to your auth only if the demo needs it.
- **API key / webhook** in settings are display-only strings today.

## 7. Links the backend controls

- `source_url` — row identifier + detail header link. Absolute https URL or empty (empty
  renders plain text, no link). `arxiv_id` stays the primary key even for blog-sourced items.
- `repo_url` — the GitHub link on the repro panel. Point it at the real repo your pipeline
  opens (e.g. the PR/branch with `main.py`); shown with a GH monogram tile.

## 8. Security expectations (already handled, don't undo)

- Every scraped/generated string is rendered as React text nodes; the Python highlighter
  (`pf-hl.js`) emits tokens, never HTML. You do **not** need to sanitize server-side for this
  UI, but don't start returning HTML expecting it to render.
- `arxiv_id` is `encodeURIComponent`-ed into API paths and links — ids with `/` are safe.
- `run_output`/`attempts[].output` are printed verbatim (with pattern-based colorizing);
  include the `exit status N · <seconds>` trailer line if available — the terminal header
  parses failure state from `Traceback|exit status [1-9]`.

## 9. Deploy checklist

1. Serve `paper-factory/` statically from the backend origin.
2. Set `PFApi.base = "/api"` in `pf-api.js`.
3. Implement the four endpoints per `API.md`; verify with `?api=/api` first.
4. Kill switch check: stop the backend, reload — the page must render the snapshot with the
   amber "snapshot" chip and one inline notice. If it blanks, something changed in `pf-api.js`.
5. Optional: wire waitlist/settings (section 6), real `repo_url`s (section 7).
