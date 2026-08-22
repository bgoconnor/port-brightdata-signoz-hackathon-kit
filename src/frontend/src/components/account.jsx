/* Ported from the design handoff (pf-account.jsx) to ES modules.
   JSX, class names and markup are unchanged: the prototype is the
   visual spec. Only the module wiring differs (globals -> imports). */

import React from "react";
import { SectionHead } from "./ui.jsx";

/* Paper Factory — waitlist, sign-in and settings. Mocked surfaces:
   nothing here is persisted or sent anywhere in this prototype. */

export const PF_SUBJECTS = ["cs.LG", "cs.CL", "cs.CV", "cs.AI", "stat.ML", "cs.RO", "cs.IR", "cs.SE", "cs.NE"];
export const PF_SOURCES = [
  { k: "arXiv cs.* new listings", d: "every weekday, within an hour of posting" },
  { k: "Frontier-lab research blogs", d: "OpenAI, DeepMind, Anthropic, Meta AI" },
  { k: "Paper indexes", d: "Hugging Face papers, Semantic Scholar alerts" }
];
export const PF_INTEGRATIONS = [
  { k: "Webhook on approve", d: "POST the paper, the code and the run output to a URL you own" },
  { k: "REST API + key", d: "poll the same endpoints this console uses" },
  { k: "Pull request", d: "open a PR with the reproduction into a repo you nominate" },
  { k: "Slack digest", d: "one message per approved reproduction" },
  { k: "Weekly email", d: "what was flagged, what ran, what a human kept" }
];

export function Field({ label, hint, children }) {
  return (
    <label className="pf-field">
      <span className="pf-field-l">{label}</span>
      {hint ? <span className="pf-field-h">{hint}</span> : null}
      {children}
    </label>
  );
}

export function ChipPick({ options, value, onChange }) {
  return (
    <div className="pf-pick">
      {options.map(o => {
        const on = value.indexOf(o) !== -1;
        return (
          <button type="button" className="pf-chip" key={o} aria-pressed={on}
            onClick={() => onChange(on ? value.filter(v => v !== o) : value.concat([o]))}>{o}</button>
        );
      })}
    </div>
  );
}

export function CheckList({ options, value, onChange }) {
  return (
    <div className="pf-checks">
      {options.map(o => {
        const on = value.indexOf(o.k) !== -1;
        return (
          <button type="button" className="pf-check" key={o.k} aria-pressed={on}
            onClick={() => onChange(on ? value.filter(v => v !== o.k) : value.concat([o.k]))}>
            <i></i>
            <span><b>{o.k}</b><s>{o.d}</s></span>
          </button>
        );
      })}
    </div>
  );
}

