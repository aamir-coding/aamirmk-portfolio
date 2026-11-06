import { UnderHood } from "../Chat/UnderHood";
import { AssistantFallback } from "../AssistantFallback";
import { useEffect, useRef, useState } from "react";
import { useFitReport } from "../../hooks/useFitReport";
import type { SampleJobDescription } from "../../lib/types";
import { FitProgressStepper } from "./FitProgressStepper";
import { FitReportCard } from "./FitReportCard";

export interface FitReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAskGap: (requirementText: string) => void;
}

export function FitReportModal({
  isOpen,
  onClose,
  onAskGap,
}: FitReportModalProps) {
  const [jdText, setJdText] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const modalRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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

  // Escape key listener & focus management
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (status === "streaming") {
          abort();
        }
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    const timer = setTimeout(() => {
      textareaRef.current?.focus();
    }, 50);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      clearTimeout(timer);
    };
  }, [isOpen, status, abort, onClose]);

  if (!isOpen) return null;

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
    onClose();
    onAskGap(reqText);
  };

  const isTextTooShort = jdText.trim().length > 0 && jdText.trim().length < 50;
  const isSubmitDisabled = jdText.trim().length < 50 || jdText.length > 6000 || status === "streaming";

  return (
    <div
      className="fit-modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          if (status === "streaming") abort();
          onClose();
        }
      }}
      role="presentation"
    >
      <div
        className="fit-modal-dialog"
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="fit-modal-title"
      >
        <div className="fit-modal-header">
          <div className="fit-modal-title-group">
            <span className="fit-tag">Curated evidence review</span>
            <h2 id="fit-modal-title">Job Description Fit Report</h2>
          </div>
          <button
            type="button"
            className="fit-modal-close"
            onClick={() => {
              if (status === "streaming") abort();
              onClose();
            }}
            aria-label="Close fit report dialog"
          >
            ✕
          </button>
        </div>

        <div className="fit-modal-body">
          {status === "completed" && report ? (
            <FitReportCard
              report={report}
              activePreset={activePreset}
              onAskGap={handleAskGapBridge}
              onReset={handleModalReset}
              onRerunLive={handleRerunLive}
            />
          ) : status === "streaming" ? (
            <FitProgressStepper progress={progress} onAbort={abort} />
          ) : (
            <form onSubmit={handleSubmit} className="fit-form">
              {presets.length > 0 && (
                <div className="fit-presets-container" role="group" aria-label="Sample Job Description Presets">
                  <div className="fit-presets-header">
                    <span className="fit-presets-label">Curated examples (instant):</span>
                    <span className="fit-presets-subtext">Authored development examples; not calibrated ground truth</span>
                  </div>
                  <div className="fit-presets-list">
                    {presets.map((preset) => {
                      const expectation = preset.match_expectation.toLowerCase();
                      const isLowMatch = expectation.includes("low");
                      return (
                        <button
                          key={preset.id}
                          type="button"
                          className={`fit-preset-chip ${isLowMatch ? "preset-chip-low" : ""}`}
                          onClick={() => handleSelectPreset(preset)}
                          title={`Explore ${preset.title}: ${preset.match_expectation}`}
                        >
                          <span className="preset-chip-title">{preset.title.split("(")[0]?.trim()}</span>
                          <span className="preset-chip-badge">{preset.match_expectation}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="fit-divider-or" aria-hidden="true">
                <span>OR ANALYZE CUSTOM JOB DESCRIPTION</span>
              </div>

              <div className="fit-form-field">
                <label htmlFor="fit-role-title" className="fit-field-label">
                  Target Role Title <span className="field-optional">(optional)</span>
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
                    Paste Job Description <span className="field-required">*</span>
                  </label>
                  <span className={`fit-char-count ${jdText.length > 6000 ? "count-overflow" : ""}`}>
                    {jdText.length} / 6,000 characters
                  </span>
                </div>
                <textarea
                  id="fit-jd-text"
                  ref={textareaRef}
                  className="fit-textarea"
                  rows={8}
                  placeholder="Paste complete job requirements, stack expectations, and qualifications here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  maxLength={6500}
                  required
                />
                {isTextTooShort && (
                  <span className="fit-field-hint warning">
                    Minimum 50 characters required ({50 - jdText.trim().length} more needed).
                  </span>
                )}
              </div>

              {error && (
                <div className="banner-notice warning" role="alert">
                  <div><p>{error}</p><AssistantFallback /></div>
                </div>
              )}

              {errorReceipt ? <UnderHood {...errorReceipt} /> : null}
              <div className="fit-form-notice">
                <p>
                  Your pasted job description is analyzed against curated portfolio facts.
                  Uncited requirement verdicts are downgraded; citation membership alone does not
                  prove semantic support. Live text is processed by Groq. Reports are reused
                  for up to 15 minutes and held in bounded server memory until eviction or
                  restart. No message history is saved to a database.
                </p>
              </div>

              <div className="fit-modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    handleModalReset();
                    onClose();
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitDisabled}
                >
                  ⚡ Analyze Alignment
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
