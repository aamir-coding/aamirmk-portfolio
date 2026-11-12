import { useEffect, useRef, useState } from "react";
import { createSummary, type CreatedSummary, type SummaryProjectId } from "../../lib/summary";
import "../../styles/summary-action.css";

const utcDate = new Intl.DateTimeFormat("en", {
  dateStyle: "medium", timeStyle: "short", timeZone: "UTC",
});

export function SummaryAction({ projectIds }: { projectIds: readonly SummaryProjectId[] }) {
  const request = useRef<AbortController | null>(null);
  const [result, setResult] = useState<CreatedSummary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyStatus, setCopyStatus] = useState("");

  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, []);

  async function createLink() {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const deadline = window.setTimeout(() => controller.abort(), 90_000);
    setBusy(true);
    setError(null);
    setCopyStatus("");
    try {
      const summary = await createSummary(projectIds, controller.signal);
      if (request.current === controller) setResult(summary);
    } catch (cause) {
      if (request.current === controller) {
        setError(controller.signal.aborted || !(cause instanceof Error)
          ? "The summary could not be created. Try again."
          : cause.message);
      }
    } finally {
      window.clearTimeout(deadline);
      if (request.current === controller) {
        request.current = null;
        setBusy(false);
      }
    }
  }

  const sharePath = result ? `/s/${result.token}` : null;

  async function copyLink() {
    if (!sharePath) return;
    try {
      await navigator.clipboard.writeText(new URL(sharePath, window.location.origin).href);
      setCopyStatus("Link copied.");
    } catch {
      setCopyStatus("Open the summary and copy the address from your browser.");
    }
  }

  return (
    <section className="summary-action" aria-label="Share a team summary">
      <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void createLink()}>
        {busy ? "Creating summary…" : "Summarize for my team"}
      </button>
      {result && sharePath && (
        <>
          <div className="summary-action-links">
            <a href={sharePath} referrerPolicy="no-referrer">Open team summary</a>
            <button type="button" className="btn btn-secondary" onClick={() => void copyLink()}>
              Copy link
            </button>
          </div>
          <p>Anyone with the link can open it until {utcDate.format(new Date(result.expires_at))} UTC.</p>
        </>
      )}
      {copyStatus && <p role="status">{copyStatus}</p>}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
