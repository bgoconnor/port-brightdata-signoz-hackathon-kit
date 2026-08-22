/* Paper Factory — Screen 1: Pipeline */

function StatStrip({ summary, list }) {
  const n = v => (v === null || v === undefined || !isFinite(v) ? null : v);
  const ingested = n(summary && summary.papers_ingested) !== null ? summary.papers_ingested : (list ? list.length : null);
  const attempted = n(summary && summary.reproductions_attempted);
  const rate = n(summary && summary.pass_rate);
  const awaiting = n(summary && summary.awaiting_review) !== null ? summary.awaiting_review
    : (list ? list.filter(p => p.status === "awaiting_review").length : null);
  const live = list && list.length ? list.filter(p => p.status === "awaiting_review" || p.status === "approved").length : awaiting;
  const cell = (value, label, sub, hot) => (
    <div className="pf-stat" data-hot={hot ? "1" : "0"}>
      <b>{value === null ? "\u2014" : value}</b>
      <u className="pf-eyebrow">{label}</u>
      <s>{sub}</s>
    </div>
  );
  return (
    <div className="pf-stats">
      {cell(ingested, "papers ingested", "arXiv cs.*, frontier-lab blogs, paper indexes")}
      {cell(attempted, "reproductions attempted", "papers the agent has written code for")}
      {cell(rate === null ? null : <React.Fragment>{Math.round(rate * 100)}<em>%</em></React.Fragment>, "pass rate", "attempts whose code executed cleanly")}
      {cell(live, "live repros", awaiting ? awaiting + " waiting on a human decision" : "none waiting on a decision", awaiting > 0)}
    </div>
  );
}

function FilterBar({ counts, active, onStatus, repOnly, onRep, query, onQuery }) {
  const keys = ["all", "generating", "awaiting_review", "queued", "approved", "rejected", "ingested"];
  return (
    <React.Fragment>
      <div className="pf-searchrow">
        <div className="pf-search">
          <span>/</span>
          <input value={query} onChange={e => onQuery(e.target.value)} spellCheck="false"
            placeholder="keyword in title — e.g. decoding, adapter, retrieval" aria-label="search paper titles" />
          {query ? <button onClick={() => onQuery("")} aria-label="clear search">clear</button> : null}
        </div>
        <button className="pf-toggle" aria-pressed={repOnly} onClick={() => onRep(!repOnly)}>
          <i></i>reproducible only
        </button>
      </div>
      <div className="pf-filters">
        {keys.map(k => (
          <button className="pf-chip" key={k} aria-pressed={active === k} onClick={() => onStatus(k)}>
            {k === "all" ? "all states" : pfStatus(k).label}
            <em>{k === "all" ? counts.all : (counts[k] || 0)}</em>
          </button>
        ))}
      </div>
    </React.Fragment>
  );
}

function PaperRow({ p, onOpen }) {
  const fam = pfStatus(p.status).fam;
  return (
    <div className="pf-row" data-fam={fam} role="button" tabIndex={0}
      onClick={() => onOpen(p.arxiv_id)}
      onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onOpen(p.arxiv_id); } }}>
      <div>
        <div className="pf-ttl">{p.title}</div>
        <div className="pf-sub">
          <span className="pf-src">{p.source || "arXiv"}</span>
          {p.source_url
            ? <a href={p.source_url} target="_blank" rel="noreferrer noopener" onClick={e => e.stopPropagation()}>{p.arxiv_id}</a>
            : <span>{p.arxiv_id}</span>}
          <span className="pf-subj">{(p.subjects || []).slice(0, 2).map(s => <span key={s}>{s}</span>)}</span>
          <span>{pfAgo(p.scraped_at)}</span>
        </div>
      </div>
      <div className="pf-auth">{pfAuthors(p.authors)}</div>
      <ScoreBar score={p.score} reproducible={p.reproducible} />
      <div><StatusChip status={p.status} retry={p.retry_count} /></div>
    </div>
  );
}

function PipelineScreen({ list, summary, notice, onOpen, onWaitlist }) {
  const [status, setStatus] = React.useState("all");
  const [repOnly, setRepOnly] = React.useState(false);
  const [byActivity, setByActivity] = React.useState(true);
  const [query, setQuery] = React.useState("");

  const counts = React.useMemo(() => {
    const c = { all: list.length };
    list.forEach(p => { c[p.status] = (c[p.status] || 0) + 1; });
    return c;
  }, [list]);

  const rows = React.useMemo(() => {
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    let r = list.filter(p => {
      if (status !== "all" && p.status !== status) return false;
      if (repOnly && !p.reproducible) return false;
      if (terms.length) {
        const t = String(p.title || "").toLowerCase();
        if (!terms.every(w => t.indexOf(w) !== -1)) return false;
      }
      return true;
    });
    r = r.slice().sort((a, b) => {
      if (byActivity) {
        const d = (PF_ORDER[a.status] ?? 9) - (PF_ORDER[b.status] ?? 9);
        if (d) return d;
      }
      return String(b.scraped_at).localeCompare(String(a.scraped_at));
    });
    return r;
  }, [list, status, repOnly, byActivity, query]);

  return (
    <div className="pf-wrap">
      <Notice text={notice} />
      <Hero onWaitlist={onWaitlist} />
      <WorkflowViz list={list} />
      <div className="pf-sec pf-floor">
        <SectionHead title="status" note="updated every 4 seconds" />
        <StatStrip summary={summary} list={list} />
      </div>
      <FilterBar counts={counts} active={status} onStatus={setStatus} repOnly={repOnly} onRep={setRepOnly} query={query} onQuery={setQuery} />
      <div className="pf-sort">
        {rows.length} of {list.length} papers{query ? <React.Fragment> matching “<b style={{ color: "var(--pf-fg-2)", fontWeight: 500 }}>{query}</b>”</React.Fragment> : null} ·{" "}
        <button className="pf-linkbtn" onClick={() => setByActivity(!byActivity)}
          style={{ background: "none", border: 0, padding: 0, cursor: "pointer", font: "inherit", color: "var(--pf-cyan)", borderBottom: "1px solid rgba(70,217,232,.28)" }}>
          {byActivity ? "sorted by pipeline activity" : "sorted newest first"}
        </button>
      </div>
      <div className="pf-table">
        <div className="pf-hrow">
          <div>paper</div><div>authors</div><div>score</div><div>factory state</div>
        </div>
        {rows.length
          ? rows.map(p => <PaperRow key={p.arxiv_id} p={p} onOpen={onOpen} />)
          : <div className="pf-empty">{query
            ? "No title contains “" + query + "” under this filter."
            : "No papers match this filter."} {list.length ? "Clear it to see all " + list.length + " papers." : "Waiting for the first scrape to land."}</div>}
      </div>
      <div className="pf-foot"></div>
    </div>
  );
}

Object.assign(window, { PipelineScreen, StatStrip, FilterBar, PaperRow });
