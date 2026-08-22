import { useEffect, useMemo, useState } from "react";

import "./App.css";


const ACTIVE_STATUSES = new Set(["submitted", "collecting", "ingesting"]);

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function titleCase(value) {
  if (!value) return "No runs yet";
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.run?.error || data.error || `Request failed (${response.status})`);
  }
  return data;
}

export default function App() {
  const [papers, setPapers] = useState([]);
  const [runs, setRuns] = useState([]);
  const [query, setQuery] = useState("");
  const [reproducibleOnly, setReproducibleOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");
  const [error, setError] = useState("");

  async function loadData({ quiet = false } = {}) {
    if (!quiet) setLoading(true);
    try {
      const [paperData, runData] = await Promise.all([
        api("/api/papers/"),
        api("/api/scrape-runs/"),
      ]);
      setPapers(paperData.papers);
      setRuns(runData.runs);
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      if (!quiet) setLoading(false);
    }
  }

  async function startRun() {
    setAction("start");
    setError("");
    try {
      await api("/api/scrape-runs/", { method: "POST" });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      await loadData({ quiet: true });
      setAction("");
    }
  }

  async function runAction(runId, nextAction, { quiet = false } = {}) {
    if (!quiet) setAction(nextAction);
    try {
      await api(`/api/scrape-runs/${runId}/${nextAction}/`, { method: "POST" });
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      await loadData({ quiet: true });
      if (!quiet) setAction("");
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const latestRun = runs[0];

  useEffect(() => {
    if (!latestRun || !ACTIVE_STATUSES.has(latestRun.status)) return undefined;
    const timer = window.setTimeout(
      () => runAction(latestRun.id, "refresh", { quiet: true }),
      5000,
    );
    return () => window.clearTimeout(timer);
  }, [latestRun?.id, latestRun?.status, latestRun?.updated_at]);

  const visiblePapers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return papers.filter((paper) => {
      if (reproducibleOnly && !paper.reproducible) return false;
      if (!normalizedQuery) return true;
      return [paper.title, paper.abstract, ...paper.authors, ...paper.subjects]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [papers, query, reproducibleOnly]);

  const reproducibleCount = papers.filter((paper) => paper.reproducible).length;

  return (
    <main className="page-shell">
      <header className="masthead">
        <div>
          <p className="eyebrow">Bright Data → Django → PostgreSQL</p>
          <h1>Paper Factory</h1>
          <p className="intro">Fresh cs.AI papers, scored for reproducible ideas.</p>
        </div>
        <button className="primary-button" onClick={startRun} disabled={Boolean(action)}>
          {action === "start" ? "Starting…" : "Run Bright scraper"}
        </button>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="status-grid" aria-label="Pipeline status">
        <div className="stat-card">
          <span>Articles</span>
          <strong>{papers.length}</strong>
        </div>
        <div className="stat-card">
          <span>Reproducible</span>
          <strong>{reproducibleCount}</strong>
        </div>
        <div className="run-card">
          <div>
            <span>Latest run</span>
            <strong className={`status status-${latestRun?.status || "idle"}`}>
              {titleCase(latestRun?.status)}
            </strong>
          </div>
          <dl>
            <div><dt>Bright job</dt><dd>{latestRun?.bright_job_id || "—"}</dd></div>
            <div><dt>Written</dt><dd>{latestRun?.records_written ?? 0}</dd></div>
            <div><dt>Updated</dt><dd>{formatDate(latestRun?.updated_at)}</dd></div>
          </dl>
          {latestRun && (
            <div className="run-actions">
              <button onClick={() => runAction(latestRun.id, "refresh")} disabled={Boolean(action)}>
                Refresh
              </button>
              {latestRun.status === "collecting" && (
                <button onClick={() => runAction(latestRun.id, "pause")} disabled={Boolean(action)}>
                  Pause
                </button>
              )}
              {latestRun.status === "paused" && (
                <button onClick={() => runAction(latestRun.id, "resume")} disabled={Boolean(action)}>
                  Resume
                </button>
              )}
              {["submitted", "collecting", "paused"].includes(latestRun.status) && (
                <button onClick={() => runAction(latestRun.id, "cancel")} disabled={Boolean(action)}>
                  Cancel
                </button>
              )}
            </div>
          )}
          {latestRun?.error && <p className="run-error">{latestRun.error}</p>}
        </div>
      </section>

      <section className="papers-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Article database</p>
            <h2>{loading ? "Loading papers…" : `${visiblePapers.length} papers`}</h2>
          </div>
          <div className="filters">
            <input
              type="search"
              placeholder="Search title, author, subject…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-label="Search papers"
            />
            <label>
              <input
                type="checkbox"
                checked={reproducibleOnly}
                onChange={(event) => setReproducibleOnly(event.target.checked)}
              />
              Reproducible only
            </label>
          </div>
        </div>

        {!loading && visiblePapers.length === 0 ? (
          <div className="empty-state">
            <h3>No matching papers</h3>
            <p>Run the Bright scraper or clear the current filters.</p>
          </div>
        ) : (
          <div className="paper-grid">
            {visiblePapers.map((paper) => (
              <article className="paper-card" key={paper.arxiv_id}>
                <div className="paper-meta">
                  <span>{paper.arxiv_id}</span>
                  <span className={paper.reproducible ? "score score-high" : "score"}>
                    {Math.round(paper.score * 100)}% score
                  </span>
                </div>
                <h3>
                  <a href={paper.url} target="_blank" rel="noreferrer">{paper.title}</a>
                </h3>
                <p className="authors">{paper.authors.join(", ")}</p>
                <p className="abstract">{paper.abstract}</p>
                <div className="subject-list">
                  {paper.subjects.map((subject) => <span key={subject}>{subject}</span>)}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
