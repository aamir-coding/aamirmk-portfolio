import { UnderHood } from "../Chat/UnderHood";
import { AssistantFallback } from "../AssistantFallback";
import { useLayoutEffect, useRef, useState } from "react";
import { useFitReport } from "../../hooks/useFitReport";
import type { SampleJobDescription } from "../../lib/types";
import { FitProgressStepper } from "./FitProgressStepper";
import { FitReportCard } from "./FitReportCard";
import { SummaryAction } from "../Summary/SummaryAction";
import { summaryProjectIds } from "../../lib/summary";

export interface FitReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAskGap?: (requirementText: string) => void;
}

export function FitReportModal({
  isOpen,
  onClose,
  onAskGap,
}: FitReportModalProps) {
  const [jdText, setJdText] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const modalRef = useRef<HTMLDialogElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);

  const {
    status,
    progress,
    report,
    error,
    errorReceipt,
    presets,
    activePreset,
    loadPreset,
    submit,
    abort,
    reset,
  } = useFitReport();

  useLayoutEffect(() => {
    const dialog = modalRef.current;
    if (!isOpen || !dialog) return;
    dialog.showModal();
    return () => { if (dialog.open) dialog.close(); };
  }, [isOpen]);

  useLayoutEffect(() => {
    if (!isOpen) return;
    const body = bodyRef.current;
    if (body) body.scrollTop = 0;
    const target = status === "completed" ? body?.querySelector<HTMLElement>(".fit-role-title") : titleRef.current;
    target?.focus({ preventScroll: true });
  }, [isOpen, status]);

  if (!isOpen) return null;

  const dismiss = () => {
    if (status === "streaming") abort();
    modalRef.current?.close();
    onClose();
  };

  const handleSelectPreset = (preset: SampleJobDescription) => {
    setJdText(preset.text);
    setRoleTitle(preset.title);
    loadPreset(preset);
  };

  const handleRerunLive = () => {
    if (activePreset) {
      void submit(activePreset.text, activePreset.title, true);
    } else if (jdText) {
      void submit(jdText, roleTitle, true);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void submit(jdText, roleTitle);
  };

  const handleModalReset = () => {
    reset();
    setJdText("");
    setRoleTitle("");
  };

  const handleAskGapBridge = (reqText: string) => {
    dismiss();
    onAskGap?.(reqText);
  };

  const trimmedLength = jdText.trim().length;
  const lengthHint = jdText.length > 6000
    ? "Shorten the job description to 6,000 characters or fewer."
    : trimmedLength > 0 && trimmedLength < 50
      ? `Add ${50 - trimmedLength} more characters to enable analysis.`
      : null;
  const isSubmitDisabled = trimmedLength < 50 || jdText.length > 6000;

  return (
    <dialog
      className="fit-modal-dialog"
      ref={modalRef}
      aria-labelledby="fit-modal-title"
      onCancel={(event) => {
        event.preventDefault();
        dismiss();
      }}
      onClick={(event) => {
        if (event.target !== event.currentTarget) return;
        const { left, right, top, bottom } = event.currentTarget.getBoundingClientRect();
        if (event.clientX < left || event.clientX > right || event.clientY < top || event.clientY > bottom) dismiss();
      }}
    >
        <div className="fit-modal-header">
          <div className="fit-modal-title-group">
            <h2 id="fit-modal-title" tabIndex={-1} ref={titleRef}>Job Description Fit Report</h2>
          </div>
          <button
            type="button"
            className="fit-modal-close"
            onClick={dismiss}
            aria-label="Close fit report dialog"
          >
            ✕
          </button>
        </div>

        <div className="fit-modal-body" ref={bodyRef}>
          {status === "completed" && report ? (
            <>
              <FitReportCard
                report={report}
                activePreset={activePreset}
                jobDescription={jdText}
                onAskGap={onAskGap ? handleAskGapBridge : undefined}
                onReset={handleModalReset}
                onRerunLive={handleRerunLive}
              />
              <SummaryAction projectIds={summaryProjectIds(
                report.requirements.flatMap(requirement => requirement.evidence_chunk_ids),
              )} />
            </>
          ) : status === "streaming" ? (
            <FitProgressStepper progress={progress} onAbort={abort} />
          ) : (
            <form onSubmit={handleSubmit} className="fit-form">
              {presets.length > 0 && (
                <div className="fit-presets-container" role="group" aria-label="Sample Job Description Presets">
                  <div className="fit-presets-header">
                    <span className="fit-presets-label">Curated examples</span>
                    <span className="fit-presets-subtext">Authored examples for illustration</span>
                  </div>
                  <div className="fit-presets-list">
                    {presets.map(preset => (
                        <button
                          key={preset.id}
                          type="button"
                          className="fit-preset-chip"
                          onClick={() => handleSelectPreset(preset)}
                          title={`Explore ${preset.title}: ${preset.match_expectation}`}
                        >
                          <span className="preset-chip-title">{preset.title.split("(")[0]?.trim()}</span>
                          <span className="preset-chip-badge">{preset.match_expectation}</span>
                        </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="fit-form-field">
                <label htmlFor="fit-role-title" className="fit-field-label">
                  Target role title <span className="field-optional">(optional)</span>
                </label>
                <input
                  id="fit-role-title"
                  type="text"
                  className="fit-input"
                  placeholder="e.g. Senior Full-Stack AI Engineer"
                  value={roleTitle}
                  onChange={(e) => setRoleTitle(e.target.value)}
                  maxLength={150}
                />
              </div>

              <div className="fit-form-field">
                <div className="fit-field-header">
                  <label htmlFor="fit-jd-text" className="fit-field-label">
                    Paste job description <span className="field-required">*</span>
                  </label>
                  <span className="fit-char-count" id="fit-char-count">
                    {jdText.length} / 6,000 characters (minimum 50)
                  </span>
                </div>
                <textarea
                  id="fit-jd-text"
                  className="fit-textarea"
                  rows={5}
                  placeholder="Paste complete job requirements, stack expectations, and qualifications here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  maxLength={6500}
                  aria-invalid={lengthHint ? true : undefined}
                  aria-describedby={`fit-char-count fit-data-note${lengthHint ? " fit-length-hint" : ""}`}
                  required
                />
                {lengthHint && <p id="fit-length-hint" className="fit-field-hint">{lengthHint}</p>}
              </div>

              {error && (
                <div className="banner-notice warning" role="alert">
                  <div><p>{error}</p><AssistantFallback /></div>
                </div>
              )}

              {errorReceipt ? <UnderHood {...errorReceipt} /> : null}
              <div className="fit-form-notice">
                <p id="fit-data-note">
                  Your pasted job description is analyzed against curated portfolio facts.
                  Uncited requirement verdicts are downgraded; citation membership alone does not
                  prove semantic support. Live text is processed by Groq. Reports are reused
                  for up to 15 minutes and held in bounded server memory until eviction or
                  restart.
                </p>
              </div>

              <div className="fit-modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    handleModalReset();
                    dismiss();
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitDisabled}
                >
                  Analyze Alignment
                </button>
              </div>
            </form>
          )}
        </div>
    </dialog>
  );
}
