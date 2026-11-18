import type { FitProgressData } from "../../lib/types";

interface FitProgressStepperProps {
  progress: FitProgressData | null;
  onAbort?: () => void;
}

export function FitProgressStepper({ progress, onAbort }: FitProgressStepperProps) {
  const percent = progress?.percent ?? 0;
  return (
    <section className="fit-stepper-container" aria-label="Role fit analysis">
      <p role="status">{progress?.message ?? "Preparing fit analysis…"}</p>
      <progress aria-label="Role fit analysis progress" value={percent} max={100} />
      <p>{percent}% complete</p>
      {onAbort && (
        <div>
          <button type="button" className="btn btn-secondary" onClick={onAbort}>Cancel analysis</button>
        </div>
      )}
    </section>
  );
}
