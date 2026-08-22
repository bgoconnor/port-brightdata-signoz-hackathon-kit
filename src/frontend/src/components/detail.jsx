/* Ported from the design handoff (pf-detail.jsx) to ES modules.
   JSX, class names and markup are unchanged: the prototype is the
   visual spec. Only the module wiring differs (globals -> imports). */

import React from "react";
import { ToolTile } from "./hero.jsx";
import { CodeBlock, Notice, ScoreBar, SectionHead, StatusChip, Terminal, pfAgo, pfStatus } from "./ui.jsx";

/* Paper Factory — Screen 2: Paper detail.
   The frame that explains the product: human prose on the left,
   machine-written code on the right, then proof that it ran. */

export function pfErrLine(out) {
  const s = typeof out === "string" ? out : "";
  const m = s.match(/^\s*([A-Za-z_]*(?:Error|Exception|Warning))\b.*$/m);
  if (m) return m[0].trim();
  const lines = s.trim().split("\n").filter(Boolean);
  return lines.length ? lines[lines.length - 1].trim() : "";
}

export function ReproSummary({ p }) {
  const attempts = Array.isArray(p.attempts) ? p.attempts : [];
  if (!attempts.length && !p.run_output) return null;
  const r = p.repro_result || {};
  return (
    <div className="pf-sec">
      <SectionHead title="the repro" note={attempts.length ? attempts.length + (attempts.length === 1 ? " attempt" : " attempts") + " \u00b7 sandboxed run" : "first run in progress"} />
      <div className="pf-repro">
        <div className="pf-repro-what">
          <u className="pf-eyebrow">what was reproduced</u>
          <p>{p.repro_summary || "The paper's headline claim was implemented and executed. The run output and every attempt are below."}</p>
          {p.repo_url ? (
            <a className="pf-repo" href={p.repo_url} target="_blank" rel="noreferrer noopener">
              <ToolTile t="gha" />{p.repo_url.replace("https://", "")}
            </a>
          ) : null}
        </div>
        <div className="pf-repro-res">
          <div><u className="pf-eyebrow">paper claims</u><b>{r.claimed || "\u2014"}</b></div>
          <div><u className="pf-eyebrow">factory measured</u><b>{r.measured || "\u2014"}</b></div>
          <div><u className="pf-eyebrow">verdict</u><span className={"pf-st pf-st--" + (r.reproduced ? "ok" : "no")}><i></i>{r.reproduced ? "reproduced" : "not reproduced"}</span></div>
        </div>
      </div>
    </div>
  );
}

export function ReviewBar({ paper, busy, onDecide }) {
  const passed = (paper.attempts || []).filter(a => a.status === "passed").length;
  const failed = (paper.attempts || []).filter(a => a.status === "failed").length;
  return (
    <div className="pf-review">
      <div>
        <div className="pf-review-t">The code ran. A human decides whether it reproduces the paper.</div>
        <div className="pf-review-s">
          {failed ? failed + (failed === 1 ? " failed attempt" : " failed attempts") + ", then " : ""}
          {passed ? passed + " clean run" : "no clean run yet"} · exit 0 · verified by execution, not by inspection
        </div>
      </div>
      <div className="pf-acts">
        <button className="pf-btn pf-btn--approve" disabled={busy} onClick={() => onDecide("approve")}>{busy ? "sending" : "approve"}</button>
        <button className="pf-btn pf-btn--reject" disabled={busy} onClick={() => onDecide("reject")}>reject</button>
      </div>
    </div>
  );
}

export function AttemptCard({ a, isLast }) {
  const ok = a.status === "passed";
  return (
    <div className="pf-att" data-ok={ok ? "1" : "0"}>
      <div className="pf-att-h">
        <b>attempt {a.index}</b>
        <span className={"pf-st pf-st--" + (ok ? "ok" : "no")}><i></i>{ok ? "passed" : "failed"}</span>
        <s>{ok ? "executed cleanly" : "re-prompted with the traceback"}{a.duration_s ? " · " + a.duration_s.toFixed(2) + "s" : ""}{a.finished_at ? " · " + pfAgo(a.finished_at) : ""}</s>
        <span className="pf-why">{ok ? (isLast ? "this is the code under review" : "superseded") : pfErrLine(a.output)}</span>
      </div>
      <div className="pf-att-b">
        <div>
          <div className="pf-att-lbl">code the agent produced</div>
          <CodeBlock code={a.code} height={290} />
        </div>
        <div>
          <div className="pf-att-lbl">{ok ? "program output" : "traceback fed back into the next prompt"}</div>
          <Terminal output={a.output} label={ok ? "stdout" : "stderr"} maxHeight={290} />
        </div>
      </div>
    </div>
  );
}

