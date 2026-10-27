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
