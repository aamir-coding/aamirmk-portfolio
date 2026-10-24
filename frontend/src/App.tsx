import { useEffect, useState } from "react";
import { fetchHealth, type HealthStatus } from "./lib/api";

export function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function checkHealth() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchHealth(controller.signal);
        setHealth(data);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Failed to connect to API");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void checkHealth();

    return () => {
      controller.abort();
    };
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, -apple-system, sans-serif", padding: "2rem", maxWidth: "600px", margin: "0 auto" }}>
      <h1>Aamir Mohammed Khan</h1>
      <p style={{ color: "#666" }}>AI Digital Assistant Portfolio — Walking Skeleton</p>

      <section style={{ marginTop: "2rem", padding: "1rem", border: "1px solid #ddd", borderRadius: "8px" }} aria-live="polite">
        <h2>System Status</h2>
        {loading && <p>Checking backend connectivity...</p>}
        {error && (
          <p style={{ color: "#d9411e" }}>
            <strong>Connection notice:</strong> {error}
          </p>
        )}
        {health && (
          <p style={{ color: "#0f766e" }}>
            <strong>Status:</strong> {health.status.toUpperCase()} (Ready: {health.ready ? "Yes" : "No"})
          </p>
        )}
      </section>
    </main>
  );
}

export default App;