export function KeywordInput({ value, onChange }) {
  const [draft, setDraft] = React.useState("");
  const add = () => {
    const w = draft.trim().toLowerCase();
    if (w && value.indexOf(w) === -1) onChange(value.concat([w]));
    setDraft("");
  };
  return (
    <div>
      <div className="pf-search" style={{ maxWidth: 460 }}>
        <span>+</span>
        <input value={draft} onChange={e => setDraft(e.target.value)} spellCheck="false"
          placeholder="speculative decoding, adapters, retrieval…"
          onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); add(); } }} />
        <button type="button" onClick={add}>add</button>
      </div>
      {value.length ? (
        <div className="pf-pick" style={{ marginTop: 12 }}>
          {value.map(w => (
            <button type="button" className="pf-chip" key={w} aria-pressed="true"
              onClick={() => onChange(value.filter(v => v !== w))}>{w} &times;</button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function useConfig() {
  return React.useState({
    subjects: ["cs.LG", "cs.CL"],
    keywords: ["speculative decoding", "adapters"],
    sources: [PF_SOURCES[0].k, PF_SOURCES[1].k],
    threshold: 0.7,
    retries: 2,
    integrations: [PF_INTEGRATIONS[0].k, PF_INTEGRATIONS[1].k]
  });
}

export function ConfigFields({ cfg, set }) {
  return (
    <React.Fragment>
      <Field label="areas of interest" hint="arXiv subject classes the scraper watches">
        <ChipPick options={PF_SUBJECTS} value={cfg.subjects} onChange={v => set({ subjects: v })} />
      </Field>
      <Field label="title keywords" hint="a paper matching any of these is scored even if its subject is not selected">
        <KeywordInput value={cfg.keywords} onChange={v => set({ keywords: v })} />
      </Field>
      <Field label="sources" hint="where the scraper looks">
        <CheckList options={PF_SOURCES} value={cfg.sources} onChange={v => set({ sources: v })} />
      </Field>
      <Field label="reproducibility bar" hint="claims scoring below this are held, not dispatched to the agent">
        <div className="pf-range">
          <input type="range" min="0.5" max="0.95" step="0.01" value={cfg.threshold}
            onChange={e => set({ threshold: parseFloat(e.target.value) })} />
          <b>{Number(cfg.threshold).toFixed(2)}</b>
        </div>
      </Field>
      <Field label="retry cap" hint="how many times a failed program is re-prompted with its traceback">
        <div className="pf-range">
          <input type="range" min="0" max="4" step="1" value={cfg.retries}
            onChange={e => set({ retries: parseInt(e.target.value, 10) })} />
          <b>{cfg.retries}</b>
        </div>
      </Field>
      <Field label="pipeline integrations" hint="how approved reproductions leave the factory">
        <CheckList options={PF_INTEGRATIONS} value={cfg.integrations} onChange={v => set({ integrations: v })} />
      </Field>
    </React.Fragment>
  );
}

export function WaitlistScreen({ onBack }) {
  const [cfg, setCfg] = useConfig();
  const set = patch => setCfg(c => Object.assign({}, c, patch));
  const [email, setEmail] = React.useState("");
  const [org, setOrg] = React.useState("");
  const [sent, setSent] = React.useState(false);

  if (sent) {
    return (
      <div className="pf-wrap pf-narrow">
        <button className="pf-back" onClick={onBack}>&larr; factory</button>
        <h1 className="pf-page-h1">You are on the list</h1>
        <div className="pf-hero-body"><p>
          We will write to <b>{email || "your address"}</b> when a slot opens. Your configuration is
          held with the request, so the first scrape you see is already filtered to your work.
        </p></div>
        <div className="pf-sec">
          <SectionHead title="what we recorded" />
          <div className="pf-recap">
            <div><u>subjects</u><b>{cfg.subjects.join(", ") || "none selected"}</b></div>
            <div><u>keywords</u><b>{cfg.keywords.join(", ") || "none"}</b></div>
            <div><u>sources</u><b>{cfg.sources.join(", ") || "none"}</b></div>
            <div><u>bar / retries</u><b>score &ge; {Number(cfg.threshold).toFixed(2)} · {cfg.retries} retries</b></div>
            <div><u>integrations</u><b>{cfg.integrations.join(", ") || "none"}</b></div>
          </div>
        </div>
        <div className="pf-mocknote">Prototype: nothing was sent and nothing is stored.</div>
        <div className="pf-foot"></div>
      </div>
    );
  }

  return (
    <div className="pf-wrap pf-narrow">
      <button className="pf-back" onClick={onBack}>&larr; factory</button>
      <h1 className="pf-page-h1">Join the waitlist</h1>
      <div className="pf-hero-body"><p>
        Tell us what you want read. The factory scrapes the subjects and keywords you pick, scores
        every claim against your own bar, and hands you reproductions that have already run.
      </p></div>

      <form className="pf-form" onSubmit={e => { e.preventDefault(); setSent(true); }}>
        <div className="pf-form-row">
          <Field label="work email">
            <input className="pf-input" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@lab.org" />
          </Field>
          <Field label="team or company">
            <input className="pf-input" value={org} onChange={e => setOrg(e.target.value)} placeholder="e.g. applied research" />
          </Field>
        </div>
        <ConfigFields cfg={cfg} set={set} />
        <div className="pf-form-actions">
          <button className="pf-btn pf-btn--approve" type="submit">request a slot</button>
          <button className="pf-btn pf-btn--reject" type="button" onClick={onBack}>back to the floor</button>
        </div>
      </form>
      <div className="pf-mocknote">Prototype: the form does not submit anywhere.</div>
      <div className="pf-foot"></div>
    </div>
  );
}

export function SignInScreen({ onBack, onSignedIn, onWaitlist }) {
  const [email, setEmail] = React.useState("");
  return (
    <div className="pf-wrap pf-narrow">
      <button className="pf-back" onClick={onBack}>&larr; factory</button>
      <h1 className="pf-page-h1">Sign in</h1>
      <div className="pf-hero-body"><p>Operators sign in to change what the factory reads and where finished reproductions go.</p></div>
      <form className="pf-form" style={{ maxWidth: 480 }} onSubmit={e => { e.preventDefault(); onSignedIn(); }}>
        <Field label="work email">
          <input className="pf-input" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@lab.org" />
        </Field>
        <Field label="password">
          <input className="pf-input" type="password" required placeholder="••••••••••" />
        </Field>
        <div className="pf-form-actions">
          <button className="pf-btn pf-btn--approve" type="submit">sign in</button>
          <button className="pf-btn pf-btn--reject" type="button" onClick={onWaitlist}>join the waitlist</button>
        </div>
      </form>
      <div className="pf-mocknote">Prototype: any address signs in. There is no auth behind this.</div>
      <div className="pf-foot"></div>
    </div>
  );
}

export function SettingsScreen({ onBack }) {
  const [cfg, setCfg] = useConfig();
  const set = patch => setCfg(c => Object.assign({}, c, patch));
  const [saved, setSaved] = React.useState(false);
  React.useEffect(() => { if (!saved) return; const t = setTimeout(() => setSaved(false), 2200); return () => clearTimeout(t); }, [saved]);
  return (
    <div className="pf-wrap pf-narrow">
      <button className="pf-back" onClick={onBack}>&larr; factory</button>
      <h1 className="pf-page-h1">Settings</h1>
      <div className="pf-hero-body"><p>
        What the factory reads, how hard it has to try, and where a kept reproduction goes next.
      </p></div>

      <div className="pf-sec">
        <SectionHead title="intake and policy" />
        <div className="pf-form"><ConfigFields cfg={cfg} set={set} /></div>
      </div>

      <div className="pf-sec">
        <SectionHead title="api access" note="the same endpoints this console polls" />
        <div className="pf-form">
          <Field label="api key">
            <div className="pf-key"><code>pf_live_8f2c41d7a90b4e55</code><button type="button" onClick={() => setSaved(true)}>copy</button></div>
          </Field>
          <Field label="webhook url" hint="called once a human approves a reproduction">
            <input className="pf-input" defaultValue="https://hooks.your-lab.dev/paper-factory" />
          </Field>
        </div>
      </div>

      <div className="pf-sec">
        <SectionHead title="account" />
        <div className="pf-form">
          <div className="pf-form-row">
            <Field label="operator"><input className="pf-input" defaultValue="riley@lab.org" /></Field>
            <Field label="notifications" hint="when a paper needs a decision"><input className="pf-input" defaultValue="email + Slack" /></Field>
          </div>
        </div>
      </div>

      <div className="pf-form-actions">
        <button className="pf-btn pf-btn--approve" onClick={() => setSaved(true)}>{saved ? "saved" : "save changes"}</button>
        <button className="pf-btn pf-btn--reject" onClick={onBack}>back to the floor</button>
      </div>
      <div className="pf-mocknote">Prototype: settings are held in memory and reset on reload.</div>
      <div className="pf-foot"></div>
    </div>
  );
}


