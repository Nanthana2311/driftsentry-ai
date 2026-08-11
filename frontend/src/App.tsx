import { useEffect, useState } from "react";

import { getLiveness, type LivenessResponse } from "./api";

type HealthState =
  | { kind: "loading" }
  | { kind: "online"; data: LivenessResponse }
  | { kind: "offline"; message: string };

const milestones = [
  { label: "System foundation", detail: "API, containers and contracts", state: "complete" },
  { label: "Model registry", detail: "Versions, features and ingestion keys", state: "next" },
  { label: "Prediction telemetry", detail: "Idempotent event collection", state: "planned" },
  { label: "Monitoring engine", detail: "Statistical signals and evidence", state: "planned" },
];

function PulseIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 40 40" className="brand-mark">
      <path d="M4 22h8l3-10 6 20 4-14 3 4h8" />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" className="chevron">
      <path d="m6 3 5 5-5 5" />
    </svg>
  );
}

function App() {
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    getLiveness(controller.signal)
      .then((data) => setHealth({ kind: "online", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const message = error instanceof Error ? error.message : "Unknown connection error";
        setHealth({ kind: "offline", message });
      });
    return () => controller.abort();
  }, []);

  const online = health.kind === "online";
  const statusLabel = health.kind === "loading" ? "Checking" : online ? "Operational" : "Unavailable";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#top" aria-label="DriftSentry home">
          <PulseIcon />
          <span>
            <strong>DriftSentry</strong>
            <small>ML reliability</small>
          </span>
        </a>

        <nav className="nav" aria-label="Primary navigation">
          <p className="nav-label">Workspace</p>
          <a className="nav-item active" href="#overview">
            <span className="nav-dot" /> Overview
          </a>
          <span className="nav-item muted"><span className="nav-dot" /> Models <em>Soon</em></span>
          <span className="nav-item muted"><span className="nav-dot" /> Incidents <em>Soon</em></span>
          <span className="nav-item muted"><span className="nav-dot" /> Benchmarks <em>Soon</em></span>
        </nav>

        <div className="sidebar-note">
          <span className="eyebrow">Build phase</span>
          <strong>Foundation</strong>
          <p>Day 1 of the production monitoring build.</p>
          <div className="progress-track" aria-label="Foundation phase complete">
            <span style={{ width: "12%" }} />
          </div>
        </div>
      </aside>

      <main id="top" className="main">
        <header className="topbar">
          <div>
            <span className="breadcrumb">DriftSentry /</span> Overview
          </div>
          <div className={`service-pill ${online ? "online" : ""}`}>
            <span className="status-light" /> API {statusLabel}
          </div>
        </header>

        <div className="content" id="overview">
          <section className="hero">
            <div>
              <span className="eyebrow accent">System control</span>
              <h1>Trust your model<br />after deployment.</h1>
              <p>
                DriftSentry turns production prediction telemetry into measurable drift signals,
                inspectable evidence, and actionable incidents.
              </p>
            </div>
            <div className="hero-visual" aria-hidden="true">
              <div className="orbit orbit-one" />
              <div className="orbit orbit-two" />
              <div className="core-pulse"><PulseIcon /></div>
              <span className="node node-one">INGEST</span>
              <span className="node node-two">DETECT</span>
              <span className="node node-three">EXPLAIN</span>
            </div>
          </section>

          <section className="metrics-grid" aria-label="Foundation status">
            <article className="metric-card primary">
              <div className="card-heading">
                <span>API process</span>
                <span className={`status-badge ${online ? "good" : "neutral"}`}>{statusLabel}</span>
              </div>
              <strong className="metric-value">{online ? health.data.version : "—"}</strong>
              <p>{online ? `${health.data.service} · ${health.data.environment}` : "Waiting for backend connection"}</p>
            </article>
            <article className="metric-card">
              <div className="card-heading"><span>Architecture</span><span className="mini-index">01</span></div>
              <strong className="metric-value small">Designed</strong>
              <p>API, database, queue, worker and dashboard boundaries</p>
            </article>
            <article className="metric-card">
              <div className="card-heading"><span>Current capability</span><span className="mini-index">02</span></div>
              <strong className="metric-value small">Health</strong>
              <p>Separate liveness and dependency-readiness checks</p>
            </article>
          </section>

          <section className="lower-grid">
            <article className="panel roadmap-panel">
              <div className="panel-title">
                <div>
                  <span className="eyebrow">Implementation queue</span>
                  <h2>From foundation to evidence</h2>
                </div>
                <span className="panel-code">DS / 001</span>
              </div>
              <div className="milestone-list">
                {milestones.map((milestone, index) => (
                  <div className={`milestone ${milestone.state}`} key={milestone.label}>
                    <span className="milestone-number">{String(index + 1).padStart(2, "0")}</span>
                    <span className="milestone-copy">
                      <strong>{milestone.label}</strong>
                      <small>{milestone.detail}</small>
                    </span>
                    <span className="milestone-state">{milestone.state}</span>
                    <ChevronIcon />
                  </div>
                ))}
              </div>
            </article>

            <article className="panel principle-panel">
              <span className="eyebrow accent">Engineering principle</span>
              <blockquote>“The LLM explains evidence. It does not decide whether drift exists.”</blockquote>
              <div className="evidence-chain">
                <span>Telemetry</span><i />
                <span>Statistics</span><i />
                <span>Evidence</span><i />
                <span>Report</span>
              </div>
              {health.kind === "offline" && (
                <p className="error-note">Backend check: {health.message}</p>
              )}
            </article>
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
