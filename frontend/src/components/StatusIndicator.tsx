export type ServerState = "checking" | "warming" | "ready" | "resting" | "error";

export interface StatusIndicatorProps {
  state: ServerState;
  errorMessage?: string | null;
}

export function StatusIndicator({
  state,
  errorMessage,
}: StatusIndicatorProps) {
  if (state === "resting") return (
    <div className="status-pill" aria-label="Server status: live answers resting">
      <span className="status-dot warming" aria-hidden="true" />
      <span>Live answers resting</span>
    </div>
  );
  if (state === "ready") {
    return (
      <div className="status-pill" aria-label="Server status: ready">
        <span className="status-dot ready" aria-hidden="true" />
        <span>Ready</span>
      </div>
    );
  }

  if (state === "warming" || state === "checking") {
    return (
      <div
        className="status-pill"
        aria-label="Server status: waking up on Render free tier"
      >
        <span className="status-dot warming" aria-hidden="true" />
        <span>
          {state === "warming" ? "Waking Up (Render ~25s)" : "Connecting..."}
        </span>
      </div>
    );
  }

  return (
    <div
      className="status-pill"
      aria-label={`Server status error: ${errorMessage || "Connection failed"}`}
    >
      <span className="status-dot error" aria-hidden="true" />
      <span>Offline</span>
    </div>
  );
}
