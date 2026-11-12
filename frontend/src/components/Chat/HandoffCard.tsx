import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { submitHandoff } from "../../lib/api";
import type { ChatHistoryMessage } from "../../lib/types";

interface HandoffCardProps {
  id: string;
  transcript: readonly ChatHistoryMessage[];
}

export function HandoffCard({ id, transcript }: HandoffCardProps) {
  const heading = useId();
  const request = useRef<AbortController | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent || sent || request.current) return;
    const form = new FormData(event.currentTarget);
    const controller = new AbortController();
    request.current = controller;
    const timeout = window.setTimeout(() => controller.abort(), 20_000);
    setError(null);
    setBusy(true);
    try {
      await submitHandoff({
        id,
        consent: true,
        website: String(form.get("website") ?? ""),
        reply_email: String(form.get("reply_email") ?? "").trim() || null,
        transcript,
      }, controller.signal);
      if (request.current === controller) setSent(true);
    } catch (cause) {
      if (request.current === controller) {
        setError(controller.signal.aborted
          ? "The handoff could not be confirmed. You can try again."
          : cause instanceof Error ? cause.message : "The handoff could not be confirmed.");
      }
    } finally {
      window.clearTimeout(timeout);
      if (request.current === controller) {
        request.current = null;
        setBusy(false);
      }
    }
  }

  return (
    <section className="handoff-card" aria-labelledby={heading}>
      <h3 id={heading}>Send this to Aamir?</h3>
      {sent ? <p role="status">Request received.</p> : (
        <form onSubmit={(event) => void handleSubmit(event)}>
          <p>Aamir will receive up to 10 recent messages through Telegram. Include your email if you’d like a reply.</p>
          <details>
            <summary>Preview messages to share</summary>
            <ol className="handoff-transcript">
              {transcript.map(({ role, content }, index) => (
                <li key={index}>
                  <strong>{role === "user" ? "You" : "Assistant"}</strong>
                  <p>{content}</p>
                </li>
              ))}
            </ol>
          </details>
          <label className="handoff-email">
            Reply email (optional)
            <input type="email" name="reply_email" autoComplete="email" maxLength={254} disabled={busy} />
          </label>
          <input type="text" name="website" autoComplete="off" tabIndex={-1} hidden />
          <label className="handoff-consent">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} disabled={busy} />
            I agree to share the previewed messages and my reply email, if provided.
          </label>
          <button type="submit" className="btn btn-primary" disabled={!consent || busy}>
            {busy ? "Sending…" : "Send to Aamir"}
          </button>
          {error && <p role="alert">{error}</p>}
        </form>
      )}
    </section>
  );
}