export function DetailScreen({ paper, stub, notice, loading, onBack, onDecide, busy }) {
  const p = paper || stub;
  if (!p) {
    return (
      <div className="pf-wrap">
        <button className="pf-back" onClick={onBack}>&larr; pipeline</button>
        <Notice text={notice || "This paper could not be loaded. It may not have been scraped yet."} />
        <div className="pf-foot"></div>
      </div>
    );
  }
  const st = pfStatus(p.status);
  const attempts = Array.isArray(p.attempts) ? p.attempts : [];
  const generating = p.status === "generating";
  const decided = p.status === "approved" || p.status === "rejected";
  const lastPassed = attempts.filter(a => a.status === "passed").slice(-1)[0];

  return (
    <div className="pf-wrap">
      <button className="pf-back" onClick={onBack}>&larr; pipeline</button>
      <Notice text={notice} />

      <div className="pf-head">
        <div>
          <h1 className="pf-h1">{p.title}</h1>
          <div className="pf-meta">
            <span className="pf-src">{p.source || "arXiv"}</span>
            {p.source_url
              ? <a href={p.source_url} target="_blank" rel="noreferrer noopener">{p.arxiv_id}</a>
              : <span>{p.arxiv_id}</span>}
            <span className="pf-dot">/</span>
            <span>{(p.subjects || []).join("  ")}</span>
            <span className="pf-dot">/</span>
            <span>{(p.authors || []).join(", ") || "authors unavailable"}</span>
            <span className="pf-dot">/</span>
            <span>scraped {pfAgo(p.scraped_at) || "recently"}</span>
          </div>
        </div>
        <div className="pf-hstat">
          <StatusChip status={p.status} retry={p.retry_count} />
          <div className="pf-hscore">
            <span>score {Number(p.score || 0).toFixed(2)}</span>
            <ScoreBar score={p.score} reproducible={p.reproducible} />
          </div>
        </div>
      </div>

      {p.status === "awaiting_review" ? <ReviewBar paper={p} busy={busy} onDecide={onDecide} /> : null}
      {decided ? (
        <div className="pf-decided">
          <StatusChip status={p.status} />
          <span>{p.status === "approved" ? "Approved by a human. The implementation is published to the reproductions index." : "Rejected by a human. The paper returns to the queue with the note below."}</span>
        </div>
      ) : null}
      {p.review_note ? <div className="pf-note"><b>reviewer note</b>{p.review_note}</div> : null}

      <ReproSummary p={p} />

      <div className="pf-frame">
        <div className="pf-pane">
          <div className="pf-pane-h" data-who="human"><b>abstract</b><u>human</u><s>{p.source || "arXiv"} · {p.arxiv_id}</s></div>
          <div className="pf-abstract">
            <div className="pf-lede">what the researchers claim</div>
            <p>{p.abstract || (loading ? "loading\u2026" : "No abstract was captured for this paper.")}</p>
          </div>
        </div>
        <div className="pf-pane">
          <div className="pf-pane-h" data-who="machine">
            <b>generated implementation</b><u>agent</u>
            <s>{generating ? <React.Fragment>writing<span className="pf-caret"></span></React.Fragment> : (p.generated_code ? "main.py · python 3.12" : "not written yet")}</s>
          </div>
          <CodeBlock code={p.generated_code} height={560} />
        </div>
      </div>

      <div className="pf-sec">
        <SectionHead title="run output" note={lastPassed && lastPassed.duration_s ? "attempt " + lastPassed.index + " · " + lastPassed.duration_s.toFixed(2) + "s · sandboxed, no network" : "sandboxed, no network"} />
        <Terminal output={p.run_output} running={generating} label={"python main.py"} />
      </div>

      <div className="pf-sec">
        <SectionHead title="attempt history" note={attempts.length
          ? attempts.length + (attempts.length === 1 ? " attempt" : " attempts") + " · " + attempts.filter(a => a.status === "failed").length + " failed · retry cap 2"
          : "no attempts yet"} />
        {attempts.length ? (
          <div className="pf-atts">
            {attempts.map((a, i) => <AttemptCard key={a.index + "-" + i} a={a} isLast={i === attempts.length - 1} />)}
          </div>
        ) : (
          <div className="pf-empty" style={{ border: "1px solid var(--pf-line)", padding: "28px 22px" }}>
            {generating ? "The agent is writing the first attempt now." : "This paper has not been dispatched to the agent."}
          </div>
        )}
      </div>
      <div className="pf-foot"></div>
    </div>
  );
}


