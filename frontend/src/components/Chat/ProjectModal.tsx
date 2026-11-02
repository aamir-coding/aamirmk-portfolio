import React, { useEffect, useRef } from "react";
import type { ProjectCardData } from "../../lib/types";

export interface ProjectModalProps {
  card: ProjectCardData | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ProjectModal = React.memo(function ProjectModal({
  card,
  isOpen,
  onClose,
}: ProjectModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const triggerElementRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Save previous active element to restore focus on close
    triggerElementRef.current = document.activeElement as HTMLElement | null;

    // Lock background scrolling
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    // Focus the modal or first focusable element
    const focusable = modalRef.current?.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable && focusable.length > 0) {
      focusable[0]?.focus();
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === "Tab" && focusable && focusable.length > 0) {
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last?.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first?.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      triggerElementRef.current?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen || !card) {
    return null;
  }

  return (
    <div className="modal-portal" role="presentation">
      <div
        className="modal-backdrop"
        onClick={onClose}
        aria-hidden="true"
        data-testid="modal-backdrop"
      />
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-project-title"
        className="project-modal"
      >
        <header className="modal-header">
          <div className="modal-header-meta">
            <span className="dossier-badge dossier-badge-role">{card.role}</span>
            <span className="dossier-badge dossier-badge-verified">
              BLUEPRINT
            </span>
          </div>
          <div className="modal-title-row">
            <h2 id="modal-project-title" className="modal-title">
              {card.title}
            </h2>
            <button
              type="button"
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close architecture modal (Esc)"
            >
              ✕ <span className="modal-key-hint">ESC</span>
            </button>
          </div>
          <p className="modal-subtitle">{card.subtitle}</p>
        </header>

        <div className="modal-body">
          <section className="modal-section">
            <h4 className="modal-section-heading">SYSTEM SUMMARY</h4>
            <p className="modal-text">{card.summary}</p>
          </section>

          <section className="modal-section">
            <h4 className="modal-section-heading">ARCHITECTURE & DESIGN DECISIONS</h4>
            <div className="modal-architecture-content">
              <pre className="modal-architecture-pre">
                <code>{card.architecture_details}</code>
              </pre>
            </div>
          </section>

          <section className="modal-section">
            <h4 className="modal-section-heading">TECHNICAL STACK</h4>
            <div className="dossier-tech-chips">
              {card.tech_stack.map((tech) => (
                <span key={tech} className="dossier-tech-chip">
                  {tech}
                </span>
              ))}
            </div>
          </section>

          {card.highlights && card.highlights.length > 0 && (
            <section className="modal-section">
              <h4 className="modal-section-heading">ENGINEERING HIGHLIGHTS</h4>
              <ul className="modal-list">
                {card.highlights.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </section>
          )}

          {card.metrics && Object.keys(card.metrics).length > 0 && (
            <section className="modal-section">
              <h4 className="modal-section-heading">VERIFIED METRICS</h4>
              <div className="dossier-card-metrics">
                {Object.entries(card.metrics).map(([k, v]) => (
                  <div key={k} className="dossier-metric-cell">
                    <span className="dossier-metric-key">{k}:</span>
                    <span className="dossier-metric-val">{v}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {card.source_sections && card.source_sections.length > 0 && (
            <section className="modal-section">
              <h4 className="modal-section-heading">GROUNDED QUESTIONNAIRE SECTIONS</h4>
              <p className="modal-receipt-code">
                {card.source_sections.map((s) => `[${s}]`).join(" ")}
              </p>
            </section>
          )}
        </div>

        <footer className="modal-footer">
          <div className="modal-footer-links">
            {card.live_url && (
              <a
                href={card.live_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                Launch Live App ↗
              </a>
            )}
            {card.github_url && (
              <a
                href={card.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                Source Repository ↗
              </a>
            )}
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
          >
            Dismiss Dossier
          </button>
        </footer>
      </div>
    </div>
  );
});
