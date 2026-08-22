import { useEffect, useState } from "react";

const initialHealth = {
  state: "checking",
  message: "Checking Django through the Kubernetes service…",
};

export default function App() {
  const [health, setHealth] = useState(initialHealth);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/health/", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Health check returned ${response.status}`);
        }
        return response.json();
      })
      .then((payload) => {
        setHealth({
          state: "ready",
          message: `${payload.service} is ready in ${payload.environment}.`,
        });
      })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setHealth({ state: "error", message: error.message });
        }
      });

    return () => controller.abort();
  }, []);

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Port × Bright Data × SigNoz</p>
        <h1>Paper Factory</h1>
        <p className="lede">
          A Django and React foundation for turning fresh AI papers into verified,
          runnable illustrations.
        </p>

        <div className={`status status--${health.state}`} role="status">
          <span className="status__dot" aria-hidden="true" />
          <span>{health.message}</span>
        </div>

        <div className="flow" aria-label="Planned application flow">
          <span>Collect</span>
          <span aria-hidden="true">→</span>
          <span>Score</span>
          <span aria-hidden="true">→</span>
          <span>Reproduce</span>
          <span aria-hidden="true">→</span>
          <span>Verify</span>
        </div>
      </section>
    </main>
  );
}

