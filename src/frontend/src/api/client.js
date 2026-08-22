/* Research Factory - API client.
 *
 * Every call tries the live REST API and falls back to the bundled snapshot.
 * A failure must never blank a screen: it renders the last known data and
 * raises one quiet notice. See design_handoff_research_factory/paper-factory/
 * API.md and INTEGRATION.md section 9 (kill-switch test).
 */

import snapshot from "../data/snapshot.js";

const TIMEOUT_MS = 2500;

const STATUSES = [
  "ingested",
  "queued",
  "generating",
  "awaiting_review",
  "approved",
  "rejected",
];

/** REST root. `?api=<root>` overrides per load; `?api=` (empty) forces the
 *  snapshot with no network calls and no degraded notice. */
export const apiBase = (() => {
  const match = /[?&]api=([^&]*)/.exec(window.location.search);
  return match ? decodeURIComponent(match[1]) : "/api";
})();

const asString = (value, fallback = "") =>
  typeof value === "string" ? value : value == null ? fallback : String(value);

const asNumber = (value, fallback = 0) => {
  const n = typeof value === "number" ? value : parseFloat(value);
  return Number.isFinite(n) ? n : fallback;
};

const asArray = (value) => (Array.isArray(value) ? value : []);

/** Coerce a partial payload into a complete paper so a missing field renders
 *  rather than throwing. Unknown status values fall back to `ingested`. */
export function normalizePaper(raw) {
  const p = raw && typeof raw === "object" ? raw : {};
  const status = asString(p.status, "ingested");
  const result = p.repro_result;

  return {
    paper_id: asString(p.paper_id, asString(p.arxiv_id, "unknown")),
    arxiv_id: asString(p.arxiv_id, "unknown"),
    title: asString(p.title, "Untitled"),
    authors: asArray(p.authors).map((a) => asString(a)),
    abstract: asString(p.abstract),
    subjects: asArray(p.subjects).map((s) => asString(s)),
    score: Math.max(0, Math.min(1, asNumber(p.score, 0))),
    reproducible: Boolean(p.reproducible),
    scraped_at: asString(p.scraped_at),
    source: asString(p.source, "arXiv"),
    source_url: asString(p.source_url),
    status: STATUSES.includes(status) ? status : "ingested",
    retry_count: asNumber(p.retry_count, 0),
    generated_code: asString(p.generated_code),
    run_output: asString(p.run_output),
    review_note: asString(p.review_note),
    repro_summary: asString(p.repro_summary),
    evidence_url: asString(p.evidence_url, asString(p.repo_url)),
    repro_result:
      result && typeof result === "object"
        ? {
            claimed: asString(result.claimed),
            measured: asString(result.measured),
            reproduced: Boolean(result.reproduced),
          }
        : null,
    attempts: asArray(p.attempts).map((a, i) => {
      const attempt = a && typeof a === "object" ? a : {};
      return {
        index: asNumber(attempt.index, i + 1),
        status: asString(attempt.status, "failed"),
        code: asString(attempt.code),
        output: asString(attempt.output),
        duration_s: asNumber(attempt.duration_s, 0),
        finished_at: asString(attempt.finished_at),
      };
    }),
  };
}

/** Header figures. Any field may be absent; null lets the UI show a dash. */
export function normalizeSummary(raw) {
  const s = raw && typeof raw === "object" ? raw : {};
  return {
    papers_ingested: asNumber(s.papers_ingested, null),
    reproductions_attempted: asNumber(s.reproductions_attempted, null),
    pass_rate: asNumber(s.pass_rate, null),
    awaiting_review: asNumber(s.awaiting_review, null),
  };
}

async function request(path, options) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(apiBase + path, {
      signal: controller.signal,
      headers: { "content-type": "application/json" },
      ...options,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

/** Try live, fall back to the snapshot. Resolves to {data, source, notice};
 *  it never rejects, so callers cannot blank the screen on an error path. */
async function withFallback(path, options, fallback, label) {
  if (!apiBase) {
    return { data: fallback(), source: "local", notice: null };
  }
  try {
    const data = await request(path, options);
    return { data, source: "live", notice: null };
  } catch (error) {
    const reason = error?.message || "error";
    return {
      data: fallback(),
      source: "fallback",
      notice:
        `API unreachable (${reason}) — showing the last known snapshot` +
        (label ? ` for ${label}.` : "."),
    };
  }
}

const unwrap = (payload, key) =>
  payload && typeof payload === "object" && payload[key] ? payload[key] : payload;

export async function fetchSummary() {
  const result = await withFallback(
    "/summary/",
    null,
    () => {
      snapshot.advance();
      return snapshot.summary();
    },
    "counts",
  );
  return { ...result, data: normalizeSummary(unwrap(result.data, "summary")) };
}

export async function fetchPapers() {
  const result = await withFallback(
    "/papers/",
    null,
    () => ({ papers: snapshot.list() }),
    "the paper list",
  );
  const raw = result.data;
  const list = Array.isArray(raw) ? raw : asArray(raw?.papers);
  return { ...result, data: list.map(normalizePaper) };
}

export async function fetchPaper(id) {
  const result = await withFallback(
    `/papers/${encodeURIComponent(id)}/`,
    null,
    () => snapshot.detail(id),
    "this paper",
  );
  const raw = unwrap(result.data, "paper");
  return { ...result, data: raw ? normalizePaper(raw) : null };
}

export async function submitReview(id, decision) {
  const result = await withFallback(
    `/papers/${encodeURIComponent(id)}/review/`,
    { method: "POST", body: JSON.stringify({ decision }) },
    () => snapshot.review(id, decision),
    "the review",
  );
  const raw = unwrap(result.data, "paper");
  return { ...result, data: raw ? normalizePaper(raw) : null };
}
