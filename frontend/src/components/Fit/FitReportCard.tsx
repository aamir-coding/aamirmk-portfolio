import { useId } from "react";
import { UnderHood } from "../Chat/UnderHood";
import type { FitReport, JudgedRequirement, SampleJobDescription } from "../../lib/types";

interface FitReportCardProps {
  report: FitReport;
  activePreset?: SampleJobDescription | null;
  jobDescription?: string;
  onAskGap?: (requirementText: string) => void;
  onReset?: () => void;
  onRerunLive?: () => void;
}

const evidenceLinks = new Map([
  ["proj-entropy-oj-stack", { title: "Entropy Online Judge source", href: "https://github.com/aamir-coding/entropy-oj" }],
  ["proj-entropy-oj-pitch", { title: "Entropy Online Judge project", href: "https://github.com/aamir-coding/entropy-oj" }],
]);

const verdictLabels = { strong: "Strong", partial: "Partial", gap: "Gap" } as const;
const verdictOrder = { gap: 0, partial: 1, strong: 2 } as const;

function RequirementRow({ item, onAskGap }: {
  item: JudgedRequirement;
  onAskGap?: (requirementText: string) => void;
}) {
  const { requirement, verdict, evidence_chunk_ids, explanation, ramp_up, downgraded } = item;
  const requirementId = useId();

  return (
    <div className={`fit-req-row verdict-${verdict}`}>
      <p className="fit-req-text">
        <strong className={`fit-verdict-text verdict-${verdict}`}>{verdictLabels[verdict]}</strong>{" "}
        <span id={requirementId}>{requirement.text}</span>
      </p>
      <p className="fit-req-explanation">{explanation}</p>
      {downgraded && (
        <p className="fit-downgrade-notice" role="note">
          Downgraded to a gap because the proposed match had no valid supporting evidence.
        </p>
      )}
      {evidence_chunk_ids.length ? (
        <details className="fit-evidence">
          <summary aria-describedby={requirementId}>Evidence ({evidence_chunk_ids.length})</summary>
          <ul>
            {evidence_chunk_ids.map(id => {
              const link = evidenceLinks.get(id);
              return (
                <li key={id}>
                  {link && <a href={link.href} target="_blank" rel="noopener noreferrer">{link.title}</a>}
                  <code>[{id}]</code>
                </li>
              );
            })}
          </ul>
        </details>
      ) : <p className="fit-evidence-empty">No supporting evidence on record.</p>}
      {ramp_up && (
        <details className="fit-evidence">
          <summary aria-describedby={requirementId}>Ramp-up plan</summary>
          <p>{ramp_up}</p>
        </details>
      )}
      {verdict !== "strong" && onAskGap && (
        <button
          type="button"
          className="btn btn-ask-gap"
          aria-describedby={requirementId}
          onClick={() => onAskGap(requirement.text)}
        >
          Ask about this in chat
        </button>
      )}
    </div>
  );
}

export function FitReportCard({ report, activePreset, jobDescription, onAskGap, onReset, onRerunLive }: FitReportCardProps) {
  const { score } = report;
  const countsLabel = useId();
  const origin = report.telemetry?.origin ?? (activePreset?.report ? "curated" : undefined);
  const isCurated = origin === "curated";
  const isCached = origin === "cache" || (!origin && report.cached);
  const reviewedDescription = jobDescription || activePreset?.text;
  const mustHaves = report.requirements.filter(item => item.requirement.importance === "must_have")
    .sort((a, b) => verdictOrder[a.verdict] - verdictOrder[b.verdict]);
  const niceToHaves = report.requirements.filter(item => item.requirement.importance === "nice_to_have");

  return (
    <article className="fit-report-card" aria-label={`Job Fit Report: ${report.role_title}`}>
      <header className="fit-report-header">
        <p className="fit-report-origin">
          {isCurated ? "Curated example" : isCached ? "Cached report" : origin === "fresh" ? "Live assessment" : "Fit assessment"}
        </p>
        <h3 className="fit-role-title" tabIndex={-1}>{report.role_title}</h3>
        <p className="fit-headline"><strong>{score.overall_fit}</strong></p>
        {isCurated && <p className="fit-report-note">Authored development example for illustration. Live evaluation and ground-truth calibration are outside its scope.</p>}
        {isCached && <p className="fit-report-note">This request reused an earlier report and made no model calls.</p>}

        <p className="metric-name" id={countsLabel}>Must-have results</p>
        <dl className="fit-score-metrics" aria-labelledby={countsLabel}>
          <div className="score-metric-box">
            <dt className="metric-name">Strong</dt>
            <dd className="metric-number">{score.must_have_strong}/{score.must_have_total}</dd>
          </div>
          <div className="score-metric-box">
            <dt className="metric-name">Partial</dt>
            <dd className="metric-number">{score.must_have_partial}</dd>
          </div>
          <div className="score-metric-box">
            <dt className="metric-name">Gaps</dt>
            <dd className="metric-number">{score.must_have_gap}</dd>
          </div>
        </dl>
      </header>

      {mustHaves.length > 0 && (
        <section className="fit-req-group">
          <h4 className="fit-group-title">Must-have requirements</h4>
          {mustHaves.map(item => <RequirementRow key={item.requirement.id} item={item} onAskGap={onAskGap} />)}
        </section>
      )}
      {reviewedDescription && (
        <details className="fit-jd-preview-details">
          <summary className="fit-jd-preview-summary">View evaluated job description</summary>
          <div className="fit-jd-preview-body">
            <pre className="fit-jd-preview-text">{reviewedDescription}</pre>
          </div>
        </details>
      )}
      {niceToHaves.length > 0 && (
        <section className="fit-req-group">
          <h4 className="fit-group-title">Preferred requirements</h4>
          {niceToHaves.map(item => <RequirementRow key={item.requirement.id} item={item} onAskGap={onAskGap} />)}
        </section>
      )}

      <section className="fit-summary-callout" aria-label="Report summary">
        <h4 className="fit-group-title">Report summary</h4>
        <p>{score.headline}</p>
        <p className="summary-callout-text">{report.summary}</p>
      </section>

      <UnderHood telemetry={report.telemetry} browserTiming={report.browserTiming} delivery={!report.telemetry && isCurated ? "curated" : undefined} />
      <footer className="fit-report-footer">
        {onReset && <button type="button" className="btn btn-secondary" onClick={onReset}>Analyze custom job description</button>}
        {onRerunLive && reviewedDescription && (
          <div className="fit-rerun">
            <button type="button" className="btn btn-secondary" onClick={onRerunLive} aria-describedby="fit-live-note">
              {isCurated ? "Run live analysis" : "Run live again"}
            </button>
            <p id="fit-live-note">Live analysis sends this job description to Groq.</p>
          </div>
        )}
      </footer>
    </article>
  );
}
