/* Paper Factory — API client.
   Every call tries the live REST API and falls back to the last known
   local snapshot. A failure never blanks a screen; it sets a notice. */
(function () {
  var TIMEOUT = 2500;
  var state = { source: "unknown", notice: null, lastOk: null };

  function str(v, d) { return typeof v === "string" ? v : (v == null ? (d || "") : String(v)); }
  function num(v, d) { var n = typeof v === "number" ? v : parseFloat(v); return isFinite(n) ? n : (d === undefined ? 0 : d); }
  function arr(v) { return Array.isArray(v) ? v : []; }

  var STATUSES = ["ingested", "queued", "generating", "awaiting_review", "approved", "rejected"];

  function normPaper(p) {
    p = p && typeof p === "object" ? p : {};
    var s = str(p.status, "ingested");
    return {
      arxiv_id: str(p.arxiv_id, "unknown"),
      title: str(p.title, "Untitled"),
      authors: arr(p.authors).map(function (a) { return str(a); }),
      abstract: str(p.abstract, ""),
      subjects: arr(p.subjects).map(function (a) { return str(a); }),
      score: Math.max(0, Math.min(1, num(p.score, 0))),
      reproducible: !!p.reproducible,
      scraped_at: str(p.scraped_at, ""),
      source: str(p.source, "arXiv"),
      source_url: str(p.source_url, ""),
      repro_summary: str(p.repro_summary, ""),
      evidence_url: str(p.evidence_url, ""),
      repro_result: p.repro_result && typeof p.repro_result === "object"
        ? { claimed: str(p.repro_result.claimed, ""), measured: str(p.repro_result.measured, ""), reproduced: !!p.repro_result.reproduced }
        : null,
      status: STATUSES.indexOf(s) === -1 ? "ingested" : s,
      retry_count: num(p.retry_count, 0),
      generated_code: str(p.generated_code, ""),
      run_output: str(p.run_output, ""),
      review_note: str(p.review_note, ""),
      attempts: arr(p.attempts).map(function (a, i) {
        a = a && typeof a === "object" ? a : {};
        return { index: num(a.index, i + 1), status: str(a.status, "failed"), code: str(a.code, ""), output: str(a.output, ""), duration_s: num(a.duration_s, 0), finished_at: str(a.finished_at, "") };
      })
    };
  }

  function normSummary(s) {
    s = s && typeof s === "object" ? s : {};
    return { papers_ingested: num(s.papers_ingested, null), reproductions_attempted: num(s.reproductions_attempted, null), pass_rate: num(s.pass_rate, null), awaiting_review: num(s.awaiting_review, null) };
  }

  function req(path, opts) {
    var ctrl = new AbortController();
    var t = setTimeout(function () { ctrl.abort(); }, TIMEOUT);
    return fetch(PFApi.base + path, Object.assign({ signal: ctrl.signal, headers: { "content-type": "application/json" } }, opts || {}))
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .finally(function () { clearTimeout(t); });
  }

  function withFallback(path, opts, fallback, label) {
    if (!PFApi.base) return Promise.resolve({ data: fallback(), source: "local", notice: null });
    return req(path, opts).then(function (j) {
      state.source = "live"; state.notice = null;
      return { data: j, source: "live", notice: null };
    }).catch(function (e) {
      state.source = "fallback";
      state.notice = "API unreachable (" + (e && e.message ? e.message : "error") + ") — showing the last known snapshot" + (label ? " for " + label : "") + ".";
      return { data: fallback(), source: "fallback", notice: state.notice };
    });
  }

  window.PFApi = {
    /* REST root. Empty by default: the console runs on its bundled
       snapshot with no network calls and no degraded banner. Point it at
       a real backend with ?api=/api (or set this to "/api" in source) —
       every call then falls back to the snapshot if the API is down. */
    base: (function () {
      var m = /[?&]api=([^&]*)/.exec(location.search);
      return m ? decodeURIComponent(m[1]) : "";
    })(),
    state: state,

    summary: function () {
      return withFallback("/summary", null, function () { PFData.advance(); return PFData.summary(); }, "counts")
        .then(function (r) { r.data = normSummary(r.data && r.data.summary ? r.data.summary : r.data); return r; });
    },

    papers: function () {
      return withFallback("/papers", null, function () { return { papers: PFData.list() }; }, "the paper list")
        .then(function (r) {
          var raw = r.data;
          var list = Array.isArray(raw) ? raw : arr(raw && raw.papers);
          r.data = list.map(normPaper);
          return r;
        });
    },

    paper: function (id) {
      return withFallback("/papers/" + encodeURIComponent(id), null, function () { return PFData.detail(id); }, "this paper")
        .then(function (r) {
          var raw = r.data && r.data.paper ? r.data.paper : r.data;
          r.data = raw ? normPaper(raw) : null;
          return r;
        });
    },

    review: function (id, decision) {
      return withFallback("/papers/" + encodeURIComponent(id) + "/review", { method: "POST", body: JSON.stringify({ decision: decision }) },
        function () { return PFData.review(id, decision); }, "the review")
        .then(function (r) {
          var raw = r.data && r.data.paper ? r.data.paper : r.data;
          r.data = raw ? normPaper(raw) : null;
          return r;
        });
    }
  };
})();
