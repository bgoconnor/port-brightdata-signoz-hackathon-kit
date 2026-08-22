/* Ported from the design handoff (pf-ui.jsx) to ES modules.
   JSX, class names and markup are unchanged: the prototype is the
   visual spec. Only the module wiring differs (globals -> imports). */

import React from "react";
import { lines as hlLines } from "../lib/highlight.js";

/* Paper Factory — shared UI atoms. All content arrives as React text
   nodes (never innerHTML), so scraped titles/abstracts cannot inject markup. */

export const PF_STATUS = {
  ingested: { label: "ingested", fam: "inert" },
  queued: { label: "queued", fam: "queued" },
  generating: { label: "generating", fam: "gen" },
  awaiting_review: { label: "repro", fam: "human" },
  approved: { label: "approved", fam: "ok" },
  rejected: { label: "rejected", fam: "no" }
};
export const PF_ORDER = { generating: 0, awaiting_review: 1, queued: 2, approved: 3, rejected: 4, ingested: 5 };

export function pfStatus(s) { return PF_STATUS[s] || PF_STATUS.ingested; }

export function pfAuthors(list) {
  const a = Array.isArray(list) ? list.filter(Boolean) : [];
  if (!a.length) return "—";
  if (a.length <= 2) return a.join(", ");
  return a.slice(0, 2).join(", ") + " et al.";
}

export function pfAgo(iso) {
  if (!iso) return "";
  const t = Date.parse(iso);
  if (!isFinite(t)) return "";
  const m = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (m < 60) return m + "m ago";
  const h = Math.round(m / 60);
  if (h < 48) return h + "h ago";
  return Math.round(h / 24) + "d ago";
}

export function StatusChip({ status, retry }) {
  const s = pfStatus(status);
  return (
    <span className={"pf-st pf-st--" + s.fam}>
      <i></i>{s.label}
      {retry > 0 ? <em>{"\u00d7" + (retry + 1)}</em> : null}
    </span>
  );
}

export function ScoreBar({ score, reproducible }) {
  const v = Math.max(0, Math.min(1, Number(score) || 0));
  return (
    <div className="pf-score">
      <div className="pf-bar" data-rep={reproducible ? "1" : "0"} title={"reproducibility score " + v.toFixed(2)}>
        <i style={{ width: (v * 100).toFixed(1) + "%" }}></i>
      </div>
      {reproducible ? <span className="pf-flag">REP</span> : null}
    </div>
  );
}

/* syntax-highlighted Python with line numbers */
export function CodeBlock({ code, height }) {
  const src = typeof code === "string" ? code : "";
  const lines = React.useMemo(() => hlLines(src), [src]);
  if (!src.trim()) {
    return (
      <div className="pf-codewrap" style={height ? { height } : null}>
        <div className="pf-code" style={{ padding: "22px 24px", color: "#5F7580" }}>no code produced yet<span className="pf-caret"></span></div>
      </div>
    );
  }
  return (
    <div className="pf-codewrap" style={height ? { height } : null}>
      <div className="pf-code">
        {lines.map((toks, i) => (
          <div className="pf-ln" key={i}>
            <u>{i + 1}</u>
            <span>{toks.length ? toks.map((t, j) => t.c ? <span className={"tk-" + t.c} key={j}>{t.t}</span> : <React.Fragment key={j}>{t.t}</React.Fragment>) : "\u00a0"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function pfOutClass(line) {
  if (/^\s*\$ /.test(line)) return "pf-cmd";
  if (/Traceback|^\s*File "|Error:|error:|^[A-Za-z]*Error\b|exit status [1-9]/.test(line)) return "pf-err";
  if (/Warning|warn/.test(line)) return "pf-warn";
  if (/REPRODUCED: True|exit status 0|held: True/.test(line)) return "pf-ok";
  return "";
}

export function Terminal({ output, label, running, maxHeight }) {
  const raw = typeof output === "string" ? output : "";
  const lines = raw.replace(/\s+$/, "").split("\n");
  const bad = /exit status [1-9]|Traceback/.test(raw);
  const code = bad ? "exit 1" : (raw ? "exit 0" : "—");
  return (
    <div className="pf-term">
      <div className="pf-term-h">
        <span>{label || "run output"}</span>
        <b data-bad={bad ? "1" : "0"}>{running ? "running" : code}</b>
        <s>{running ? "streaming" : (raw ? lines.length + " lines" : "nothing yet")}</s>
      </div>
      <pre className="pf-out" style={maxHeight ? { maxHeight } : null}>
        {raw
          ? lines.map((l, i) => <div className={pfOutClass(l)} key={i}>{l || "\u00a0"}</div>)
          : <div style={{ color: "#5F7580" }}>{running ? "$ python main.py" : "the program has not been executed yet"}<span className="pf-caret"></span></div>}
      </pre>
    </div>
  );
}

export function Notice({ text }) {
  if (!text) return null;
  return <div className="pf-notice"><b>degraded</b><span>{text}</span></div>;
}

export function SectionHead({ title, note }) {
  return <div className="pf-sec-h"><h2>{title}</h2>{note ? <s>{note}</s> : null}<span className="pf-rule"></span></div>;
}


