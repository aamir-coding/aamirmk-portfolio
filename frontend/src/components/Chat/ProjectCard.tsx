import React from "react";
import type { ProjectCardData } from "../../lib/types";

export interface ProjectCardProps {
  card: ProjectCardData;
  onInspectArchitecture?: (card: ProjectCardData) => void;
}

export const ProjectCard = React.memo(function ProjectCard({
  card,
  onInspectArchitecture,
}: ProjectCardProps) {
  return (
    <section
      className="dossier-card"
      aria-label={`Project Dossier: ${card.title}`}
    >
      <header className="dossier-card-header">
        <div className="dossier-card-tags">
          <span className="dossier-badge dossier-badge-role">{card.role}</span>
          <span className="dossier-badge dossier-badge-verified">
            VERIFIED RECEIPT
          </span>
        </div>
        <h3 className="dossier-card-title">{card.title}</h3>
        <p className="dossier-card-subtitle">{card.subtitle}</p>
      </header>

      <div className="dossier-card-body">
        <p className="dossier-card-summary">{card.summary}</p>

        {card.highlights && card.highlights.length > 0 && (
          <ul className="dossier-card-highlights">
            {card.highlights.slice(0, 3).map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        )}

        <div className="dossier-card-tech">
          <span className="dossier-tech-label">STACK:</span>
          <div className="dossier-tech-chips">
            {card.tech_stack.map((tech) => (
              <span key={tech} className="dossier-tech-chip">
                {tech}
              </span>
            ))}
          </div>
        </div>

        {card.metrics && Object.keys(card.metrics).length > 0 && (
          <div className="dossier-card-metrics">
            {Object.entries(card.metrics).map(([key, val]) => (
              <div key={key} className="dossier-metric-cell">
                <span className="dossier-metric-key">{key}:</span>
                <span className="dossier-metric-val">{val}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <footer className="dossier-card-footer">
        {onInspectArchitecture && (
          <button
            type="button"
            className="btn btn-primary dossier-card-action"
            onClick={() => onInspectArchitecture(card)}
            aria-haspopup="dialog"
          >
            Inspect Architecture →
          </button>
        )}

        <div className="dossier-card-links">
          {card.live_url && (
            <a
              href={card.live_url}
              target="_blank"
              rel="noopener noreferrer"
              className="dossier-link"
              title={`Open live app for ${card.title}`}
            >
              Live Demo ↗
            </a>
          )}
          {card.github_url && (
            <a
              href={card.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="dossier-link"
              title={`View repository for ${card.title}`}
            >
              Repository ↗
            </a>
          )}
        </div>
      </footer>
    </section>
  );
});
