import type { FitReport, JudgedRequirement, SampleJobDescription } from "../../lib/types";

export interface FitReportCardProps {
  report: FitReport;
  activePreset?: SampleJobDescription | null;
  onAskGap?: (requirementText: string) => void;
  onReset?: () => void;
  onRerunLive?: () => void;
}

export function FitReportCard({
  report,
  activePreset,
  onAskGap,
  onReset,
  onRerunLive,
}: FitReportCardProps) {
  const { score } = report;
  const isBenchmark = Boolean(activePreset?.report || report.cached);

  const mustHaves = report.requirements.filter(
    (r) => r.requirement.importance === "must_have"
  );
  const niceToHaves = report.requirements.filter(
    (r) => r.requirement.importance === "nice_to_have"
  );

  const getVerdictClass = (verdict: string) => {
    switch (verdict) {
      case "strong":
        return "verdict-strong";
      case "partial":
        return "verdict-partial";
      case "gap":
      default:
        return "verdict-gap";
    }
  };

  const getVerdictIcon = (verdict: string) => {
    switch (verdict) {
      case "strong":
        return "✓";
      case "partial":
        return "◑";
      case "gap":
      default:
        return "✕";
    }
  };

  const renderRequirementRow = (item: JudgedRequirement) => {
    const { requirement, verdict, evidence_chunk_ids, explanation, ramp_up, downgraded } = item;
    const isGapOrPartial = verdict === "gap" || verdict === "partial";

    return (
      <div key={requirement.id} className={`fit-req-row ${getVerdictClass(verdict)}`}>
        <div className="fit-req-header">
          <div className="fit-req-badges">
            <span className={`fit-verdict-pill ${getVerdictClass(verdict)}`}>
              <span className="verdict-icon" aria-hidden="true">{getVerdictIcon(verdict)}</span>
              <span className="verdict-text">{verdict.toUpperCase()}</span>
            </span>
            <span className="fit-type-pill">{requirement.type.toUpperCase()}</span>
            {requirement.importance === "must_have" && (
              <span className="fit-importance-pill">MUST-HAVE</span>
            )}
          </div>
        </div>

        <p className="fit-req-text">{requirement.text}</p>

        <p className="fit-req-explanation">{explanation}</p>

        {downgraded && (
          <div className="fit-downgrade-notice" role="note">
            <span aria-hidden="true">⚠️</span>
            <span>Overclaiming Guard: Model claimed unevidenced match; downgraded to gap.</span>
          </div>
        )}

        {evidence_chunk_ids.length > 0 && (
          <div className="fit-citations-row">
            <span className="fit-citations-label">Verified Citations:</span>
            {evidence_chunk_ids.map((cid) => (
              <span key={cid} className="fit-citation-tag">
                [{cid}]
              </span>
            ))}
          </div>
        )}

        {ramp_up && (
          <div className="fit-ramp-up-box">
            <span className="ramp-up-label">RAMP-UP NARRATIVE:</span>
            <p className="ramp-up-text">{ramp_up}</p>
          </div>
        )}

        {isGapOrPartial && onAskGap && (
          <div className="fit-ask-gap-action">
            <button
              type="button"
              className="btn btn-ask-gap"
              onClick={() => onAskGap(requirement.text)}
              title={`Ask the assistant about: ${requirement.text}`}
            >
              💬 Ask about this in chat →
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <article className="fit-report-card" aria-label={`Job Fit Report: ${report.role_title}`}>
      {isBenchmark && (
        <div className="fit-benchmark-banner" role="status">
          <div className="fit-benchmark-meta">
            <span className="fit-benchmark-icon" aria-hidden="true">⚡</span>
            <div className="fit-benchmark-details">
              <strong>VERIFIED GOLDEN BENCHMARK (CACHED SNAPSHOT)</strong>
              <span>
                Pre-evaluated against Aamir's verified dossier to preserve free-tier compute.
              </span>
            </div>
          </div>
          {onRerunLive && activePreset && (
            <button
              type="button"
              className="btn-fit-rerun"
              onClick={onRerunLive}
              title="Re-run live against Groq LLM and hybrid RAG"
            >
              🔄 Re-Run Live Pipeline
            </button>
          )}
        </div>
      )}

      {activePreset?.text && (
        <details className="fit-jd-preview-details">
          <summary className="fit-jd-preview-summary">
            📄 View Evaluated Job Description ({activePreset.title})
          </summary>
          <div className="fit-jd-preview-body">
            <pre className="fit-jd-preview-text">{activePreset.text}</pre>
          </div>
        </details>
      )}

      <header className="fit-report-header">
        <div className="fit-header-meta">
          <span className="fit-tag">EVALUATION DOSSIER</span>
          <span className={`fit-overall-badge ${score.overall_fit.toLowerCase().replace(/\s+/g, "-")}`}>
            {score.overall_fit}
          </span>
        </div>
        <h3 className="fit-role-title">{report.role_title}</h3>
        <p className="fit-headline">{score.headline}</p>

        <div className="fit-score-metrics">
          <div className="score-metric-box">
            <span className="metric-number">{score.must_have_strong}/{score.must_have_total}</span>
            <span className="metric-name">Must-Haves Evidenced</span>
          </div>
          <div className="score-metric-box">
            <span className="metric-number">{score.must_have_partial}</span>
            <span className="metric-name">Partial Alignments</span>
          </div>
          <div className="score-metric-box">
            <span className="metric-number">{score.must_have_gap}</span>
            <span className="metric-name">Identified Gaps</span>
          </div>
        </div>
      </header>

      <section className="fit-summary-callout" aria-label="Executive Summary">
        <span className="summary-callout-label">EXECUTIVE SYNTHESIS</span>
        <p className="summary-callout-text">{report.summary}</p>
      </section>

      <section className="fit-requirements-breakdown">
        {mustHaves.length > 0 && (
          <div className="fit-req-group">
            <h4 className="fit-group-title">Core Requirements ({mustHaves.length})</h4>
            <div className="fit-req-list">
              {mustHaves.map(renderRequirementRow)}
            </div>
          </div>
        )}

        {niceToHaves.length > 0 && (
          <div className="fit-req-group">
            <h4 className="fit-group-title">Preferred & Nice-To-Have Skills ({niceToHaves.length})</h4>
            <div className="fit-req-list">
              {niceToHaves.map(renderRequirementRow)}
            </div>
          </div>
        )}
      </section>

      <footer className="fit-report-footer">
        {onReset && (
          <button type="button" className="btn btn-secondary" onClick={onReset}>
            ← Analyze Custom Job Description
          </button>
        )}
      </footer>
    </article>
  );
}
