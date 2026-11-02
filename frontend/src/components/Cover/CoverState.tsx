import { StarterChips } from "../Chat/StarterChips";

export interface CoverStateProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

export function CoverState({
  onSelectPrompt,
  disabled = false,
}: CoverStateProps) {
  return (
    <section
      className="dossier-cover"
      aria-label="Candidate Overview and Inquiries"
    >
      <div className="dossier-masthead">
        <div className="dossier-eyebrow">
          <span className="dossier-tag">VERIFIED DOSSIER</span>
          <span className="dossier-dispatch-id">REF: AMK-PORTFOLIO</span>
        </div>
        <h2 className="dossier-name">Aamir Mohammed Khan</h2>
        <p className="dossier-role">AI Systems & Full-Stack Engineer</p>

        <div className="dossier-credentials-ribbon" aria-label="Candidate Credentials">
          <span className="dossier-credential-pill">
            AMU B.Tech (CGPA 9.77/10)
          </span>
          <span className="dossier-credential-pill">
            Aligarh, India
          </span>
          <span className="dossier-credential-pill dossier-credential-available">
            <span className="credential-dot" aria-hidden="true" />
            Available for Hire
          </span>
        </div>

        <nav className="dossier-external-links" aria-label="Direct Candidate Links">
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
          I am an AI digital assistant trained exclusively on Aamir’s verified
          résumé, engineering projects, and system architectures. Inquiries are
          grounded strictly in verified facts.
        </p>
      </div>

      <div className="dossier-meta-grid" aria-label="Core Competencies">
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
            Authoritative facts from resume.tex, zero hallucinations
          </span>
        </div>
      </div>

      <div className="dossier-inquiries">
        <StarterChips onSelect={onSelectPrompt} disabled={disabled} />
      </div>
    </section>
  );
}
