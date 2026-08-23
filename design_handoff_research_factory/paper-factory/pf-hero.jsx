/* Research Factory — page head: mark, title, prose, workflow rail + heal loops. */

function PFMark({ size }) {
  const s = size || 22;
  return (
    <svg className="pf-mark" width={s} height={s} viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10.25" fill="none" stroke="#46D9E8" strokeWidth="1.6" />
      <rect x="6.5" y="8" width="11" height="2" style={{ fill: "var(--pf-mark-bars, #F2F7F9)" }} />
      <rect x="6.5" y="12" width="8" height="2" style={{ fill: "var(--pf-mark-bars, #F2F7F9)" }} />
      <rect x="6.5" y="16" width="5" height="2" fill="#46D9E8" />
    </svg>
  );
}

function ToolTile({ t }) {
  const M = { port: "P", signoz: "S", bright: "B", k8s: "GH" };
  return M[t] ? <i className="pf-ttile" data-tool={t}>{M[t]}</i> : null;
}

function Hero({ onWaitlist }) {
  return (
    <div className="pf-hero">
      <div className="pf-hero-eyebrow">Papers in. Working code out.</div>
      <div className="pf-lockup"><PFMark size={62} /><h1 className="pf-hero-h1">Research Factory</h1></div>
      <div className="pf-hero-body">
        <p>
          Research Factory reads new AI research the day it appears, decides which claims can be
          reproduced from the text alone, and puts an agent to work writing runnable Python for the
          ones that can. Every program is executed before a person sees it, failures are re-prompted
          with their own traceback, and only code that actually ran reaches review.
        </p>
      </div>
      <div className="pf-hero-cta">
        <button className="pf-btn pf-btn--approve" onClick={onWaitlist}>join the waitlist</button>
        <div className="pf-hero-note">
          Choose the subjects and keywords you want scraped, set your own reproducibility bar, and
          wire finished reproductions into your product research pipeline.
        </div>
      </div>
    </div>
  );
}

function HBox({ tool, name, sub, small }) {
  return (
    <div className={"pf-hbox" + (small ? " pf-hbox--sm" : "")} data-tool={tool || "state"}>
      <b><ToolTile t={tool} />{name}</b>
      {sub ? <s>{sub}</s> : null}
    </div>
  );
}

function Leg({ t, name }) { return <span className="pf-leg"><i data-tool={t}></i>{name}</span>; }

function HealLoops() {
  const Arr = () => <span className="pf-harr" aria-hidden="true">&rarr;</span>;
  return (
    <div className="pf-heals">
      <div className="pf-heal">
        <div className="pf-heal-t">loop 1 &mdash; the scraper broke</div>
        <div className="pf-heal-row">
          <HBox name="Scrape fails" sub="partial rows land" />
          <Arr /><HBox tool="signoz" name="SigNoz" sub="detects, alerts" />
          <Arr /><HBox tool="port" name="Port" sub="heals, no gate" />
          <Arr /><HBox tool="bright" name="Bright Data" sub="gets a new scraper" />
        </div>
        <div className="pf-heal-drop" aria-hidden="true">
          <span className="pf-drop-line" style={{ left: "63%" }}></span>
          <div style={{ position: "absolute", left: "63%", top: 18, transform: "translateX(-50%)" }}>
            <HBox tool="port" name="human notified" small />
          </div>
        </div>
      </div>
      <div className="pf-heal">
        <div className="pf-heal-t">loop 2 &mdash; the generated reproduction broke</div>
        <div className="pf-heal-row">
          <HBox name="Paper flagged" sub="in the catalog" />
          <Arr /><HBox tool="port" name="Port agent" sub="writes code" />
          <Arr /><HBox tool="k8s" name="Kubernetes" sub="runs it" />
          <Arr /><HBox tool="port" name="Port" sub="human approves" />
        </div>
        <div className="pf-heal-return">
          <div className="pf-arc pf-arc--dash" style={{ left: "37%", right: "37%", top: 8 }}></div>
          <u>on failure, retry with the traceback, max 2</u>
        </div>
      </div>
    </div>
  );
}

function WorkflowViz({ list }) {
  const c = k => list.filter(p => p.status === k).length;
  const steps = [
    { k: "scrape", d: "Bright Data pulls new research from arXiv and the other sources you choose." },
    { k: "score", d: "Every paper is scored on how reproducible its claims are." },
    { k: "reproduce", d: "Port orchestrates an agent that reproduces the most promising research.", live: c("generating") > 0 ? "gen" : null },
    { k: "monitoring & review", d: "SigNoz watches the scrape and repro pipelines, alerting on failures to drive the self-healing loops. A person makes the final call.", live: c("awaiting_review") > 0 ? "human" : null }
  ];
  const n = steps.length;
  const at = i => ((i + 0.5) / n * 100);
  return (
    <div className="pf-wf">
      <div className="pf-wf-h"><b>how it works</b></div>
      <div className="pf-wf-grid">
        {steps.map(s => (
          <div className="pf-wf-col" key={s.k} data-live={s.live || ""}>
            <div className="pf-wf-lbl">{s.k}{s.live ? <i></i> : null}</div>
          </div>
        ))}
      </div>
      <div className="pf-wf-rail" aria-hidden="true">
        <span className="pf-wf-line"></span>
        {steps.map((s, i) => <span className="pf-wf-node" key={s.k} data-live={s.live || ""} style={{ left: at(i) + "%" }}></span>)}
        <i></i><i></i><i></i><i></i>
      </div>
      <div className="pf-wf-grid pf-wf-desc">
        {steps.map(s => (
          <div className="pf-wf-col" key={s.k}>
            <p>{s.d}</p>
          </div>
        ))}
      </div>
      <div className="pf-wf-h" style={{ borderTop: "1px solid var(--pf-line)" }}><b>self healing loops</b></div>
      <HealLoops />
    </div>
  );
}

Object.assign(window, { Hero, WorkflowViz, PFMark, HealLoops, ToolTile });
