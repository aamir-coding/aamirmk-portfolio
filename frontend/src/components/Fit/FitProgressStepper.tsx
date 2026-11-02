import type { FitProgressData } from "../../lib/types";

export interface FitProgressStepperProps {
  progress: FitProgressData | null;
  onAbort?: () => void;
}

const STAGES = [
  { key: "reading_jd", label: "Read & Structure", minPercent: 10 },
  { key: "extracting_requirements", label: "Extract Criteria", minPercent: 25 },
  { key: "retrieving_evidence", label: "Retrieve Evidence", minPercent: 50 },
  { key: "evaluating_fit", label: "Judge Alignment", minPercent: 75 },
  { key: "synthesizing", label: "Executive Synthesis", minPercent: 90 },
];

export function FitProgressStepper({ progress, onAbort }: FitProgressStepperProps) {
  const currentPercent = progress?.percent ?? 0;
  const currentMessage = progress?.message ?? "Preparing verification pipeline...";

  return (
    <div className="fit-stepper-container" aria-live="polite" aria-busy="true">
      <div className="fit-stepper-header">
        <span className="fit-stepper-label">PIPELINE EXECUTION</span>
        <span className="fit-stepper-percent">{currentPercent}%</span>
      </div>

      <div className="fit-stepper-bar-bg" role="progressbar" aria-valuenow={currentPercent} aria-valuemin={0} aria-valuemax={100}>
        <div className="fit-stepper-bar-fill" style={{ width: `${currentPercent}%` }} />
      </div>

      <div className="fit-stepper-message">
        <span className="fit-stepper-spinner" aria-hidden="true" />
        <span>{currentMessage}</span>
      </div>

      <div className="fit-stepper-stages" aria-hidden="true">
        {STAGES.map((s, idx) => {
          const isDone = currentPercent > s.minPercent;
          const isActive = currentPercent >= s.minPercent && (idx === STAGES.length - 1 || currentPercent < STAGES[idx + 1]!.minPercent);

          return (
            <div
              key={s.key}
              className={`fit-stage-item ${isDone ? "stage-done" : ""} ${isActive ? "stage-active" : ""}`}
            >
              <span className="stage-dot" />
              <span className="stage-name">{s.label}</span>
            </div>
          );
        })}
      </div>

      {onAbort && (
        <div className="fit-stepper-abort">
          <button type="button" className="btn btn-secondary" onClick={onAbort}>
            Cancel Analysis
          </button>
        </div>
      )}
    </div>
  );
}
