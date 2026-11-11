import { StarterChips } from "../Chat/StarterChips";

export interface CoverStateProps {
  onSelectPrompt: (prompt: string) => void;
  onOpenFitModal?: () => void;
  disabled?: boolean;
}

export function CoverState({
  onSelectPrompt,
  onOpenFitModal,
  disabled = false,
}: CoverStateProps) {
  return (
    <section
      className="dossier-cover"
      aria-label="Candidate Overview and Inquiries"
    >
      <div className="dossier-masthead">
        <div className="dossier-eyebrow">
          <span className="dossier-tag">CANDIDATE DOSSIER</span>
          <span className="dossier-dispatch-id">REF: AMK-PORTFOLIO</span>
        </div>
        <h2 className="dossier-name">Aamir Mohammed Khan</h2>
        <p className="dossier-role">AI Systems & Full-Stack Engineer</p>

        <div className="dossier-credentials-ribbon" role="group" aria-label="Candidate Credentials">
          <span className="dossier-credential-pill">
            MSRUAS B.Tech (CGPA 9.77/10)
          </span>
          <span className="dossier-credential-pill">
            Bengaluru, India
          </span>
          <span className="dossier-credential-pill dossier-credential-available">
            <span className="credential-dot" aria-hidden="true" />
            Available for Hire
          </span>
        </div>

        <nav className="dossier-external-links" aria-label="Direct Candidate Links">
          <a href="/resume.pdf" target="_blank" rel="noopener noreferrer"
            className="dossier-external-link">Résumé (PDF)</a>
          <a
            href="https://github.com/aamir-coding"
            target="_blank"
            rel="noopener noreferrer"
            className="dossier-external-link"
            title="Aamir's GitHub profile"
          >
            GitHub ↗
          </a>
          <a
            href="https://www.linkedin.com/in/aamir-mk/"
            target="_blank"
            rel="noopener noreferrer"
            className="dossier-external-link"
            title="Aamir's LinkedIn profile"
          >
            LinkedIn ↗
          </a>
          <a
            href="mailto:aamirmkh25@gmail.com"
            className="dossier-external-link"
            title="Email Aamir directly"
          >
            aamirmkh25@gmail.com ↗
          </a>
        </nav>
      </div>

      <div className="dossier-statement">
        <p>
          I'm an AI assistant trained on Aamir's verified résumé, projects, and experience.
        </p>
      </div>

      <div className="dossier-meta-grid" role="group" aria-label="Core Competencies">
        <div className="dossier-meta-card">
          <span className="meta-label">CORE FOCUS</span>
          <span className="meta-value">
            High-throughput LLM pipelines, Hybrid RAG & Async Services
          </span>
        </div>
        <div className="dossier-meta-card">
          <span className="meta-label">PRIMARY STACK</span>
          <span className="meta-value">
            Python, FastAPI, Groq, React, TypeScript, Docker
          </span>
        </div>
        <div className="dossier-meta-card">
          <span className="meta-label">GROUNDING POLICY</span>
          <span className="meta-value">
            Curated résumé and project facts, with source receipts
          </span>
        </div>
      </div>

      {onOpenFitModal && (
        <div className="dossier-fit-cta-box" role="group" aria-label="Job Description Fit Analysis">
          <div className="dossier-fit-cta-text">
            <span className="dossier-fit-cta-title">JOB DESCRIPTION FIT ANALYSIS</span>
            <span className="dossier-fit-cta-desc">
              Paste any job description to evaluate verified requirement match, gaps, and ramp-up notes.
            </span>
          </div>
          <button
            type="button"
            className="btn-fit-action"
            onClick={onOpenFitModal}
            disabled={disabled}
            aria-label="Open Job Description Fit Report dialog"
          >
            ⚡ Analyze Role Fit →
          </button>
        </div>
      )}

      <div className="dossier-inquiries">
        <StarterChips
          onSelect={onSelectPrompt}
          onOpenFitModal={onOpenFitModal}
          disabled={disabled}
        />
      </div>
    </section>
  );
}
