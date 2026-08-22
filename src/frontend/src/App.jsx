/* Ported from the design handoff (pf-app.jsx) to ES modules.
   Root: view switching, 4s polling, degradation handling. State-based
   view switching as in the prototype - no router. */

import React from "react";
import { PFMark } from "./components/hero.jsx";
import { Notice } from "./components/ui.jsx";
import { PipelineScreen } from "./components/list.jsx";
import { DetailScreen } from "./components/detail.jsx";
import { SettingsScreen, SignInScreen, WaitlistScreen } from "./components/account.jsx";
import { fetchPaper, fetchPapers, fetchSummary, submitReview } from "./api/client.js";

/* Paper Factory — root: routing, polling, degradation handling. */

const PF_POLL_MS = 4000;

class PFBoundary extends React.Component {
  constructor(p) { super(p); this.state = { err: null }; }
  static getDerivedStateFromError(err) { return { err: err }; }
  render() {
    if (this.state.err) {
      return (
        <div className="pf-wrap">
          <Notice text={"This view failed to render (" + String(this.state.err && this.state.err.message) + "). The rest of the console is unaffected."} />
          <div className="pf-foot"></div>
        </div>
      );
    }
    return this.props.children;
  }
}

/* Top bar: logo tile, factory/settings tabs, then on the right the
   "N repros ready" pill, the light/dark toggle and the waitlist CTA.
   The live/poll chip and sign-in button stay removed; SignInScreen is
   kept in code but unlinked. */
function TopBar({ awaiting, view, go, theme, onTheme }) {
  const tab = (k, label) => (
    <button className="pf-tab" aria-current={view === k || (k === "list" && view === "detail") ? "page" : undefined} onClick={() => go(k)}>{label}</button>
  );
  return (
    <div className="pf-top">
      <div className="pf-wrap">
        <button className="pf-logo" onClick={() => go("list")} aria-label="Research Factory home"><PFMark size={26} /></button>
        <div className="pf-top-sep"></div>
        <nav className="pf-nav">
          {tab("list", "factory")}
          {tab("settings", "settings")}
        </nav>
        <div className="pf-top-right">
          {awaiting > 0 ? <div className="pf-await"><i></i>{awaiting} repros ready</div> : null}
          <button className="pf-tab" onClick={onTheme}>{theme === "dark" ? "light mode" : "dark mode"}</button>
          <button className="pf-cta" onClick={() => go("waitlist")}>join the waitlist</button>
        </div>
      </div>
    </div>
  );
}

export default function PaperFactory() {
  const [list, setList] = React.useState([]);
  const [summary, setSummary] = React.useState(null);
  const [mode, setMode] = React.useState("fallback");
  const [notice, setNotice] = React.useState(null);
  const [updatedAt, setUpdatedAt] = React.useState("");
  const [view, setView] = React.useState({ name: "list", id: null });
  const [detail, setDetail] = React.useState(null);
  const [detailNotice, setDetailNotice] = React.useState(null);
  const [loadingDetail, setLoadingDetail] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [signedIn, setSignedIn] = React.useState(false);
  const [theme, setTheme] = React.useState(() => document.documentElement.dataset.pfTheme || "light");
  React.useEffect(() => {
    document.documentElement.dataset.pfTheme = theme;
    try { localStorage.setItem("pf-theme", theme); } catch (e) {}
  }, [theme]);
  const viewRef = React.useRef(view);
  viewRef.current = view;

  const clock = () => new Date().toLocaleTimeString([], { hour12: false });

  const poll = React.useCallback(() => {
    fetchSummary().then(r => { setSummary(r.data); setMode(r.source); setNotice(r.notice); setUpdatedAt(clock()); }).catch(() => {});
    fetchPapers().then(r => { if (Array.isArray(r.data) && r.data.length) setList(r.data); if (r.notice) setNotice(r.notice); }).catch(() => {});
    const v = viewRef.current;
    if (v.name === "detail" && v.id) {
      fetchPaper(v.id).then(r => {
        if (viewRef.current.id !== v.id) return;
        if (r.data) setDetail(r.data);
        setDetailNotice(r.notice);
      }).catch(() => {});
    }
  }, []);

  React.useEffect(() => {
    poll();
    const t = setInterval(poll, PF_POLL_MS);
    return () => clearInterval(t);
  }, [poll]);

  const open = React.useCallback(id => {
    setView({ name: "detail", id: id });
    setDetail(null); setDetailNotice(null); setLoadingDetail(true);
    window.scrollTo(0, 0);
    fetchPaper(id).then(r => { setDetail(r.data); setDetailNotice(r.notice); setLoadingDetail(false); })
      .catch(() => { setLoadingDetail(false); setDetailNotice("This paper could not be loaded."); });
  }, []);

  const back = React.useCallback(() => { setView({ name: "list", id: null }); window.scrollTo(0, 0); }, []);
  const go = React.useCallback(k => { setView({ name: k, id: null }); window.scrollTo(0, 0); }, []);

  const decide = React.useCallback(decision => {
    const id = viewRef.current.id;
    if (!id) return;
    setBusy(true);
    const optimistic = decision === "approve" ? "approved" : "rejected";
    setDetail(d => (d ? Object.assign({}, d, { status: optimistic }) : d));
    setList(l => l.map(p => (p.paper_id === id ? Object.assign({}, p, { status: optimistic }) : p)));
    submitReview(id, decision).then(r => {
      if (r.data) setDetail(r.data);
      setDetailNotice(r.notice);
      setBusy(false);
      poll();
    }).catch(() => { setBusy(false); setDetailNotice("The decision could not be sent to the API. It is applied locally only."); });
  }, [poll]);

  const awaiting = list.filter(p => p.status === "awaiting_review").length;
  const stub = view.id ? list.find(p => p.paper_id === view.id) : null;

  return (
    <div className="pf-shell">
      <TopBar awaiting={awaiting} view={view.name} go={go} theme={theme} onTheme={() => setTheme(t => (t === "dark" ? "light" : "dark"))} />
      <PFBoundary>
        {view.name === "list"
          ? <PipelineScreen list={list} summary={summary} notice={notice} onOpen={open} onWaitlist={() => go("waitlist")} />
          : view.name === "detail"
            ? <DetailScreen paper={detail} stub={stub} notice={detailNotice} loading={loadingDetail} onBack={back} onDecide={decide} busy={busy} />
            : view.name === "waitlist"
              ? <WaitlistScreen onBack={back} />
              : view.name === "signin"
                ? <SignInScreen onBack={back} onWaitlist={() => go("waitlist")} onSignedIn={() => { setSignedIn(true); go("settings"); }} />
                : <SettingsScreen onBack={back} />}
      </PFBoundary>
    </div>
  );
}

