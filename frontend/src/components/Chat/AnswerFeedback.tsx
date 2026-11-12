import { useEffect, useRef, useState, type FormEvent } from "react";
import { submitFeedback } from "../../lib/api";
import type { FeedbackRating } from "../../lib/types";

const RATINGS = [
  { rating: "up", icon: "👍", label: "Helpful" },
  { rating: "down", icon: "👎", label: "Not helpful" },
] as const;

export function AnswerFeedback({ answerId }: { answerId: string }) {
  const request = useRef<AbortController | null>(null);
  const [rating, setRating] = useState<FeedbackRating | null>(null);
  const [saved, setSaved] = useState<FeedbackRating | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!rating || request.current) return;
    const reason = String(new FormData(event.currentTarget).get("reason") ?? "").trim();
    const controller = new AbortController();
    request.current = controller;
    const timeout = window.setTimeout(() => controller.abort(), 12_000);
    setBusy(true);
    setError(null);
    try {
      const result = await submitFeedback(answerId, rating, reason || null, controller.signal);
      if (request.current === controller) setSaved(result);
    } catch (cause) {
      if (request.current === controller) {
        setError(controller.signal.aborted || !(cause instanceof Error)
          ? "Feedback could not be confirmed. Try again."
          : cause.message);
      }
    } finally {
      window.clearTimeout(timeout);
      if (request.current === controller) {
        request.current = null;
        setBusy(false);
      }
    }
  }

  if (saved) {
    return (
      <p className="answer-feedback" role="status">
        {saved === rating ? "Feedback saved." : "Feedback was already recorded for this answer."}
      </p>
    );
  }
  return (
    <form className="answer-feedback" onSubmit={(event) => void handleSubmit(event)}>
      <div className="feedback-options" role="group" aria-label="Rate this answer">
        {RATINGS.map((choice) => (
          <button
            key={choice.rating}
            type="button"
            className="btn btn-secondary"
            aria-pressed={rating === choice.rating}
            onClick={() => setRating(choice.rating)}
            disabled={busy}
          >
            <span aria-hidden="true">{choice.icon}</span> {choice.label}
          </button>
        ))}
      </div>
      {rating && (
        <div className="feedback-reason">
          <label>
            Reason (optional)
            <textarea name="reason" rows={2} maxLength={1000} disabled={busy} />
          </label>
          <button type="submit" className="btn btn-secondary" disabled={busy}>
            {busy ? "Saving…" : "Send feedback"}
          </button>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
