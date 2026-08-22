# Paper Factory — API contract

The frontend polls a REST API every **4 s** (`PF_POLL_MS` in `pf-app.jsx`). No websockets.
Base path is `/api`, overridable per load with `?api=<root>`; `?api=` (empty) runs the UI
entirely on the bundled snapshot in `pf-data.js`.

All four calls **degrade gracefully**: a non-2xx, a timeout (2.5 s), or malformed JSON falls
back to the last known snapshot, renders the full screen, and shows one quiet inline notice.
Missing fields are coerced (`pf-api.js` → `normPaper`, `normSummary`), so a partial payload
renders rather than throwing. Unknown `status` values fall back to `ingested`.

---

## `GET /api/summary`

Header figures. Any field may be omitted; the UI shows `—` or derives it from the list.

```json
{
  "papers_ingested": 222,
  "reproductions_attempted": 4,
  "pass_rate": 0.57,
  "awaiting_review": 2
}
```

- `pass_rate` is a **0–1 fraction over attempts** (clean runs ÷ total attempts), not over papers.
- `reproductions_attempted` counts papers dispatched to the agent at least once.

## `GET /api/papers`

The whole table in one response — no pagination, no sort params. Filtering, keyword search
(substring match on `title`, all terms must match) and sorting are client-side.
`{"papers": [...]}` or a bare array both parse.

```json
{"papers": [{
  "arxiv_id": "2608.04417",
  "title": "Entropy-Gated Speculative Decoding for Autoregressive Language Models",
  "authors": ["M. Nakamura", "R. Okonkwo", "L. Bergström"],
  "abstract": "Speculative decoding accelerates…",
  "subjects": ["cs.CL", "cs.LG"],
  "score": 0.91,
  "reproducible": true,
  "scraped_at": "2026-08-22T04:41:00Z",
  "source": "arXiv",
  "source_url": "https://arxiv.org/abs/2608.04417",
  "status": "awaiting_review",
  "retry_count": 1
}]}
```

`source` is a short human label for where the scraper found the work — `"arXiv"` plus
frontier-lab research blogs and paper indexes (e.g. `"DeepMind blog"`, `"HF papers"`). It is
rendered as a badge on every row; defaults to `"arXiv"` if absent. `source_url` is the canonical
link; when it is empty the identifier renders as plain text instead of a link, so blog-sourced
entries do not need a fabricated arXiv URL. `arxiv_id` stays the primary key regardless of source.

`abstract` may be omitted here to keep the payload small — the detail call must return it.
`generated_code`, `run_output` and `attempts` are **not** expected in this response.

## `GET /api/papers/{arxiv_id}`

Everything above, plus:

```json
{
  "generated_code": "\"\"\"Entropy-gated…\"\"\"\nimport numpy as np\n…",
  "run_output": "$ python main.py\nbaseline acceptance rate : 0.621\n…\nexit status 0  ·  38.90s",
  "review_note": "optional free text shown after a decision",
  "repro_summary": "one short paragraph: what was actually reproduced, in plain words",
  "repo_url": "https://github.com/research-factory/repro-2608-04417",
  "repro_result": {"claimed": "acceptance 0.620 → 0.780 (+0.160)", "measured": "0.621 → 0.774 (+0.153)", "reproduced": true},
  "attempts": [
    {"index": 1, "status": "failed", "code": "…", "output": "Traceback (most recent call last):\n…",
     "duration_s": 4.31, "finished_at": "2026-08-22T05:02:00Z"},
    {"index": 2, "status": "passed", "code": "…", "output": "…", "duration_s": 38.9,
     "finished_at": "2026-08-22T05:09:00Z"}
  ]
}
```

- `repro_summary`, `repo_url`, `repro_result` feed the "the repro" panel shown for any paper with
  attempts or run output. All three are optional — the panel renders placeholders/hides the link
  when absent. `repro_result.reproduced` drives the reproduced / not-reproduced verdict chip.

- `attempts[].status` — `"passed" | "failed"`. Failed attempts are rendered in full, expanded,
  with their traceback. Do not omit them: they are the proof the verification loop is real.
- `attempts[].output` is raw stdout **or** stderr, exactly as captured. The UI colourises lines
  by pattern (`$ ` prompt, `Traceback`/`*Error`, `Warning`, `exit status 0`) and prints them
  verbatim — send the trailing `exit status N · <seconds>` line if you have it.
- `generated_code` is the current head; `attempts[].code` is that attempt's version.
- 404 is fine for an unknown id — the UI shows an inline "could not be loaded" state.

## `POST /api/papers/{arxiv_id}/review`

```json
→ {"decision": "approve"}        // or "reject"
← {"status": "approved", …}      // the updated paper, same shape as the detail call
```

The UI applies the decision optimistically, then reconciles with the response. On failure the
local state stands and an inline notice says the decision was not sent.

---

## Status vocabulary

`ingested` · `queued` · `generating` · `awaiting_review` · `approved` · `rejected`

Rendered as four visual families, not six colours: **inert** (`ingested`, no chip),
**in flight** (`queued`, `generating` — cyan, `generating` animated), **needs a human**
(`awaiting_review` — the only solid white block in the app), **terminal** (`approved`,
`rejected` — dim green / dim red, no motion).

Keep `awaiting_review` as the wire value: the UI renders its label as **"repro"** (an executed
paper waiting on a decision). The "live repros" figure = `awaiting_review` + `approved`.

`retry_count` renders as a `×2` / `×3` multiplier on the chip. Retry cap is 2 (3 attempts total).

## Security

Titles, abstracts, authors and subjects are untrusted scraped input. Nothing is ever passed to
`innerHTML`: the Python highlighter (`pf-hl.js`) returns **tokens**, and the renderer emits React
text nodes, so markup in scraped or generated content cannot execute. `arxiv_id` is
`encodeURIComponent`-ed into both the arXiv link and every API path.
